"""ASS/SSA字幕格式解析器"""

import re
import chardet


DETECT_SAMPLE_SIZE = 65536

TAG_PATTERN = re.compile(r"\{[^}]*\}")


def _decode_subtitle_bytes(raw: bytes) -> str:
    """稳健地解码字幕字节流。

    顺序：UTF-8（严格）→ chardet 检测 → GBK → UTF-8(replace)。
    相比单一 chardet 检测，可避免中文被误判为 latin-1/Windows-1252 后变乱码。
    """
    # 1. 优先 UTF-8（最常见的字幕编码，且能严格校验）
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    # 2. chardet 检测
    try:
        det = chardet.detect(raw[:DETECT_SAMPLE_SIZE]) or {}
        enc = det.get("encoding") or ""
        if enc:
            try:
                return raw.decode(enc, errors="strict")
            except (UnicodeDecodeError, LookupError):
                pass
    except Exception:
        pass
    # 3. 回退 GBK（中文 Windows 常见）
    try:
        return raw.decode("gbk")
    except (UnicodeDecodeError, LookupError):
        pass
    # 4. 最后兜底：UTF-8 + replace，保证不抛异常
    return raw.decode("utf-8", errors="replace")


class ASSEntry:
    """ASS字幕条目"""

    __slots__ = ("layer", "start_time", "end_time", "style", "name",
                 "margin_l", "margin_r", "margin_v", "effect", "text",
                 "raw_line", "translated_text", "header_line_index")

    def __init__(self, layer: int, start_time: str, end_time: str,
                 style: str, name: str, margin_l: int, margin_r: int,
                 margin_v: int, effect: str, text: str, raw_line: str,
                 header_line_index: int = -1):
        self.layer = layer
        self.start_time = start_time
        self.end_time = end_time
        self.style = style
        self.name = name
        self.margin_l = margin_l
        self.margin_r = margin_r
        self.margin_v = margin_v
        self.effect = effect
        self.text = text
        self.raw_line = raw_line
        self.translated_text = ""
        # 该 Dialogue 行在 headers["[Events]"] 列表中的下标，用于 save 时精准回填
        self.header_line_index = header_line_index


class ASSParser:
    """ASS/SSA字幕解析器"""

    DIALOGUE_PATTERN = re.compile(
        r"^Dialogue:\s*(\d+),"
        r"(\d+:\d{2}:\d{2}\.\d{2}),"
        r"(\d+:\d{2}:\d{2}\.\d{2}),"
        r"([^,]*),"
        r"([^,]*),"
        r"(\d+),(\d+),(\d+),"
        r"([^,]*),"
        r"(.+)$"
    )

    @classmethod
    def parse(cls, file_path: str) -> tuple[dict, list[ASSEntry]]:
        """解析ASS文件，返回(头部信息, 对话条目列表)"""
        with open(file_path, "rb") as f:
            raw = f.read()
        content = _decode_subtitle_bytes(raw)
        return cls.parse_content(content)

    @classmethod
    def parse_content(cls, content: str) -> tuple[dict, list[ASSEntry]]:
        """解析ASS内容字符串"""
        headers = {}
        entries = []
        current_section = ""

        # 统一行尾（兼容 CRLF / CR）
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        for line in content.split("\n"):
            line_stripped = line.strip()

            if line_stripped.startswith("[") and line_stripped.endswith("]"):
                current_section = line_stripped
                headers[current_section] = []
            elif current_section and line_stripped:
                if current_section not in headers:
                    headers[current_section] = []
                # 记录该行即将被 append 的下标
                line_index = len(headers[current_section])
                headers[current_section].append(line_stripped)

                if current_section == "[Events]":
                    match = cls.DIALOGUE_PATTERN.match(line_stripped)
                    if match:
                        entry = ASSEntry(
                            layer=int(match.group(1)),
                            start_time=match.group(2),
                            end_time=match.group(3),
                            style=match.group(4),
                            name=match.group(5),
                            margin_l=int(match.group(6)),
                            margin_r=int(match.group(7)),
                            margin_v=int(match.group(8)),
                            effect=match.group(9),
                            text=match.group(10),
                            raw_line=line_stripped,
                            header_line_index=line_index,
                        )
                        entries.append(entry)

        return headers, entries

    @staticmethod
    def _extract_text_without_tags(text: str) -> str:
        """提取去除ASS样式标签后的纯文本"""
        clean = TAG_PATTERN.sub("", text)
        clean = clean.replace("\\N", "\n").replace("\\n", "\n")
        return clean.strip()

    @classmethod
    def get_translatable_texts(cls, entries: list[ASSEntry]) -> list[tuple[int, str]]:
        """获取可翻译的文本列表，返回 (索引, 纯文本)"""
        result = []
        for i, entry in enumerate(entries):
            pure_text = cls._extract_text_without_tags(entry.text)
            if pure_text and not pure_text.isspace():
                result.append((i, pure_text))
        return result

    @staticmethod
    def _build_index_map(entries: list[ASSEntry]) -> dict[int, ASSEntry]:
        """构建 header_line_index -> entry 的映射（用下标而非文本做键，避免碰撞）"""
        return {e.header_line_index: e for e in entries if e.header_line_index >= 0}

    @staticmethod
    def _rebuild_dialogue(entry: ASSEntry, text: str) -> str:
        """根据条目字段重建 Dialogue 行（不再重复正则匹配）"""
        return (f"Dialogue: {entry.layer},{entry.start_time},{entry.end_time},"
                f"{entry.style},{entry.name},{entry.margin_l},{entry.margin_r},"
                f"{entry.margin_v},{entry.effect},{text}")

    @classmethod
    def save(cls, headers: dict, entries: list[ASSEntry], file_path: str,
             encoding: str = "utf-8-sig"):
        """保存为ASS文件"""
        entry_map = cls._build_index_map(entries)
        events_key = "[Events]"
        with open(file_path, "w", encoding=encoding) as f:
            for section, lines in headers.items():
                f.write(f"{section}\n")
                for idx, line in enumerate(lines):
                    if section == events_key and idx in entry_map:
                        entry = entry_map[idx]
                        if entry.translated_text:
                            translated = entry.translated_text.replace("\n", "\\N")
                            f.write(cls._rebuild_dialogue(entry, translated) + "\n")
                            continue
                    f.write(f"{line}\n")
                f.write("\n")

    @classmethod
    def to_bilingual(cls, headers: dict, entries: list[ASSEntry],
                     file_path: str, encoding: str = "utf-8-sig"):
        """保存双语ASS字幕"""
        entry_map = cls._build_index_map(entries)
        events_key = "[Events]"
        with open(file_path, "w", encoding=encoding) as f:
            for section, lines in headers.items():
                f.write(f"{section}\n")
                for idx, line in enumerate(lines):
                    if section == events_key and idx in entry_map:
                        entry = entry_map[idx]
                        if entry.translated_text:
                            original = cls._extract_text_without_tags(entry.text)
                            translated = entry.translated_text
                            bilingual = f"{original}\\N{translated}".replace("\n", "\\N")
                            f.write(cls._rebuild_dialogue(entry, bilingual) + "\n")
                            continue
                    f.write(f"{line}\n")
                f.write("\n")
