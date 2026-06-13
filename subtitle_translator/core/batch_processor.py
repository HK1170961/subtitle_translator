"""批量字幕处理模块"""

import os
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from .srt_parser import SRTParser, SubtitleEntry
from .ass_parser import ASSParser, ASSEntry
from .translator import LlamaTranslator


CONTEXT_LINES = 5  # 上下文行数


class TranslateWorker(QThread):
    """翻译工作线程"""
    progress = pyqtSignal(int, int, str)
    file_done = pyqtSignal(str, str)
    error = pyqtSignal(str)
    finished_all = pyqtSignal()

    def __init__(self, files: list[str], source_lang: str, target_lang: str,
                 output_dir: str, bilingual: bool = False,
                 host: str = "127.0.0.1", port: int = 8080,
                 temperature: float = 0.3, top_p: float = 0.9,
                 batch_size: int = 10):
        super().__init__()
        self.files = files
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.output_dir = output_dir
        self.bilingual = bilingual
        self.host = host
        self.port = port
        self.temperature = temperature
        self.top_p = top_p
        self.batch_size = batch_size
        self._running = True

    def stop(self):
        self._running = False

    def run(self):
        translator = LlamaTranslator(self.host, self.port)
        total = len(self.files)

        for file_idx, file_path in enumerate(self.files):
            if not self._running:
                break

            self.progress.emit(file_idx, total, f"Processing: {os.path.basename(file_path)}")

            try:
                ext = Path(file_path).suffix.lower()
                if ext == ".srt":
                    self._process_srt(translator, file_path)
                elif ext in (".ass", ".ssa"):
                    self._process_ass(translator, file_path)
                else:
                    self.error.emit(f"Unsupported format: {ext}")
                    continue
            except Exception as e:
                self.error.emit(f"Failed {os.path.basename(file_path)}: {str(e)}")

        self.finished_all.emit()

    def _get_context(self, all_texts: list[str], start: int, end: int) -> tuple[str, str]:
        """获取前后上下文"""
        ctx_before = "\n".join(all_texts[max(0, start - CONTEXT_LINES):start]) if start > 0 else ""
        ctx_after = "\n".join(all_texts[end:min(len(all_texts), end + CONTEXT_LINES)]) if end < len(all_texts) else ""
        return ctx_before, ctx_after

    def _process_srt(self, translator: LlamaTranslator, file_path: str):
        """处理SRT文件"""
        entries = SRTParser.parse(file_path)
        if not entries:
            self.error.emit(f"No subtitles found: {os.path.basename(file_path)}")
            return

        total_entries = len(entries)
        all_texts = [e.text for e in entries]
        self.progress.emit(0, total_entries, f"Total: {total_entries} entries")

        # 分批翻译，带上下文
        for i in range(0, total_entries, self.batch_size):
            if not self._running:
                break

            batch_end = min(i + self.batch_size, total_entries)
            batch = entries[i:batch_end]
            texts = [e.text for e in batch]

            ctx_before, ctx_after = self._get_context(all_texts, i, batch_end)

            self.progress.emit(i, total_entries,
                               f"Translating: {i+1}-{batch_end}/{total_entries}")

            success, results = translator.translate_batch(
                texts, self.source_lang, self.target_lang,
                temperature=self.temperature, top_p=self.top_p,
                context_before=ctx_before, context_after=ctx_after
            )

            if success:
                for j, entry in enumerate(batch):
                    entry.translated_text = results[j] if j < len(results) else ""
            else:
                for entry in batch:
                    entry.translated_text = "[Translation failed]"

        # 保存输出
        output_path = self._get_output_path(file_path, ".srt")
        if self.bilingual:
            SRTParser.to_bilingual(entries, output_path)
        else:
            SRTParser.save(entries, output_path)

        self.file_done.emit(file_path, output_path)

    def _process_ass(self, translator: LlamaTranslator, file_path: str):
        """处理ASS文件"""
        headers, entries = ASSParser.parse(file_path)
        if not entries:
            self.error.emit(f"No dialogues found: {os.path.basename(file_path)}")
            return

        translatable = ASSParser.get_translatable_texts(entries)
        total = len(translatable)
        all_texts = [t[1] for t in translatable]
        self.progress.emit(0, total, f"Total: {total} dialogues")

        # 分批翻译，带上下文
        for i in range(0, total, self.batch_size):
            if not self._running:
                break

            batch_end = min(i + self.batch_size, total)
            batch_indices = translatable[i:batch_end]
            texts = [t[1] for t in batch_indices]

            ctx_before, ctx_after = self._get_context(all_texts, i, batch_end)

            self.progress.emit(i, total,
                               f"Translating: {i+1}-{batch_end}/{total}")

            success, results = translator.translate_batch(
                texts, self.source_lang, self.target_lang,
                temperature=self.temperature, top_p=self.top_p,
                context_before=ctx_before, context_after=ctx_after
            )

            if success:
                for j, (idx, _) in enumerate(batch_indices):
                    if j < len(results):
                        entries[idx].translated_text = results[j]
            else:
                for idx, _ in batch_indices:
                    entries[idx].translated_text = "[Translation failed]"

        # 保存输出
        output_path = self._get_output_path(file_path, Path(file_path).suffix)
        if self.bilingual:
            ASSParser.to_bilingual(headers, entries, output_path)
        else:
            ASSParser.save(headers, entries, output_path)

        self.file_done.emit(file_path, output_path)

    def _get_output_path(self, file_path: str, ext: str) -> str:
        """生成输出文件路径"""
        name = Path(file_path).stem
        output_name = f"{name}_中文字幕{ext}"
        output_path = os.path.join(self.output_dir, output_name)

        counter = 1
        while os.path.exists(output_path):
            output_name = f"{name}_中文字幕_{counter}{ext}"
            output_path = os.path.join(self.output_dir, output_name)
            counter += 1

        return output_path
