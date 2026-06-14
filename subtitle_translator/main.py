"""字幕翻译工具 - 主入口"""

import sys


def main():
    from PyQt6.QtWidgets import QApplication
    from .gui.main_window import MainWindow

    app = QApplication(sys.argv)

    # 字体完全由全局 QSS（styles.py）统一控制：
    #   QWidget { font-family: APPLE_FONT; font-size: 13px; }
    # 不再调用 app.setFont()，避免与 QSS 字体栈冲突。

    # 设置应用程序信息
    app.setApplicationName("Subtitle Translator")
    app.setOrganizationName("SubtitleTranslator")

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
