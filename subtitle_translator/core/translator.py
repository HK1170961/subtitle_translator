"""llama-server API翻译引擎"""

import re
import time
import requests


LANGUAGE_MAP = {
    "简体中文": "zh",
    "繁體中文": "zh-tw",
    "English": "en",
    "日本語": "ja",
    "한국어": "ko",
    "Français": "fr",
    "Deutsch": "de",
    "Español": "es",
    "Русский": "ru",
    "Português": "pt",
    "Italiano": "it",
    "العربية": "ar",
}

# 编号行：开头为数字 + 分隔符，如 "1. xxx" / "2、 xxx" / "3) xxx"
_NUMBERED_LINE = re.compile(r"^\s*(\d+)\s*[\.\)、]\s*(.*)$")

# 兜底的最小 max_tokens 下限
_MIN_MAX_TOKENS = 2048


def _estimate_max_tokens(texts: list[str], requested: int) -> int:
    """根据批次文本长度估算输出 max_tokens，避免响应被截断。

    粗略估算：译文长度通常与原文相近，按字符数 * 系数（含编号/换行开销）
    再加安全余量；取估算值与请求值的较大者。
    """
    total_chars = sum(len(t) for t in texts)
    # 每字符约 0.5~1 token，乘 3 留足编号、换行与译文扩展余量，再加 200 固定开销
    estimated = int(total_chars * 3) + 200
    return max(_MIN_MAX_TOKENS, requested, estimated)


def build_batch_prompt_with_context(texts: list[str], source_lang: str,
                                     target_lang: str,
                                     context_before: str = "",
                                     context_after: str = "") -> str:
    """构建带上下文的批量翻译提示词"""
    lines = []

    lines.append(f"Translate subtitle lines from {source_lang} to {target_lang}.")
    lines.append("Keep translations concise and natural for subtitles.")
    lines.append("Output format: one translation per line, numbered exactly as input.")
    lines.append("Output ONLY the numbered translations, no explanations.")
    lines.append("")

    if context_before:
        lines.append("--- Previous context (for reference only, do NOT translate) ---")
        for t in context_before.split("\n"):
            if t.strip():
                lines.append(t)
        lines.append("--- End of previous context ---")
        lines.append("")

    lines.append("--- Lines to translate ---")
    for i, t in enumerate(texts):
        lines.append(f"{i+1}. {t}")
    lines.append("--- End ---")

    if context_after:
        lines.append("")
        lines.append("--- Next context (for reference only, do NOT translate) ---")
        for t in context_after.split("\n"):
            if t.strip():
                lines.append(t)
        lines.append("--- End of next context ---")

    return "\n".join(lines)


class LlamaTranslator:
    """llama-server翻译客户端"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8080,
                 timeout: int = 120):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()
        # 翻译缓存: (source_lang, target_lang, text) -> translation
        self._cache: dict[tuple[str, str, str], str] = {}

    def close(self):
        """关闭底层 HTTP 会话，释放连接资源"""
        try:
            self.session.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def check_connection(self) -> tuple[bool, str]:
        """检查llama-server连接状态"""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=(3, 5))
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                return status == "ok", status
            return False, f"HTTP {resp.status_code}"
        except requests.ConnectionError:
            return False, "无法连接到服务器"
        except Exception as e:
            return False, str(e)

    def translate_batch(self, texts: list[str], source_lang: str = "English",
                        target_lang: str = "简体中文",
                        temperature: float = 0.3,
                        top_p: float = 0.9,
                        max_tokens: int = 2048,
                        context_before: str = "",
                        context_after: str = "",
                        max_retries: int = 3) -> tuple[bool, list[str]]:
        """批量翻译多条文本，支持上下文，带指数退避重试。

        返回 (success, results)：
        - success=True 表示所有行均翻译成功；
        - 若解析后有效行数不足（疑似被截断/格式异常），返回 (False, results)，
          results 中缺失行以空串占位，便于调用方区分失败并标记。
        """
        if not texts:
            return True, []

        # ---- 批内去重 + 缓存命中 ----
        # unique_texts 保留首次出现顺序；need_translate 标记每条是否需请求 LLM
        results: list[str] = [""] * len(texts)
        unique_texts: list[str] = []
        unique_positions: list[list[int]] = []  # 每个 unique 文本对应的原位置列表
        cache_key_map: dict[str, int] = {}  # text -> unique 索引
        cache_key_prefix = (source_lang, target_lang)

        for pos, t in enumerate(texts):
            cached = self._cache.get((*cache_key_prefix, t))
            if cached is not None:
                results[pos] = cached
                continue
            ui = cache_key_map.get(t)
            if ui is not None:
                unique_positions[ui].append(pos)
            else:
                cache_key_map[t] = len(unique_texts)
                unique_texts.append(t)
                unique_positions.append([pos])

        # 全部命中缓存则直接返回
        if not unique_texts:
            return True, results

        # ---- 动态 max_tokens ----
        effective_max_tokens = _estimate_max_tokens(unique_texts, max_tokens)

        prompt = build_batch_prompt_with_context(
            unique_texts, source_lang, target_lang, context_before, context_after
        )

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": effective_max_tokens,
            "stream": False,
        }

        last_error = ""
        for attempt in range(max_retries):
            try:
                resp = self.session.post(
                    self.api_url,
                    json=payload,
                    timeout=self.timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    parsed, complete = self._parse_numbered_response(
                        content, len(unique_texts)
                    )
                    # 回填结果
                    for ui, tr in enumerate(parsed):
                        for pos in unique_positions[ui]:
                            results[pos] = tr
                        # 写入缓存（空串不缓存，避免缓存失败结果）
                        if tr:
                            self._cache[(*cache_key_prefix, unique_texts[ui])] = tr
                    if complete:
                        return True, results
                    # 解析不完整：可能被截断，重试一次（除非已是最后一次）
                    last_error = "Response parsed incompletely"
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return False, self._fill_unfilled(results, unique_positions,
                                                       len(texts), last_error)
                elif resp.status_code >= 500:
                    last_error = f"API error: HTTP {resp.status_code}"
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    return False, self._fill_unfilled(results, unique_positions,
                                                       len(texts), last_error)
                else:
                    last_error = f"API error: HTTP {resp.status_code}"
                    return False, self._fill_unfilled(results, unique_positions,
                                                       len(texts), last_error)
            except requests.ConnectionError:
                last_error = "Translation connection failed"
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return False, self._fill_unfilled(results, unique_positions,
                                                   len(texts), last_error)
            except requests.Timeout:
                last_error = "Translation timeout"
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return False, self._fill_unfilled(results, unique_positions,
                                                   len(texts), last_error)
            except Exception as e:
                last_error = f"Translation failed: {str(e)}"
                return False, self._fill_unfilled(results, unique_positions,
                                                   len(texts), last_error)

        return False, self._fill_unfilled(results, unique_positions,
                                           len(texts), last_error)

    @staticmethod
    def _fill_unfilled(results: list[str],
                        unique_positions: list[list[int]],
                        total: int, error: str) -> list[str]:
        """失败时构造返回列表：保留已缓存/已回填的位置，未填充位置写入错误标记。

        避免用 [error]*total 覆盖掉缓存命中的结果。
        """
        out = list(results)
        filled = set()
        for positions in unique_positions:
            for p in positions:
                filled.add(p)
        for i in range(total):
            if i not in filled and not out[i]:
                out[i] = error
        return out

    @staticmethod
    def _parse_numbered_response(response: str,
                                  expected_count: int) -> tuple[list[str], bool]:
        """严格解析编号格式的翻译响应。

        按行首编号提取，按编号大小排序去重，再按顺序对齐到 expected_count。
        返回 (results, complete)：
        - results: 长度等于 expected_count 的列表
        - complete: 解析到的编号集合是否完整覆盖 1..expected_count
        """
        numbered: dict[int, str] = {}
        for raw_line in response.split("\n"):
            line = raw_line.rstrip("\r")
            if not line.strip():
                continue
            m = _NUMBERED_LINE.match(line)
            if not m:
                # 非编号行：若是无前缀的纯文本也跳过，避免污染（如解释性段落）
                continue
            num = int(m.group(1))
            content = m.group(2).strip()
            if num not in numbered:
                numbered[num] = content

        results: list[str] = []
        complete = True
        for i in range(1, expected_count + 1):
            results.append(numbered.get(i, ""))

        # 判定完整性：缺失任一编号即不完整
        for i in range(1, expected_count + 1):
            if i not in numbered:
                complete = False
                break

        return results, complete
