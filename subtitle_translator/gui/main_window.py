"""主窗口模块"""

import os
import subprocess
import time
import threading
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QLabel, QMessageBox, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from .file_panel import FilePanel
from .settings_panel import SettingsPanel, parse_server_args
from .styles import GLOBAL_STYLE
from .icons import app_icon
from ..core.translator import LlamaTranslator
from ..core.batch_processor import TranslateWorker
from ..core.whisper_extractor import WhisperWorker
from ..utils.config import load_config, save_config


LLAMA_DIR = str(Path(__file__).resolve().parent.parent.parent / "llama")


class MainWindow(QMainWindow):
    """字幕翻译工具主窗口"""

    def __init__(self):
        super().__init__()
        self.config = load_config()
        self._worker = None
        self._llama_process = None
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        self.setWindowTitle("Subtitle Translator")
        self.setWindowIcon(app_icon())
        self.setMinimumSize(760, 640)
        self.resize(
            self.config.get("ui", {}).get("window_width", 960),
            self.config.get("ui", {}).get("window_height", 720)
        )
        self.setStyleSheet(GLOBAL_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 左侧 - 文件面板
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self._file_panel = FilePanel()
        left_layout.addWidget(self._file_panel)

        # 右侧 - 设置面板
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self._settings_panel = SettingsPanel()
        self._settings_panel.test_connection.connect(self._check_connection)
        self._settings_panel.start_translate.connect(self._start_translation)
        self._settings_panel.stop_translate.connect(self._stop_translation)
        self._settings_panel.extract_subtitles.connect(self._start_extraction)
        right_layout.addWidget(self._settings_panel)

        # 主分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([320, 640])
        splitter.setHandleWidth(1)

        main_layout.addWidget(splitter)

        # 状态栏
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("就绪")
        self._status_bar.setFixedHeight(24)

    def _load_settings(self):
        self._settings_panel.load_settings(self.config)

    def _save_settings(self):
        settings = self._settings_panel.get_settings()
        self.config["server"]["host"] = settings["host"]
        self.config["server"]["port"] = settings["port"]
        self.config["model"] = settings["model"]
        self.config["translation"]["source_lang"] = settings["source_lang"]
        self.config["translation"]["target_lang"] = settings["target_lang"]
        self.config["translation"]["batch_size"] = settings["batch_size"]
        self.config["translation"]["bilingual"] = settings["bilingual"]
        self.config["server_args"] = settings["server_args"]
        self.config["whisper_model"] = settings.get("whisper_model", "ggml-large-v3-turbo.bin")
        self.config["whisper_lang"] = settings.get("whisper_lang", "ja")
        self.config["whisper_args"] = settings.get("whisper_args", "")
        self.config["separate_vocals"] = settings.get("separate_vocals", True)
        self.config["auto_translate"] = settings.get("auto_translate", True)
        save_config(self.config)

    def _check_connection(self):
        settings = self._settings_panel.get_settings()
        host = settings["host"]
        port = settings["port"]

        self._status_bar.showMessage(f"正在检查 {host}:{port}...")
        self._settings_panel.set_port_display(port)

        translator = LlamaTranslator(host, port)
        ok, status = translator.check_connection()

        self._settings_panel.set_connected(ok, status)
        self._status_bar.showMessage(f"状态: {status}")
        return ok

    def _start_server(self, settings: dict) -> bool:
        """启动llama-server"""
        host = settings["host"]
        port = settings["port"]

        translator = LlamaTranslator(host, port)
        ok, _ = translator.check_connection()
        if ok:
            self._settings_panel.set_status("服务器已在运行")
            return True

        server_exe = os.path.join(LLAMA_DIR, "llama-server.exe")
        if not os.path.exists(server_exe):
            self._settings_panel.set_status(f"未找到 llama-server.exe: {LLAMA_DIR}")
            return False

        model_file = settings.get("model_path", "")
        if not model_file or not os.path.exists(model_file):
            self._settings_panel.set_status("未选择模型或模型不存在")
            return False

        cmd = [server_exe, "-m", model_file]
        server_args = settings.get("server_args", "")

        if server_args:
            expanded = server_args.replace("$port", str(port))
            cmd.extend(expanded.split())
        else:
            cmd.extend(["--host", "127.0.0.1", "--port", str(port)])

        args_str = " ".join(cmd)
        if "--host" not in args_str:
            cmd.extend(["--host", "127.0.0.1"])
        if "--port" not in args_str:
            cmd.extend(["--port", str(port)])

        self._settings_panel.set_status("正在启动 llama-server...")
        self._status_bar.showMessage("正在启动 llama-server...")

        try:
            self._llama_process = subprocess.Popen(
                cmd,
                cwd=LLAMA_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            self._settings_panel.set_status(f"启动失败: {e}")
            return False

        self._settings_panel.set_status("等待服务器加载模型...")
        for i in range(60):
            time.sleep(1)
            ok, status = translator.check_connection()
            if ok:
                self._settings_panel.set_connected(True, status)
                self._settings_panel.set_status("服务器就绪")
                self._status_bar.showMessage("服务器就绪")
                return True
            self._settings_panel.set_status(f"等待中... ({i+1}s)")

        self._settings_panel.set_status("服务器启动超时")
        return False

    def _on_files_changed(self, files: list[str]):
        self._status_bar.showMessage(f"已加载 {len(files)} 个文件")

    def _start_extraction(self):
        """仅提取字幕（不翻译）"""
        files = self._file_panel.files
        if not files:
            QMessageBox.warning(self, "警告", "请先添加视频文件")
            return

        video_files = [f for f in files if FilePanel.is_video_file(f)]
        if not video_files:
            QMessageBox.warning(self, "警告", "未选择视频文件。\n请添加 .mp4/.mkv/.avi/.webm/.ts 文件。")
            return

        settings = self._settings_panel.get_settings()
        output_dir = settings["output_dir"]
        if not output_dir:
            output_dir = str(Path(video_files[0]).parent)
        os.makedirs(output_dir, exist_ok=True)
        self._save_settings()

        self._whisper_output_dir = os.path.join(output_dir, "whisper_output")
        self._pending_video_files = video_files
        self._pending_subtitle_files = []
        self._pending_settings = settings
        self._pending_output_dir = output_dir
        self._start_whisper_extraction(video_files, settings, self._whisper_output_dir)

    def _start_whisper_extraction(self, video_files: list, settings: dict, output_dir: str):
        """启动Whisper提取流程"""
        self._whisper_index = 0
        self._whisper_video_files = video_files
        self._whisper_srt_files = []
        self._settings_panel.set_extracting(True)
        self._settings_panel.set_status("正在启动 Whisper 提取...")
        self._extract_next_video()

    def _extract_next_video(self):
        """提取下一个视频"""
        if self._whisper_index >= len(self._whisper_video_files):
            # 所有视频提取完成
            self._on_whisper_extraction_done()
            return

        video_path = self._whisper_video_files[self._whisper_index]
        settings = self._pending_settings
        self._settings_panel.set_status(f"正在提取 ({self._whisper_index+1}/{len(self._whisper_video_files)}): {os.path.basename(video_path)}")

        self._whisper_worker = WhisperWorker(
            video_path=video_path,
            output_dir=self._whisper_output_dir,
            model=settings.get("whisper_model", "ggml-large-v3-turbo.bin"),
            language=settings.get("whisper_lang", "ja"),
            separate=settings.get("separate_vocals", True),
            custom_args=settings.get("whisper_args", "")
        )
        self._whisper_worker.progress.connect(self._on_whisper_progress)
        self._whisper_worker.error.connect(self._on_whisper_error)
        self._whisper_worker.finished.connect(self._on_whisper_finished)
        self._whisper_worker.start()

    def _on_whisper_progress(self, msg: str):
        self._settings_panel.set_status(msg)

    def _on_whisper_error(self, error: str):
        self._settings_panel.set_status(f"Whisper 错误: {error}")
        QMessageBox.warning(self, "Whisper 错误", f"字幕提取失败:\n{error}")
        self._whisper_index += 1
        self._extract_next_video()

    def _on_whisper_finished(self, srt_path: str):
        """单个视频Whisper提取完成"""
        self._whisper_srt_files.append(srt_path)
        self._whisper_index += 1
        self._extract_next_video()

    def _on_whisper_extraction_done(self):
        """所有视频提取完成"""
        all_files = self._pending_subtitle_files + self._whisper_srt_files
        if not all_files:
            self._settings_panel.set_extracting(False)
            self._settings_panel.set_status("没有需要翻译的字幕")
            QMessageBox.warning(self, "警告", "没有需要翻译的字幕文件")
            return

        auto_translate = self._pending_settings.get("auto_translate", True)
        if auto_translate:
            self._start_translate_with_server_check(all_files, self._pending_settings, self._pending_output_dir)
        else:
            self._settings_panel.set_extracting(False)
            self._settings_panel.set_status(f"已提取 {len(self._whisper_srt_files)} 个字幕文件")
            self._cleanup_whisper_cache()
            QMessageBox.information(self, "完成",
                f"Whisper 已提取 {len(self._whisper_srt_files)} 个字幕文件。\n输出目录: {self._whisper_output_dir}")

    def _start_translate_with_server_check(self, files: list, settings: dict, output_dir: str):
        """检查服务器状态并开始翻译"""
        self._settings_panel.set_translating(True)
        translator = LlamaTranslator(settings["host"], settings["port"])
        ok, _ = translator.check_connection()

        if ok:
            self._do_translate(files, settings, output_dir)
        else:
            self._settings_panel.set_status("正在启动服务器...")
            self._pending_files = files
            self._pending_settings = settings
            self._pending_output_dir = output_dir
            threading.Thread(target=self._start_server_thread, daemon=True).start()

    def _start_translation(self):
        files = self._file_panel.files
        if not files:
            QMessageBox.warning(self, "警告", "请先添加字幕或视频文件")
            return

        settings = self._settings_panel.get_settings()
        output_dir = settings["output_dir"]
        if not output_dir:
            output_dir = str(Path(files[0]).parent)
        os.makedirs(output_dir, exist_ok=True)
        self._save_settings()

        # 检查是否有视频文件需要Whisper提取
        video_files = [f for f in files if FilePanel.is_video_file(f)]
        subtitle_files = [f for f in files if FilePanel.is_subtitle_file(f)]

        if video_files:
            # 有视频文件，先执行Whisper提取
            self._whisper_output_dir = os.path.join(output_dir, "whisper_output")
            self._pending_video_files = video_files
            self._pending_subtitle_files = subtitle_files
            self._pending_settings = settings
            self._pending_output_dir = output_dir
            self._start_whisper_extraction(video_files, settings, self._whisper_output_dir)
        else:
            # 只有字幕文件，直接翻译
            self._settings_panel.set_translating(True)
            self._start_translate_with_server_check(subtitle_files, settings, output_dir)

    def _start_server_thread(self):
        """后台启动服务器"""
        ok = self._start_server(self._pending_settings)
        # 服务器启动成功后，用 QTimer.singleShot 回到主线程执行翻译
        if ok:
            QTimer.singleShot(100, self._start_translate_after_server)
        else:
            QTimer.singleShot(0, self._on_server_start_failed)

    def _start_translate_after_server(self):
        """服务器启动后开始翻译"""
        self._do_translate(self._pending_files, self._pending_settings, self._pending_output_dir)

    def _on_server_start_failed(self):
        self._settings_panel.set_translating(False)
        self._settings_panel.set_status("服务器启动失败")
        QMessageBox.critical(
            self, "错误",
            "llama-server 启动失败。\n"
            "请检查 llama/ 文件夹中是否存在 llama-server.exe 和模型文件。"
        )

    def _do_translate(self, files, settings, output_dir):
        self._worker = TranslateWorker(
            files=files,
            source_lang=settings["source_lang_name"],
            target_lang=settings["target_lang_name"],
            output_dir=output_dir,
            bilingual=settings["bilingual"],
            host=settings["host"],
            port=settings["port"],
            temperature=settings["temperature"],
            top_p=settings["top_p"],
            batch_size=settings["batch_size"],
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.error.connect(self._on_error)
        self._worker.finished_all.connect(self._on_finished)

        self._status_bar.showMessage("正在翻译...")
        self._worker.start()

    def _stop_translation(self):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._status_bar.showMessage("正在停止...")

    def _on_progress(self, current: int, total: int, status: str):
        self._settings_panel.set_progress(current, total)
        self._settings_panel.set_status(status)
        self._status_bar.showMessage(status)

    def _on_file_done(self, input_path: str, output_path: str):
        self._status_bar.showMessage(
            f"完成: {os.path.basename(input_path)} → {os.path.basename(output_path)}"
        )

    def _on_error(self, error: str):
        self._status_bar.showMessage(f"错误: {error}")

    def _cleanup_whisper_cache(self):
        """清理整个Whisper输出缓存目录"""
        if not hasattr(self, '_whisper_output_dir') or not self._whisper_output_dir:
            return
        if not os.path.isdir(self._whisper_output_dir):
            return

        try:
            shutil.rmtree(self._whisper_output_dir, ignore_errors=True)
        except Exception:
            pass

    def _on_finished(self):
        self._settings_panel.set_translating(False)
        self._settings_panel.set_status("翻译完成！")
        self._status_bar.showMessage("完成")
        self._cleanup_whisper_cache()
        QMessageBox.information(self, "完成", "所有字幕文件已翻译！")

    def closeEvent(self, event):
        self._save_settings()
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        if hasattr(self, '_whisper_worker') and self._whisper_worker.isRunning():
            self._whisper_worker.wait(3000)
        # 关闭llama-server进程
        self._kill_llama_server()
        event.accept()

    def _kill_llama_server(self):
        """关闭llama-server进程（包括外部启动的）"""
        # 关闭自己启动的进程
        if self._llama_process:
            try:
                self._llama_process.terminate()
                self._llama_process.wait(3000)
            except Exception:
                pass
            self._llama_process = None

        # 通过端口查找并关闭所有llama-server进程
        settings = self._settings_panel.get_settings()
        port = settings["port"]

        try:
            import subprocess
            # 查找占用端口的进程
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            for line in result.stdout.split("\n"):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pid = parts[-1]
                        # 关闭进程
                        subprocess.run(
                            ["taskkill", "/F", "/PID", pid],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
                        )
        except Exception:
            pass
