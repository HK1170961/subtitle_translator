"""SRT字幕格式解析器"""

import re
import chardet


DETECT_SAMPLE_SIZE = 65536


class SubtitleEntry:
    """字幕条目"""

    __slots__ = ("index", "start_time", "end_time", "text", "translated_text")

    def __init__(self, index: int, start_time: str, end_time: str, text: str):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
        self.translated_text = ""

    def __repr__(self):
        return f"SubtitleEntry(index={self.index}, time={self.start_time} -> {self.end_time})"


class SRTParser:
    """SRT字幕解析器"""

    TIME_PATTERN = re.compile(
        r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})"
    )
    BLOCK_SPLIT = re.compile(r"\n\s*\n")

    @staticmethod
    def detect_encoding(file_path: str) -> str:
        """检测文件编码（仅读取前64KB）"""
        with open(file_path, "rb") as f:
            raw_data = f.read(DETECT_SAMPLE_SIZE)
        result = chardet.detect(raw_data)
        return result.get("encoding", "utf-8") or "utf-8"

    @classmethod
    def parse(cls, file_path: str) -> list[SubtitleEntry]:
        """解析SRT文件"""
        encoding = cls.detect_encoding(file_path)
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            content = f.read()
        return cls.parse_content(content)

    @classmethod
    def parse_content(cls, content: str) -> list[SubtitleEntry]:
        """解析SRT内容字符串"""
        entries = []
        blocks = cls.BLOCK_SPLIT.split(content.strip())

        for block in blocks:
            lines = block.split("\n")
            if len(lines) < 2:
                continue

            time_line_idx = -1
            for i, line in enumerate(lines):
                if cls.TIME_PATTERN.search(line):
                    time_line_idx = i
                    break

            if time_line_idx < 0:
                continue

            try:
                index = int(lines[0]) if time_line_idx > 0 else len(entries) + 1
            except ValueError:
                index = len(entries) + 1

            match = cls.TIME_PATTERN.search(lines[time_line_idx])
            if not match:
                continue
            start_time = match.group(1)
            end_time = match.group(2)

            text_lines = lines[time_line_idx + 1:]
            text = "\n".join(text_lines).strip()

            if text:
                entries.append(SubtitleEntry(index, start_time, end_time, text))

        return entries

    @staticmethod
    def save(entries: list[SubtitleEntry], file_path: str, encoding: str = "utf-8"):
        """保存为SRT文件"""
        with open(file_path, "w", encoding=encoding) as f:
            for i, entry in enumerate(entries, 1):
                f.write(f"{i}\n")
                f.write(f"{entry.start_time} --> {entry.end_time}\n")
                f.write(f"{entry.translated_text or entry.text}\n")
                f.write("\n")

    @staticmethod
    def to_bilingual(entries: list[SubtitleEntry], file_path: str, encoding: str = "utf-8"):
        """保存双语字幕"""
        with open(file_path, "w", encoding=encoding) as f:
            for i, entry in enumerate(entries, 1):
                f.write(f"{i}\n")
                f.write(f"{entry.start_time} --> {entry.end_time}\n")
                f.write(f"{entry.text}\n")
                if entry.translated_text:
                    f.write(f"{entry.translated_text}\n")
                f.write("\n")
