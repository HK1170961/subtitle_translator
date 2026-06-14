"""翻译设置面板"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QCheckBox, QSpinBox,
    QGroupBox, QScrollArea, QFrame, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal

from ..core.translator import LlamaTranslator, LANGUAGE_MAP
from .styles import (SUCCESS, DANGER, FS_CAPTION, FW_SEMIBOLD,
                     H_CONTROL, H_BUTTON, H_BUTTON_LG)

LLAMA_DIR = str(Path(__file__).resolve().parent.parent.parent / "llama")


def parse_server_args(args_str: str) -> dict:
    """从原始参数字符串中解析关键参数"""
    result = {
        "port": 8080,
        "temperature": 0.3,
        "top_p": 0.9,
    }

    tokens = args_str.split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok in ("--port", "-p"):
            if i + 1 < len(tokens):
                try:
                    result["port"] = int(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
                continue

        if tok in ("--temp", "-t"):
            if i + 1 < len(tokens):
                try:
                    result["temperature"] = float(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
                continue

        if tok in ("--top-p",):
            if i + 1 < len(tokens):
                try:
                    result["top_p"] = float(tokens[i + 1])
                except ValueError:
                    pass
                i += 2
                continue

        i += 1

    return result


class SettingsPanel(QWidget):
    """翻译设置面板"""

    start_translate = pyqtSignal()
    stop_translate = pyqtSignal()
    test_connection = pyqtSignal()
    extract_subtitles = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(0)

        # ── 服务器连接 ──
        conn_group = QGroupBox("服务器连接")
        conn_layout = QVBoxLayout(conn_group)
        conn_layout.setSpacing(10)

        # Host + Port + 测试
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self._host_input = QLineEdit("127.0.0.1")
        self._host_input.setFixedWidth(130)
        row1.addWidget(self._host_input)
        row1.addWidget(QLabel(":"))
        self._port_label = QLabel("8080")
        self._port_label.setObjectName("port_label")
        self._port_label.setFixedWidth(50)
        row1.addWidget(self._port_label)

        self._btn_test = QPushButton("测试连接")
        self._btn_test.setObjectName("secondary")
        self._btn_test.setFixedHeight(H_BUTTON)
        self._btn_test.setMinimumWidth(80)
        self._btn_test.clicked.connect(self.test_connection.emit)
        row1.addWidget(self._btn_test)

        self._status_label = QLabel("未连接")
        self._status_label.setObjectName("hint")
        self._status_label.setWordWrap(False)
        self._status_label.setMinimumWidth(80)
        row1.addWidget(self._status_label, 1)
        conn_layout.addLayout(row1)

        # 模型选择
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(QLabel("模型:"))
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(200)
        self._refresh_models()
        row2.addWidget(self._model_combo, 1)

        self._btn_refresh = QPushButton("刷新列表")
        self._btn_refresh.setObjectName("secondary")
        self._btn_refresh.setFixedHeight(H_BUTTON)
        self._btn_refresh.setMinimumWidth(80)
        self._btn_refresh.clicked.connect(self._refresh_models)
        row2.addWidget(self._btn_refresh)
        conn_layout.addLayout(row2)

        layout.addWidget(conn_group)

        # ── 服务器参数 ──
        args_group = QGroupBox("llama-server 参数")
        args_layout = QVBoxLayout(args_group)
        args_layout.setSpacing(6)

        self._server_args = QTextEdit()
        self._server_args.setPlaceholderText(
            "示例: -ngl 100 --port $port --temp 0.7 --top-p 0.6 --top-k 20 -n 4096"
        )
        self._server_args.setFixedHeight(60)
        args_layout.addWidget(self._server_args)

        hint = QLabel("$port 会自动替换为端口号，翻译时自动启动服务器")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        args_layout.addWidget(hint)

        layout.addWidget(args_group)

        # ── 翻译设置 ──
        trans_group = QGroupBox("翻译设置")
        trans_layout = QVBoxLayout(trans_group)
        trans_layout.setSpacing(10)

        lang_names = list(LANGUAGE_MAP.keys())

        lang_row = QHBoxLayout()
        lang_row.setSpacing(6)
        lang_row.addWidget(QLabel("源语言:"))
        self._source_lang = QComboBox()
        self._source_lang.addItems(lang_names)
        self._source_lang.setCurrentText("English")
        self._source_lang.setFixedHeight(H_CONTROL)
        lang_row.addWidget(self._source_lang, 1)

        self._btn_swap = QPushButton("交换")
        self._btn_swap.setObjectName("secondary")
        self._btn_swap.setFixedSize(60, H_BUTTON)
        self._btn_swap.clicked.connect(self._swap_languages)
        lang_row.addWidget(self._btn_swap)

        self._target_lang = QComboBox()
        self._target_lang.addItems(lang_names)
        self._target_lang.setCurrentText("简体中文")
        self._target_lang.setFixedHeight(H_CONTROL)
        lang_row.addWidget(self._target_lang, 1)
        trans_layout.addLayout(lang_row)

        opt_row = QHBoxLayout()
        opt_row.setSpacing(6)
        opt_row.addWidget(QLabel("批量:"))
        self._batch_size = QLineEdit("10")
        self._batch_size.setFixedWidth(50)
        self._batch_size.setFixedHeight(H_CONTROL)
        opt_row.addWidget(self._batch_size)
        opt_row.addSpacing(12)
        opt_row.addWidget(QLabel("并发:"))
        self._max_workers = QSpinBox()
        self._max_workers.setRange(1, 16)
        self._max_workers.setValue(4)
        self._max_workers.setFixedWidth(64)
        self._max_workers.setFixedHeight(H_CONTROL)
        # 彻底隐藏上下箭头按钮（Apple 风格数字框无 spinner，比 QSS 隐藏更可靠）
        self._max_workers.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self._max_workers.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._max_workers.setToolTip("同时发送的翻译请求数。\n本地 LLM 并发过高可能因显存不足变慢或报错，建议 2-6。")
        opt_row.addWidget(self._max_workers)
        opt_row.addSpacing(12)
        self._bilingual_check = QCheckBox("双语字幕")
        self._bilingual_check.setChecked(False)
        opt_row.addWidget(self._bilingual_check)
        opt_row.addStretch()
        trans_layout.addLayout(opt_row)

        layout.addWidget(trans_group)

        # ── Whisper 设置 ──
        whisper_group = QGroupBox("Whisper 提取")
        whisper_layout = QVBoxLayout(whisper_group)
        whisper_layout.setSpacing(10)

        whisper_hint = QLabel("模型首次使用时自动从 HuggingFace 下载，缓存后离线可用")
        whisper_hint.setObjectName("hint")
        whisper_hint.setWordWrap(True)
        whisper_layout.addWidget(whisper_hint)

        opts_row = QHBoxLayout()
        opts_row.setSpacing(6)
        opts_row.addWidget(QLabel("语言:"))
        self._whisper_lang = QComboBox()
        self._whisper_lang.addItems(["ja", "en", "zh", "ko", "auto"])
        self._whisper_lang.setFixedWidth(60)
        self._whisper_lang.setFixedHeight(H_CONTROL)
        opts_row.addWidget(self._whisper_lang)
        opts_row.addSpacing(8)
        opts_row.addWidget(QLabel("模型:"))
        self._whisper_model = QComboBox()
        self._whisper_model.addItems([
            "large-v3-turbo",
            "large-v3",
            "medium",
            "small",
            "base",
            "tiny",
        ])
        self._whisper_model.setFixedHeight(H_CONTROL)
        opts_row.addWidget(self._whisper_model, 1)
        whisper_layout.addLayout(opts_row)

        opt_row2 = QHBoxLayout()
        opt_row2.setSpacing(12)
        self._separate_check = QCheckBox("人声分离")
        self._separate_check.setChecked(True)
        opt_row2.addWidget(self._separate_check)
        self._auto_translate_check = QCheckBox("提取后自动翻译")
        self._auto_translate_check.setChecked(True)
        opt_row2.addWidget(self._auto_translate_check)
        self._vad_check = QCheckBox("VAD")
        self._vad_check.setChecked(True)
        opt_row2.addWidget(self._vad_check)
        opt_row2.addStretch()
        whisper_layout.addLayout(opt_row2)

        self._btn_extract = QPushButton("提取字幕")
        self._btn_extract.setObjectName("primary")
        self._btn_extract.setFixedHeight(H_BUTTON_LG)
        self._btn_extract.clicked.connect(self.extract_subtitles.emit)
        whisper_layout.addWidget(self._btn_extract)

        layout.addWidget(whisper_group)

        # ── 输出设置 ──
        output_group = QGroupBox("输出设置")
        output_layout = QHBoxLayout(output_group)
        output_layout.setSpacing(6)

        self._output_dir = QLineEdit()
        self._output_dir.setPlaceholderText("输出目录（默认：源文件所在目录）")
        self._output_dir.setFixedHeight(H_CONTROL)
        output_layout.addWidget(self._output_dir, 1)
        self._btn_browse = QPushButton("浏览")
        self._btn_browse.setObjectName("secondary")
        self._btn_browse.setFixedWidth(60)
        self._btn_browse.setFixedHeight(H_BUTTON)
        self._btn_browse.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(self._btn_browse)

        layout.addWidget(output_group)

        # ── 操作按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._btn_start = QPushButton("开始翻译")
        self._btn_start.setObjectName("success")
        self._btn_start.setFixedHeight(H_BUTTON_LG)
        self._btn_start.clicked.connect(self.start_translate.emit)
        btn_layout.addWidget(self._btn_start)

        self._btn_stop = QPushButton("停止")
        self._btn_stop.setObjectName("danger")
        self._btn_stop.setFixedHeight(H_BUTTON_LG)
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self.stop_translate.emit)
        btn_layout.addWidget(self._btn_stop)

        layout.addLayout(btn_layout)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setValue(0)
        self._progress.setVisible(False)
        self._progress.setFixedHeight(6)
        layout.addWidget(self._progress)

        # 状态文字
        self._status_text = QLabel("")
        self._status_text.setObjectName("status_text")
        self._status_text.setWordWrap(True)
        self._status_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._status_text)

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _swap_languages(self):
        src = self._source_lang.currentText()
        tgt = self._target_lang.currentText()
        self._source_lang.setCurrentText(tgt)
        self._target_lang.setCurrentText(src)

    def _browse_output_dir(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if folder:
            self._output_dir.setText(folder)

    def _refresh_models(self):
        """扫描llama目录下的模型文件"""
        self._model_combo.clear()
        if not os.path.isdir(LLAMA_DIR):
            self._model_combo.addItem("(未找到 llama/ 文件夹)")
            return

        models = []
        for f in os.listdir(LLAMA_DIR):
            if f.lower().endswith(".gguf"):
                size_mb = os.path.getsize(os.path.join(LLAMA_DIR, f)) // (1024 * 1024)
                models.append((f, size_mb))

        models.sort(key=lambda x: x[0])

        if not models:
            self._model_combo.addItem("(未找到 .gguf 模型)")
            return

        for name, size_mb in models:
            self._model_combo.addItem(f"{name}  ({size_mb} MB)", name)

    def get_selected_model(self) -> str:
        """获取选中的模型文件名"""
        data = self._model_combo.currentData()
        return data if data else ""

    def get_selected_model_path(self) -> str:
        """获取选中的模型完整路径"""
        model = self.get_selected_model()
        if model:
            return os.path.join(LLAMA_DIR, model)
        return ""

    def set_connected(self, connected: bool, status: str = ""):
        if connected:
            self._status_label.setText(f"已连接 - {status}")
            self._status_label.setStyleSheet(
                f"color: {SUCCESS}; font-size: {FS_CAPTION}; font-weight: {FW_SEMIBOLD};"
            )
        else:
            self._status_label.setText(f"{status or '未连接'}")
            self._status_label.setStyleSheet(
                f"color: {DANGER}; font-size: {FS_CAPTION}; font-weight: {FW_SEMIBOLD};"
            )

    def set_translating(self, translating: bool):
        self._btn_start.setEnabled(not translating)
        self._btn_stop.setEnabled(translating)
        self._progress.setVisible(translating)

    def set_extracting(self, extracting: bool):
        self._btn_extract.setEnabled(not extracting)
        self._btn_start.setEnabled(not extracting)
        self._progress.setVisible(extracting)

    def set_progress(self, value: int, maximum: int = 100):
        self._progress.setMaximum(maximum)
        self._progress.setValue(value)

    def set_status(self, text: str):
        self._status_text.setText(text)

    def set_port_display(self, port: int):
        self._port_label.setText(str(port))

    def get_settings(self) -> dict:
        raw_args = self._server_args.toPlainText().strip()
        parsed = parse_server_args(raw_args)
        port = parsed["port"]

        try:
            batch_size = int(self._batch_size.text().strip())
        except ValueError:
            batch_size = 10

        return {
            "host": self._host_input.text().strip(),
            "port": port,
            "model": self.get_selected_model(),
            "model_path": self.get_selected_model_path(),
            "source_lang": LANGUAGE_MAP.get(self._source_lang.currentText(), "en"),
            "target_lang": LANGUAGE_MAP.get(self._target_lang.currentText(), "zh"),
            "source_lang_name": self._source_lang.currentText(),
            "target_lang_name": self._target_lang.currentText(),
            "temperature": parsed["temperature"],
            "top_p": parsed["top_p"],
            "batch_size": batch_size,
            "max_workers": self._max_workers.value(),
            "bilingual": self._bilingual_check.isChecked(),
            "output_dir": self._output_dir.text().strip(),
            "server_args": raw_args,
            "whisper_model": self._whisper_model.currentText(),
            "whisper_lang": self._whisper_lang.currentText(),
            "use_vad": self._vad_check.isChecked(),
            "separate_vocals": self._separate_check.isChecked(),
            "auto_translate": self._auto_translate_check.isChecked(),
        }

    def load_settings(self, config: dict):
        if "server" in config:
            self._host_input.setText(config["server"].get("host", "127.0.0.1"))
            self._port_label.setText(str(config["server"].get("port", 8080)))
        if "translation" in config:
            t = config["translation"]
            lang_names = list(LANGUAGE_MAP.keys())
            lang_codes = list(LANGUAGE_MAP.values())
            src_code = t.get("source_lang", "en")
            tgt_code = t.get("target_lang", "zh")
            if src_code in lang_codes:
                self._source_lang.setCurrentText(lang_names[lang_codes.index(src_code)])
            if tgt_code in lang_codes:
                self._target_lang.setCurrentText(lang_names[lang_codes.index(tgt_code)])
            self._batch_size.setText(str(t.get("batch_size", 10)))
            try:
                self._max_workers.setValue(int(t.get("max_workers", 4)))
            except (ValueError, TypeError):
                self._max_workers.setValue(4)
            self._bilingual_check.setChecked(t.get("bilingual", False))
        if "server_args" in config:
            self._server_args.setPlainText(config.get("server_args", ""))
        saved_model = config.get("model", "")
        if saved_model:
            for i in range(self._model_combo.count()):
                if self._model_combo.itemData(i) == saved_model:
                    self._model_combo.setCurrentIndex(i)
                    break
        # whisper_model 兼容旧的 ggml 文件名
        saved_whisper_model = config.get("whisper_model", "large-v3-turbo")
        _whisper_compat = {
            "ggml-large-v3-turbo.bin": "large-v3-turbo",
            "ggml-large-v3.bin": "large-v3",
            "ggml-medium.bin": "medium",
            "ggml-small.bin": "small",
            "ggml-base.bin": "base",
        }
        saved_whisper_model = _whisper_compat.get(saved_whisper_model, saved_whisper_model)
        if saved_whisper_model not in [self._whisper_model.itemText(i)
                                        for i in range(self._whisper_model.count())]:
            saved_whisper_model = "large-v3-turbo"
        self._whisper_model.setCurrentText(saved_whisper_model)
        self._whisper_lang.setCurrentText(config.get("whisper_lang", "ja"))
        self._vad_check.setChecked(config.get("use_vad", True))
        self._separate_check.setChecked(config.get("separate_vocals", True))
        self._auto_translate_check.setChecked(config.get("auto_translate", True))
