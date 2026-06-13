"""ASS/SSA字幕格式解析器"""

import re
import chardet


DETECT_SAMPLE_SIZE = 65536

TAG_PATTERN = re.compile(r"\{[^}]*\}")


class ASSEntry:
    """ASS字幕条目"""

    __slots__ = ("layer", "start_time", "end_time", "style", "name",
                 "margin_l", "margin_r", "margin_v", "effect", "text",
                 "raw_line", "translated_text")

    def __init__(self, layer: int, start_time: str, end_time: str,
                 style: str, name: str, margin_l: int, margin_r: int,
                 margin_v: int, effect: str, text: str, raw_line: str):
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

    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """检测文件编码（仅读取前64KB）"""
        with open(file_path, "rb") as f:
            raw_data = f.read(DETECT_SAMPLE_SIZE)
        result = chardet.detect(raw_data)
        return result.get("encoding", "utf-8") or "utf-8"

    @classmethod
    def parse(cls, file_path: str) -> tuple[dict, list[ASSEntry]]:
        """解析ASS文件，返回(头部信息, 对话条目列表)"""
        encoding = cls.detect_encoding(file_path)
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            content = f.read()
        return cls.parse_content(content)

    @classmethod
    def parse_content(cls, content: str) -> tuple[dict, list[ASSEntry]]:
        """解析ASS内容字符串"""
        headers = {}
        entries = []
        current_section = ""

        for line in content.split("\n"):
            line_stripped = line.strip()

            if line_stripped.startswith("[") and line_stripped.endswith("]"):
                current_section = line_stripped
                headers[current_section] = []
            elif current_section and line_stripped:
                if current_section not in headers:
                    headers[current_section] = []
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

    @classmethod
    def save(cls, headers: dict, entries: list[ASSEntry], file_path: str,
             encoding: str = "utf-8-sig"):
        """保存为ASS文件"""
        entry_map = cls._build_entry_map(entries)
        with open(file_path, "w", encoding=encoding) as f:
            for section, lines in headers.items():
                f.write(f"{section}\n")
                for line in lines:
                    if section == "[Events]" and line.startswith("Dialogue:"):
                        match = cls.DIALOGUE_PATTERN.match(line)
                        if match:
                            key = (match.group(2), match.group(3), match.group(10))
                            entry = entry_map.get(key)
                            if entry and entry.translated_text:
                                translated = entry.translated_text.replace("\n", "\\N")
                                new_line = f"Dialogue: {match.group(1)},{match.group(2)},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{translated}"
                                f.write(new_line + "\n")
                                continue
                    f.write(f"{line}\n")
                f.write("\n")

    @classmethod
    def _build_entry_map(cls, entries: list[ASSEntry]) -> dict:
        """构建条目索引映射 (start_time, end_time, text) -> entry"""
        entry_map = {}
        for entry in entries:
            key = (entry.start_time, entry.end_time, entry.text)
            entry_map[key] = entry
        return entry_map

    @classmethod
    def to_bilingual(cls, headers: dict, entries: list[ASSEntry],
                     file_path: str, encoding: str = "utf-8-sig"):
        """保存双语ASS字幕"""
        entry_map = cls._build_entry_map(entries)
        with open(file_path, "w", encoding=encoding) as f:
            for section, lines in headers.items():
                f.write(f"{section}\n")
                for line in lines:
                    if section == "[Events]" and line.startswith("Dialogue:"):
                        match = cls.DIALOGUE_PATTERN.match(line)
                        if match:
                            key = (match.group(2), match.group(3), match.group(10))
                            entry = entry_map.get(key)
                            if entry and entry.translated_text:
                                original = cls._extract_text_without_tags(entry.text)
                                translated = entry.translated_text
                                bilingual = f"{original}\\N{translated}".replace("\n", "\\N")
                                new_line = f"Dialogue: {match.group(1)},{match.group(2)},{match.group(3)},{match.group(4)},{match.group(5)},{match.group(6)},{match.group(7)},{match.group(8)},{match.group(9)},{bilingual}"
                                f.write(new_line + "\n")
                                continue
                    f.write(f"{line}\n")
                f.write("\n")
