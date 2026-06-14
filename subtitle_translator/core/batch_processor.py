"""批量字幕处理模块"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal

from .srt_parser import SRTParser, SubtitleEntry
from .ass_parser import ASSParser, ASSEntry
from .translator import LlamaTranslator


CONTEXT_LINES = 5  # 上下文行数


class TranslateWorker(QThread):
    """翻译工作线程（支持并发批次请求）"""

    progress = pyqtSignal(int, int, str)
    file_done = pyqtSignal(str, str)
    error = pyqtSignal(str)
    finished_all = pyqtSignal()

    def __init__(self, files: list[str], source_lang: str, target_lang: str,
                 output_dir: str, bilingual: bool = False,
                 host: str = "127.0.0.1", port: int = 8080,
                 temperature: float = 0.3, top_p: float = 0.9,
                 batch_size: int = 10, max_workers: int = 4):
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
        self.batch_size = max(1, int(batch_size))
        # 并发数至少为 1；<=0 时按 1 处理
        self.max_workers = max(1, int(max_workers))
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        # 用 with 确保 Session 在结束时关闭，避免连接泄漏
        with LlamaTranslator(self.host, self.port) as translator:
            total = len(self.files)

            for file_idx, file_path in enumerate(self.files):
                if self._stop_event.is_set():
                    break

                self.progress.emit(file_idx, total,
                                   f"Processing: {os.path.basename(file_path)}")

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
        """获取前后上下文（基于原文，并发安全）"""
        ctx_before = "\n".join(all_texts[max(0, start - CONTEXT_LINES):start]) if start > 0 else ""
        ctx_after = "\n".join(all_texts[end:min(len(all_texts), end + CONTEXT_LINES)]) if end < len(all_texts) else ""
        return ctx_before, ctx_after

    def _translate_all(self, translator: LlamaTranslator,
                       all_texts: list[str], total: int) -> list[str]:
        """并发翻译全部文本，返回按原顺序排列的译文列表。

        - 上下文基于原文（all_texts），相邻批次无译文依赖，天然可并发。
        - 通过 ThreadPoolExecutor 并发提交批次，as_completed 边完成边回填/上报。
        - 任何时刻 _stop_event 被置位即尽快返回。
        """
        results: list[str] = [""] * total

        # 预构建所有批次任务
        batches: list[tuple[int, int, list[str], str, str]] = []
        for i in range(0, total, self.batch_size):
            batch_end = min(i + self.batch_size, total)
            texts = all_texts[i:batch_end]
            ctx_before, ctx_after = self._get_context(all_texts, i, batch_end)
            batches.append((i, batch_end, texts, ctx_before, ctx_after))

        workers = min(self.max_workers, len(batches)) if batches else 1

        # 单批次直接串行，避免无谓的线程开销
        if workers <= 1 or len(batches) <= 1:
            for i, batch_end, texts, ctx_before, ctx_after in batches:
                if self._stop_event.is_set():
                    break
                self.progress.emit(i, total,
                                   f"Translating: {i+1}-{batch_end}/{total}")
                success, part = translator.translate_batch(
                    texts, self.source_lang, self.target_lang,
                    temperature=self.temperature, top_p=self.top_p,
                    context_before=ctx_before, context_after=ctx_after,
                )
                self._apply_results(results, i, batch_end, part, success)
            return results

        # 并发执行
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="translator") as pool:
            future_to_meta = {}
            for i, batch_end, texts, ctx_before, ctx_after in batches:
                if self._stop_event.is_set():
                    break
                fut = pool.submit(
                    translator.translate_batch,
                    texts, self.source_lang, self.target_lang,
                    self.temperature, self.top_p,
                    2048, ctx_before, ctx_after, 3,
                )
                future_to_meta[fut] = (i, batch_end)

            completed = 0
            total_batches = len(future_to_meta)
            for fut in as_completed(future_to_meta):
                if self._stop_event.is_set():
                    break
                i, batch_end = future_to_meta[fut]
                completed += 1
                self.progress.emit(i, total,
                                   f"Translating: {i+1}-{batch_end}/{total} "
                                   f"(batch {completed}/{total_batches})")
                try:
                    success, part = fut.result()
                except Exception as e:
                    success, part = False, [f"[Error: {e}"] * (batch_end - i)
                self._apply_results(results, i, batch_end, part, success)

        return results

    @staticmethod
    def _apply_results(results: list[str], start: int, end: int,
                       part: list[str], success: bool) -> None:
        """把单批次结果写回 results（按位置），失败批次统一标记。"""
        for j in range(start, end):
            k = j - start
            if success and k < len(part) and part[k]:
                results[j] = part[k]
            else:
                results[j] = "[Translation failed]" if not success else \
                    (part[k] if k < len(part) else "[Translation failed]")

    def _process_srt(self, translator: LlamaTranslator, file_path: str):
        """处理SRT文件"""
        entries = SRTParser.parse(file_path)
        if not entries:
            self.error.emit(f"No subtitles found: {os.path.basename(file_path)}")
            return

        total_entries = len(entries)
        all_texts = [e.text for e in entries]
        self.progress.emit(0, total_entries, f"Total: {total_entries} entries")

        translated = self._translate_all(translator, all_texts, total_entries)

        for entry, tr in zip(entries, translated):
            entry.translated_text = tr

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
        if total == 0:
            # 无可翻译文本，直接原样输出
            output_path = self._get_output_path(file_path, Path(file_path).suffix)
            if self.bilingual:
                ASSParser.to_bilingual(headers, entries, output_path)
            else:
                ASSParser.save(headers, entries, output_path)
            self.file_done.emit(file_path, output_path)
            return

        all_texts = [t[1] for t in translatable]
        self.progress.emit(0, total, f"Total: {total} dialogues")

        translated = self._translate_all(translator, all_texts, total)

        for (idx, _), tr in zip(translatable, translated):
            entries[idx].translated_text = tr

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
