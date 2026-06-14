"""UI 样式定义 - Apple HIG 设计令牌 + 全局 QSS

所有颜色、字号、字重、圆角、高度统一以模块级常量定义，
QSS 与 Python 内联样式引用同一套令牌，避免裸值散落导致不一致。
"""

# ── 字体栈 ──
APPLE_FONT = ('"SF Pro Text", -apple-system, "PingFang SC", "PingFang TC", '
              '"Microsoft YaHei", "Helvetica Neue", "Arial", sans-serif')
MONO_FONT = '"SF Mono", "Menlo", "Consolas", "Courier New", monospace'

# ── 颜色令牌（Apple HIG 系统色）──
TEXT_PRIMARY = "#1D1D1F"
TEXT_SECONDARY = "#8E8E93"
TEXT_TERTIARY = "#AEAEB2"

BG_GROUPED = "#F2F2F7"      # 分组背景
BG_CARD = "#FFFFFF"          # 卡片/输入背景
SEPARATOR = "#E5E5EA"        # 细分隔线
SEPARATOR_STRONG = "#D1D1D6" # 输入框边框

ACCENT = "#007AFF"           # 系统蓝
ACCENT_HOVER = "#0062CC"
ACCENT_PRESSED = "#004A99"
ACCENT_TINT = "#EBF3FF"      # 选中淡蓝底

SUCCESS = "#34C759"
SUCCESS_HOVER = "#2EB850"
SUCCESS_PRESSED = "#28A745"

DANGER = "#FF3B30"
DANGER_HOVER = "#E0342B"
DANGER_PRESSED = "#C73028"

NEUTRAL = "#E5E5EA"          # 次级按钮底
NEUTRAL_HOVER = "#D1D1D6"
NEUTRAL_PRESSED = "#C7C7CC"

# ── 字号令牌（px）──
FS_CAPTION = "11px"
FS_BODY = "13px"
FS_HEADLINE = "15px"
FS_TITLE = "17px"

# ── 字重令牌 ──
FW_REGULAR = "400"
FW_MEDIUM = "500"
FW_SEMIBOLD = "600"
FW_BOLD = "700"

# ── 圆角令牌 ──
RADIUS_SM = "6px"
RADIUS_MD = "8px"
RADIUS_LG = "10px"

# ── 高度令牌（px，Python 端用 int）──
H_CONTROL = 30       # 输入框 / 下拉 / Spin
H_BUTTON = 32        # 普通按钮
H_BUTTON_LG = 36     # 主操作按钮


GLOBAL_STYLE = """
/* ── 基础 ── */
QMainWindow {
    background-color: %(BG_GROUPED)s;
}
QWidget {
    font-family: %(APPLE_FONT)s;
    font-size: %(FS_BODY)s;
    color: %(TEXT_PRIMARY)s;
}
QLabel {
    background: transparent;
}

/* ── 语义化标签（objectName 驱动）── */
QLabel#section_title {
    font-size: %(FS_HEADLINE)s;
    font-weight: %(FW_BOLD)s;
    color: %(TEXT_PRIMARY)s;
}
QLabel#caption_label {
    color: %(TEXT_SECONDARY)s;
    font-size: %(FS_CAPTION)s;
}
QLabel#hint {
    color: %(TEXT_SECONDARY)s;
    font-size: %(FS_CAPTION)s;
}
QLabel#status_text {
    color: %(TEXT_SECONDARY)s;
    font-size: %(FS_CAPTION)s;
}
QLabel#port_label {
    font-weight: %(FW_SEMIBOLD)s;
    font-size: %(FS_BODY)s;
}
QLabel#drop_hint {
    color: %(TEXT_SECONDARY)s;
    font-size: %(FS_BODY)s;
    padding: 24px;
    border: 2px dashed %(SEPARATOR_STRONG)s;
    border-radius: %(RADIUS_LG)s;
    background: rgba(0, 0, 0, 0.02);
}

/* ── 按钮 ── */
QPushButton {
    border: none;
    border-radius: %(RADIUS_SM)s;
    padding: 6px 14px;
    font-weight: %(FW_SEMIBOLD)s;
    font-size: %(FS_BODY)s;
    min-height: 22px;
    min-width: 40px;
}
QPushButton:disabled {
    background-color: %(NEUTRAL)s;
    color: %(TEXT_TERTIARY)s;
}
QPushButton#primary {
    background-color: %(ACCENT)s;
    color: white;
}
QPushButton#primary:hover {
    background-color: %(ACCENT_HOVER)s;
}
QPushButton#primary:pressed {
    background-color: %(ACCENT_PRESSED)s;
}
QPushButton#secondary {
    background-color: %(NEUTRAL)s;
    color: %(TEXT_PRIMARY)s;
}
QPushButton#secondary:hover {
    background-color: %(NEUTRAL_HOVER)s;
}
QPushButton#secondary:pressed {
    background-color: %(NEUTRAL_PRESSED)s;
}
QPushButton#danger {
    background-color: %(DANGER)s;
    color: white;
}
QPushButton#danger:hover {
    background-color: %(DANGER_HOVER)s;
}
QPushButton#danger:pressed {
    background-color: %(DANGER_PRESSED)s;
}
QPushButton#success {
    background-color: %(SUCCESS)s;
    color: white;
}
QPushButton#success:hover {
    background-color: %(SUCCESS_HOVER)s;
}
QPushButton#success:pressed {
    background-color: %(SUCCESS_PRESSED)s;
}

/* ── 输入框 ── */
QLineEdit, QSpinBox {
    border: 1px solid %(SEPARATOR_STRONG)s;
    border-radius: %(RADIUS_SM)s;
    padding: 6px 10px;
    background: %(BG_CARD)s;
    selection-background-color: %(ACCENT)s;
    min-height: 22px;
    font-size: %(FS_BODY)s;
}
QLineEdit:focus, QSpinBox:focus {
    border-color: %(ACCENT)s;
    border-width: 1.5px;
}
QComboBox {
    border: 1px solid %(SEPARATOR_STRONG)s;
    border-radius: %(RADIUS_SM)s;
    padding: 6px 10px;
    background: %(BG_CARD)s;
    min-width: 120px;
    min-height: 22px;
    font-size: %(FS_BODY)s;
}
QComboBox:focus {
    border-color: %(ACCENT)s;
    border-width: 1.5px;
}
QComboBox QAbstractItemView {
    border: 1px solid %(SEPARATOR_STRONG)s;
    border-radius: %(RADIUS_MD)s;
    background: %(BG_CARD)s;
    selection-background-color: %(ACCENT_TINT)s;
    selection-color: %(ACCENT)s;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    /* 弹出列表项的间距与高度，保证与整体行高一致 */
    min-height: 24px;
    padding: 4px 8px;
}
QComboBox::drop-down {
    border: none;
    border-left: 1px solid %(SEPARATOR)s;
    width: 26px;
}
QComboBox::down-arrow {
    /* 纯 QSS 三角形箭头（不依赖任何图片，跨平台可靠）：
       用一个 0 宽高的元素，仅靠上边框形成倒三角 */
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid %(TEXT_SECONDARY)s;
    width: 0;
    height: 0;
}
QComboBox::down-arrow:disabled {
    border-top-color: %(TEXT_TERTIARY)s;
}

/* ── 数字输入框：隐藏默认的上下箭头按钮（Apple 风格数字框无 spinner）── */
QSpinBox::up-button, QSpinBox::down-button {
    subcontrol-origin: margin;
    width: 0;
    height: 0;
    border: none;
    background: none;
}
QSpinBox::up-arrow, QSpinBox::down-arrow {
    image: none;
    width: 0;
    height: 0;
}

/* ── 进度条 ── */
QProgressBar {
    border: none;
    border-radius: 3px;
    background-color: %(NEUTRAL)s;
    text-align: center;
    height: 6px;
    max-height: 6px;
}
QProgressBar::chunk {
    background-color: %(ACCENT)s;
    border-radius: 3px;
}

/* ── 列表 ── */
QListWidget {
    border: 1px solid %(SEPARATOR_STRONG)s;
    border-radius: %(RADIUS_MD)s;
    background: %(BG_CARD)s;
    outline: none;
    padding: 4px;
    font-size: %(FS_BODY)s;
}
QListWidget::item {
    padding: 7px 10px;
    border-radius: %(RADIUS_SM)s;
    margin: 1px 3px;
    min-height: 20px;
}
QListWidget::item:selected {
    background-color: %(ACCENT_TINT)s;
    color: %(ACCENT)s;
}
QListWidget::item:hover:!selected {
    background-color: %(BG_GROUPED)s;
}

/* ── 文本编辑 ── */
QTextEdit {
    border: 1px solid %(SEPARATOR_STRONG)s;
    border-radius: %(RADIUS_MD)s;
    background: %(BG_CARD)s;
    padding: 8px;
    selection-background-color: %(ACCENT)s;
    font-family: %(MONO_FONT)s;
    font-size: 12px;
}
QTextEdit:focus {
    border-color: %(ACCENT)s;
}

/* ── 分割器 ── */
QSplitter::handle {
    background-color: %(SEPARATOR_STRONG)s;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}

/* ── 状态栏 ── */
QStatusBar {
    background-color: %(BG_GROUPED)s;
    border-top: 1px solid %(SEPARATOR)s;
    font-size: 12px;
    color: %(TEXT_SECONDARY)s;
}

/* ── 分组框 ── */
QGroupBox {
    border: none;
    border-bottom: 1px solid %(SEPARATOR)s;
    border-radius: 0;
    margin-top: 16px;
    padding-top: 20px;
    padding-bottom: 12px;
    font-size: %(FS_BODY)s;
    font-weight: %(FW_BOLD)s;
    color: %(TEXT_PRIMARY)s;
    background: transparent;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 0;
    padding: 0;
    background: transparent;
}

/* ── 复选框 ── */
QCheckBox {
    spacing: 8px;
    font-size: %(FS_BODY)s;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1.5px solid %(SEPARATOR_STRONG)s;
    background: %(BG_CARD)s;
}
QCheckBox::indicator:hover {
    border-color: %(TEXT_SECONDARY)s;
}
QCheckBox::indicator:checked {
    background-color: %(ACCENT)s;
    border-color: %(ACCENT)s;
}

/* ── 滚动区域 ── */
QScrollArea {
    border: none;
    background: transparent;
}

/* ── 滚动条 ── */
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
""" % {
    "APPLE_FONT": APPLE_FONT,
    "MONO_FONT": MONO_FONT,
    "BG_GROUPED": BG_GROUPED,
    "BG_CARD": BG_CARD,
    "TEXT_PRIMARY": TEXT_PRIMARY,
    "TEXT_SECONDARY": TEXT_SECONDARY,
    "TEXT_TERTIARY": TEXT_TERTIARY,
    "SEPARATOR": SEPARATOR,
    "SEPARATOR_STRONG": SEPARATOR_STRONG,
    "ACCENT": ACCENT,
    "ACCENT_HOVER": ACCENT_HOVER,
    "ACCENT_PRESSED": ACCENT_PRESSED,
    "ACCENT_TINT": ACCENT_TINT,
    "SUCCESS": SUCCESS,
    "SUCCESS_HOVER": SUCCESS_HOVER,
    "SUCCESS_PRESSED": SUCCESS_PRESSED,
    "DANGER": DANGER,
    "DANGER_HOVER": DANGER_HOVER,
    "DANGER_PRESSED": DANGER_PRESSED,
    "NEUTRAL": NEUTRAL,
    "NEUTRAL_HOVER": NEUTRAL_HOVER,
    "NEUTRAL_PRESSED": NEUTRAL_PRESSED,
    "FS_CAPTION": FS_CAPTION,
    "FS_BODY": FS_BODY,
    "FS_HEADLINE": FS_HEADLINE,
    "FS_TITLE": FS_TITLE,
    "FW_REGULAR": FW_REGULAR,
    "FW_MEDIUM": FW_MEDIUM,
    "FW_SEMIBOLD": FW_SEMIBOLD,
    "FW_BOLD": FW_BOLD,
    "RADIUS_SM": RADIUS_SM,
    "RADIUS_MD": RADIUS_MD,
    "RADIUS_LG": RADIUS_LG,
}
