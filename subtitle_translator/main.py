"""字幕翻译工具 - 主入口"""

import sys
import os
import re


class _StderrFilter:
    """过滤已知的 Qt 字体大小警告"""
    def __init__(self, original):
        self._original = original
        self._pattern = re.compile(r"QFont::setPointSize.*")

    def write(self, msg):
        if not self._pattern.search(msg):
            self._original.write(msg)

    def flush(self):
        self._original.flush()


def main():
    # 抑制 Qt 字体大小警告
    sys.stderr = _StderrFilter(sys.stderr)

    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from PyQt6.QtCore import Qt
    from .gui.main_window import MainWindow

    app = QApplication(sys.argv)

    # 设置默认字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 设置应用程序信息
    app.setApplicationName("Subtitle Translator")
    app.setOrganizationName("SubtitleTranslator")

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
