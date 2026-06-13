"""llama-server API翻译引擎"""

import re
import requests
from typing import Optional


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


def build_batch_prompt_with_context(texts: list[str], source_lang: str,
                                     target_lang: str,
                                     context_before: str = "",
                                     context_after: str = "") -> str:
    """构建带上下文的批量翻译提示词"""
    lines = []

    lines.append(f"Translate subtitle lines from {source_lang} to {target_lang}.")
    lines.append("Keep translations concise and natural for subtitles.")
    lines.append("Output format: one translation per line, numbered exactly as input.")
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

    @property
    def api_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    def check_connection(self) -> tuple[bool, str]:
        """检查llama-server连接状态"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("status", "unknown")
                return status == "ok", status
            return False, f"HTTP {resp.status_code}"
        except requests.ConnectionError:
            return False, "无法连接到服务器"
        except Exception as e:
            return False, str(e)

    def get_models(self) -> list[str]:
        """获取可用模型列表"""
        try:
            resp = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [m["id"] for m in data.get("data", [])]
        except Exception:
            pass
        return []

    def translate_batch(self, texts: list[str], source_lang: str = "English",
                        target_lang: str = "简体中文",
                        temperature: float = 0.3,
                        top_p: float = 0.9,
                        max_tokens: int = 2048,
                        context_before: str = "",
                        context_after: str = "") -> tuple[bool, list[str]]:
        """批量翻译多条文本，支持上下文"""
        if not texts:
            return True, []

        prompt = build_batch_prompt_with_context(
            texts, source_lang, target_lang, context_before, context_after
        )

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            resp = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                results = self._parse_numbered_response(content, len(texts))
                return True, results
            else:
                return False, [f"API error: HTTP {resp.status_code}"] * len(texts)
        except requests.Timeout:
            return False, ["Translation timeout"] * len(texts)
        except Exception as e:
            return False, [f"Translation failed: {str(e)}"] * len(texts)

    @staticmethod
    def _parse_numbered_response(response: str, expected_count: int) -> list[str]:
        """解析编号格式的翻译响应"""
        lines = response.strip().split("\n")
        results = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r"^\d+[\.\)、]\s*", "", line)
            if cleaned:
                results.append(cleaned)

        while len(results) < expected_count:
            results.append("")
        return results[:expected_count]
