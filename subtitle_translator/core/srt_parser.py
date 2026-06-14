"""SRT字幕格式解析器"""

import re
import chardet


DETECT_SAMPLE_SIZE = 65536


def _decode_subtitle_bytes(raw: bytes) -> str:
    """稳健地解码字幕字节流。

    顺序：UTF-8（严格）→ chardet 检测 → GBK → UTF-8(replace)。
    相比单一 chardet 检测，可避免中文被误判为 latin-1/Windows-1252 后变乱码。
    """
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
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
    try:
        return raw.decode("gbk")
    except (UnicodeDecodeError, LookupError):
        pass
    return raw.decode("utf-8", errors="replace")


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

    @classmethod
    def parse(cls, file_path: str) -> list[SubtitleEntry]:
        """解析SRT文件"""
        with open(file_path, "rb") as f:
            raw = f.read()
        content = _decode_subtitle_bytes(raw)
        return cls.parse_content(content)

    @classmethod
    def parse_content(cls, content: str) -> list[SubtitleEntry]:
        """解析SRT内容字符串"""
        entries = []
        # 统一行尾（兼容 CRLF / CR），避免中间行残留 \r 写入输出
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        blocks = cls.BLOCK_SPLIT.split(content.strip())

        for block in blocks:
            lines = block.split("\n")
            if len(lines) < 2:
                continue

            # 找到时间行，复用 match 对象避免二次正则扫描
            time_line_idx = -1
            match = None
            for i, line in enumerate(lines):
                match = cls.TIME_PATTERN.search(line)
                if match:
                    time_line_idx = i
                    break

            if time_line_idx < 0 or not match:
                continue

            try:
                index = int(lines[0]) if time_line_idx > 0 else len(entries) + 1
            except ValueError:
                index = len(entries) + 1

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
