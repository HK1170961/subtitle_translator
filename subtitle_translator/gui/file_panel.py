"""文件管理面板"""

import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QLabel, QFileDialog, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent


class FilePanel(QWidget):
    """文件管理面板 - 支持拖拽导入"""

    files_changed = pyqtSignal(list)
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files = []
        self._setup_ui()
        self.setAcceptDrops(True)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # 标题栏
        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("字幕 / 视频文件")
        title.setObjectName("section_title")
        header.addWidget(title)
        header.addStretch()

        self._count_label = QLabel("0 个文件")
        self._count_label.setObjectName("caption_label")
        header.addWidget(self._count_label)

        layout.addLayout(header)

        # 文件列表
        self._list = QListWidget()
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.setMinimumHeight(200)
        layout.addWidget(self._list, 1)

        # 按钮栏
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._btn_add = QPushButton("添加文件")
        self._btn_add.setObjectName("primary")
        self._btn_add.clicked.connect(self._add_files)
        btn_layout.addWidget(self._btn_add)

        self._btn_add_dir = QPushButton("添加文件夹")
        self._btn_add_dir.setObjectName("secondary")
        self._btn_add_dir.clicked.connect(self._add_folder)
        btn_layout.addWidget(self._btn_add_dir)

        btn_layout.addStretch()

        self._btn_remove = QPushButton("移除选中")
        self._btn_remove.setObjectName("danger")
        self._btn_remove.clicked.connect(self._remove_selected)
        btn_layout.addWidget(self._btn_remove)

        self._btn_clear = QPushButton("清空")
        self._btn_clear.setObjectName("secondary")
        self._btn_clear.clicked.connect(self._clear_all)
        btn_layout.addWidget(self._btn_clear)

        layout.addLayout(btn_layout)

        # 拖拽提示
        self._drop_hint = QLabel("拖拽字幕或视频文件到此处")
        self._drop_hint.setObjectName("drop_hint")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._drop_hint)

    @property
    def files(self) -> list[str]:
        return self._files.copy()

    def _add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择字幕或视频文件", "",
            "所有支持文件 (*.srt *.ass *.ssa *.mp4 *.mkv *.avi *.webm *.ts);;字幕文件 (*.srt *.ass *.ssa);;视频文件 (*.mp4 *.mkv *.avi *.webm *.ts);;所有文件 (*.*)"
        )
        if files:
            self._add_file_list(files)

    def _add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            exts = {".srt", ".ass", ".ssa", ".mp4", ".mkv", ".avi", ".webm", ".ts"}
            found = []
            for root, _, files in os.walk(folder):
                for f in files:
                    if Path(f).suffix.lower() in exts:
                        found.append(os.path.join(root, f))
            if found:
                self._add_file_list(found)

    def _add_file_list(self, files: list[str]):
        existing = set(self._files)
        for f in files:
            if f not in existing and os.path.isfile(f):
                self._files.append(f)
                existing.add(f)
                self._list.addItem(os.path.basename(f))
        self._update_ui()

    def _remove_selected(self):
        # 支持多选删除：从大到小移除，避免下标错位
        rows = sorted(set(idx.row() for idx in self._list.selectedIndexes()),
                      reverse=True)
        if not rows:
            # 兜底：若用户未多选但选中了单项，按 currentRow 删除
            cur = self._list.currentRow()
            if cur >= 0:
                rows = [cur]
        for row in rows:
            if 0 <= row < len(self._files):
                self._files.pop(row)
                self._list.takeItem(row)
        if rows:
            self._update_ui()

    def _clear_all(self):
        self._files.clear()
        self._list.clear()
        self._update_ui()

    def _update_ui(self):
        count = len(self._files)
        self._count_label.setText(f"{count} 个文件")
        self._drop_hint.setVisible(count == 0)
        self.files_changed.emit(self._files)

    def _on_selection_changed(self):
        rows = sorted(set(idx.row() for idx in self._list.selectedIndexes()))
        if rows and 0 <= rows[0] < len(self._files):
            self.file_selected.emit(self._files[rows[0]])

    @staticmethod
    def is_video_file(path: str) -> bool:
        return Path(path).suffix.lower() in {".mp4", ".mkv", ".avi", ".webm", ".mov", ".ts"}

    @staticmethod
    def is_subtitle_file(path: str) -> bool:
        return Path(path).suffix.lower() in {".srt", ".ass", ".ssa"}

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                ext = Path(path).suffix.lower()
                if ext in (".srt", ".ass", ".ssa", ".mp4", ".mkv", ".avi", ".webm", ".ts"):
                    files.append(path)
            elif os.path.isdir(path):
                for root, _, fnames in os.walk(path):
                    for f in fnames:
                        if Path(f).suffix.lower() in (".srt", ".ass", ".ssa", ".mp4", ".mkv", ".avi", ".webm", ".ts"):
                            files.append(os.path.join(root, f))
        if files:
            self._add_file_list(files)
