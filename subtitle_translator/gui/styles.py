"""UI样式定义"""

# 颜色主题 (Apple HIG)
COLORS = {
    "bg": "#F5F5F7",
    "sidebar_bg": "#E8E8ED",
    "card": "#FFFFFF",
    "blue": "#007AFF",
    "blue_hover": "#0058CC",
    "blue_light": "#EBF3FF",
    "red": "#FF3B30",
    "red_light": "#FFF0EF",
    "green": "#34C759",
    "green_light": "#EDFAF2",
    "orange": "#FF9500",
    "separator": "#C6C6C8",
    "text": "#1D1D1F",
    "text2": "#3C3C43",
    "text3": "#8E8E93",
    "g5": "#E5E5EA",
}

APPLE_FONT = '"SF Pro Text", "SF Pro Display", "PingFang SC", "PingFang TC", "Helvetica Neue", "Helvetica", "Arial", sans-serif'
MONO_FONT = '"SF Mono", "Menlo", "Monaco", "Consolas", "Courier New", monospace'

# 全局样式表
GLOBAL_STYLE = """
QMainWindow {
    background-color: #F5F5F7;
}
QWidget {
    font-family: """ + APPLE_FONT + """;
    font-size: 13px;
    color: #1D1D1F;
}
QLabel {
    background: transparent;
}
QPushButton {
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}
QPushButton:disabled {
    opacity: 0.4;
}
QPushButton#primary {
    background-color: #007AFF;
    color: white;
}
QPushButton#primary:hover {
    background-color: #0058CC;
}
QPushButton#primary:pressed {
    background-color: #0040A0;
}
QPushButton#secondary {
    background-color: rgba(0, 0, 0, 0.06);
    color: #1D1D1F;
    border: 1px solid #C6C6C8;
    border-radius: 6px;
}
QPushButton#secondary:hover {
    background-color: rgba(0, 0, 0, 0.08);
}
QPushButton#secondary:pressed {
    background-color: rgba(0, 0, 0, 0.12);
}
QPushButton#danger {
    background-color: #FFF0EF;
    color: #FF3B30;
}
QPushButton#danger:hover {
    background-color: #FFD9D7;
}
QPushButton#danger:pressed {
    background-color: #FFC2BF;
}
QPushButton#success {
    background-color: #34C759;
    color: white;
}
QPushButton#success:hover {
    background-color: #2DA44E;
}
QPushButton#success:pressed {
    background-color: #248A3D;
}
QLineEdit {
    border: 1px solid #C6C6C8;
    border-radius: 6px;
    padding: 6px 10px;
    background: white;
    selection-background-color: #007AFF;
    min-height: 20px;
}
QLineEdit:focus {
    border-color: #007AFF;
    border-width: 1.5px;
}
QComboBox {
    border: 1px solid #C6C6C8;
    border-radius: 6px;
    padding: 6px 10px;
    background: white;
    min-width: 120px;
    min-height: 20px;
}
QComboBox:focus {
    border-color: #007AFF;
    border-width: 1.5px;
}
QComboBox QAbstractItemView {
    border: 1px solid #C6C6C8;
    border-radius: 8px;
    background: white;
    selection-background-color: #EBF3FF;
    selection-color: #007AFF;
    padding: 4px;
    outline: none;
}
QSpinBox, QDoubleSpinBox {
    border: 1px solid #C6C6C8;
    border-radius: 6px;
    padding: 6px 10px;
    background: white;
    min-height: 20px;
}
QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #007AFF;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #E5E5EA;
    text-align: center;
    height: 6px;
    max-height: 6px;
}
QProgressBar::chunk {
    background-color: #007AFF;
    border-radius: 4px;
}
QListWidget {
    border: 1px solid #C6C6C8;
    border-radius: 8px;
    background: white;
    outline: none;
    padding: 4px;
    font-size: 12px;
}
QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px 4px;
    min-height: 20px;
}
QListWidget::item:selected {
    background-color: #EBF3FF;
    color: #007AFF;
}
QListWidget::item:hover:!selected {
    background-color: #F5F5F7;
}
QTextEdit {
    border: 1px solid #C6C6C8;
    border-radius: 8px;
    background: white;
    padding: 8px;
    selection-background-color: #007AFF;
    font-family: """ + MONO_FONT + """;
    font-size: 12px;
}
QTextEdit:focus {
    border-color: #007AFF;
}
QSplitter::handle {
    background-color: #C6C6C8;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}
QStatusBar {
    background-color: #F5F5F7;
    border-top: 1px solid #C6C6C8;
    font-size: 12px;
    color: #8E8E93;
}
QGroupBox {
    border: 1px solid #C6C6C8;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 18px;
    font-weight: 600;
    font-size: 13px;
    background: white;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background: white;
}
QCheckBox {
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid #C6C6C8;
    background: white;
}
QCheckBox::indicator:hover {
    border-color: #8E8E93;
}
QCheckBox::indicator:checked {
    background-color: #007AFF;
    border-color: #007AFF;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(0, 0, 0, 0.15);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(0, 0, 0, 0.25);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
"""
