"""Apple 风格图标 - 基于 SF Symbols 设计语言"""

from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QPainterPath
from PyQt6.QtCore import Qt, QRect, QRectF
from PyQt6.QtWidgets import QApplication


def _create_icon(draw_func, size=18, color="#1D1D1F"):
    """创建图标的通用方法"""
    pixmap = QPixmap(size, size)
    screen = QApplication.primaryScreen()
    pixmap.setDevicePixelRatio(screen.devicePixelRatio() if screen else 2.0)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(QColor(color), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # 在逻辑坐标中绘制（考虑 devicePixelRatio）
    logical_size = size
    draw_func(painter, logical_size, color)

    painter.end()
    icon = QIcon(pixmap)
    icon.addPixmap(pixmap, QIcon.Mode.Normal, QIcon.State.Off)
    return icon


# ── 文件操作图标 ──

def add_file_icon(color="#1D1D1F"):
    """添加文件 (+ 文档)"""
    def draw(p, s, c):
        m = s * 0.18
        p.setPen(QPen(QColor(c), 1.6))
        # 文档轮廓
        path = QPainterPath()
        x1, y1 = m, m
        w, h = s - 2*m, s - 2*m
        indent = w * 0.25
        path.moveTo(x1 + indent, y1)
        path.lineTo(x1 + w, y1)
        path.lineTo(x1 + w, y1 + h)
        path.lineTo(x1, y1 + h)
        path.lineTo(x1, y1 + indent)
        path.closeSubpath()
        p.drawPath(path)
        # 加号
        cx, cy = x1 + w * 0.48, y1 + h * 0.52
        p.drawLine(int(cx - w*0.15), int(cy), int(cx + w*0.15), int(cy))
        p.drawLine(int(cx), int(cy - h*0.15), int(cx), int(cy + h*0.15))
    return _create_icon(draw, color=color)


def add_folder_icon(color="#1D1D1F"):
    """添加文件夹"""
    def draw(p, s, c):
        m = s * 0.15
        p.setPen(QPen(QColor(c), 1.6))
        # 文件夹
        path = QPainterPath()
        x, y = m, m + s*0.12
        w, h = s - 2*m, s - 2*m - s*0.12
        tab_w = w * 0.35
        path.moveTo(x, y + h)
        path.lineTo(x, y + h*0.22)
        path.lineTo(x + tab_w, y + h*0.22)
        path.lineTo(x + tab_w + w*0.08, y)
        path.lineTo(x + w, y)
        path.lineTo(x + w, y + h)
        path.closeSubpath()
        p.drawPath(path)
    return _create_icon(draw, color=color)


def remove_icon(color="#FF3B30"):
    """移除 (- 文档)"""
    def draw(p, s, c):
        m = s * 0.18
        p.setPen(QPen(QColor(c), 1.6))
        # 文档轮廓
        path = QPainterPath()
        x1, y1 = m, m
        w, h = s - 2*m, s - 2*m
        indent = w * 0.25
        path.moveTo(x1 + indent, y1)
        path.lineTo(x1 + w, y1)
        path.lineTo(x1 + w, y1 + h)
        path.lineTo(x1, y1 + h)
        path.lineTo(x1, y1 + indent)
        path.closeSubpath()
        p.drawPath(path)
        # 减号
        cx, cy = x1 + w * 0.48, y1 + h * 0.52
        p.drawLine(int(cx - w*0.15), int(cy), int(cx + w*0.15), int(cy))
    return _create_icon(draw, color=color)


def clear_icon(color="#8E8E93"):
    """清空 (垃圾桶)"""
    def draw(p, s, c):
        m = s * 0.22
        p.setPen(QPen(QColor(c), 1.5))
        x, y = m, m
        w, h = s - 2*m, s - 2*m
        lid_h = h * 0.18
        body_top = y + lid_h + h*0.04
        body_h = h - lid_h - h*0.04
        # 盖子
        p.drawLine(int(x + w*0.25), int(y), int(x + w*0.75), int(y))
        p.drawLine(int(x + w*0.35), int(y - h*0.08), int(x + w*0.65), int(y - h*0.08))
        p.drawLine(int(x + w*0.35), int(y - h*0.08), int(x + w*0.35), int(y))
        p.drawLine(int(x + w*0.65), int(y - h*0.08), int(x + w*0.65), int(y))
        # 桶身
        body_path = QPainterPath()
        body_path.moveTo(x + w*0.15, body_top)
        body_path.lineTo(x + w*0.2, y + h)
        body_path.lineTo(x + w*0.8, y + h)
        body_path.lineTo(x + w*0.85, body_top)
        body_path.closeSubpath()
        p.drawPath(body_path)
        # 竖线
        for i in range(3):
            lx = x + w * (0.38 + i * 0.12)
            p.drawLine(int(lx), int(body_top + body_h*0.2), int(lx), int(body_top + body_h*0.7))
    return _create_icon(draw, color=color)


# ── 服务器图标 ──

def test_icon(color="#007AFF"):
    """测试连接 (雷达/信号)"""
    def draw(p, s, c):
        cx, cy = s/2, s/2
        p.setPen(QPen(QColor(c), 1.5))
        # 三层弧线
        for i in range(1, 4):
            r = s * 0.15 * i
            p.drawArc(int(cx - r), int(cy - r), int(r*2), int(r*2), -45*16, -90*16)
        # 中心点
        p.setBrush(QBrush(QColor(c)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(int(cx - s*0.06), int(cy - s*0.06), int(s*0.12), int(s*0.12))
    return _create_icon(draw, color=color)


def refresh_icon(color="#1D1D1F"):
    """刷新 (环形箭头)"""
    def draw(p, s, c):
        cx, cy = s/2, s/2
        r = s * 0.3
        p.setPen(QPen(QColor(c), 1.6))
        # 弧线
        p.drawArc(int(cx-r), int(cy-r), int(r*2), int(r*2), 30*16, 280*16)
        # 箭头
        import math
        angle = math.radians(30 + 280)
        ax = cx + r * math.cos(angle)
        ay = cy - r * math.sin(angle)
        # 箭头两翼
        for da in [25, -25]:
            angle2 = math.radians(30 + 280 + da)
            bx = ax + s*0.12 * math.cos(angle2)
            by = ay - s*0.12 * math.sin(angle2)
            p.drawLine(int(ax), int(ay), int(bx), int(by))
    return _create_icon(draw, color=color)


# ── 操作图标 ──

def start_icon(color="#34C759"):
    """开始翻译 (播放三角)"""
    def draw(p, s, c):
        m = s * 0.2
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        path = QPainterPath()
        path.moveTo(m, m)
        path.lineTo(s - m, s/2)
        path.lineTo(m, s - m)
        path.closeSubpath()
        p.drawPath(path)
    return _create_icon(draw, color=color)


def extract_icon(color="#FF9500"):
    """提取字幕 (字幕框)"""
    def draw(p, s, c):
        m = s * 0.18
        p.setPen(QPen(QColor(c), 1.6))
        # 外框
        p.drawRoundedRect(int(m), int(m + s*0.08), int(s-2*m), int(s-2*m-s*0.08), s*0.08, s*0.08)
        # 字幕波浪线
        y1 = s * 0.42
        y2 = s * 0.58
        y3 = s * 0.72
        p.drawLine(int(m + s*0.12), int(y1), int(s - m - s*0.12), int(y1))
        p.drawLine(int(m + s*0.12), int(y2), int(s - m - s*0.25), int(y2))
        p.drawLine(int(m + s*0.12), int(y3), int(s - m - s*0.18), int(y3))
    return _create_icon(draw, color=color)


def stop_icon(color="#FF3B30"):
    """停止 (方块)"""
    def draw(p, s, c):
        m = s * 0.25
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(c)))
        p.drawRoundedRect(int(m), int(m), int(s-2*m), int(s-2*m), s*0.06, s*0.06)
    return _create_icon(draw, color=color)


def browse_icon(color="#8E8E93"):
    """浏览 (...)"""
    def draw(p, s, c):
        p.setPen(QPen(QColor(c), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        cx = s / 2
        for i in range(3):
            y = s * (0.35 + i * 0.15)
            p.drawPoint(int(cx), int(y))
    return _create_icon(draw, color=color)


def swap_icon(color="#007AFF"):
    """交换语言 (双向箭头)"""
    def draw(p, s, c):
        p.setPen(QPen(QColor(c), 1.5))
        m = s * 0.15
        y_top = s * 0.35
        y_bot = s * 0.65
        # 上箭头 →
        p.drawLine(int(m), int(y_top), int(s - m), int(y_top))
        p.drawLine(int(s - m - s*0.1), int(y_top - s*0.08), int(s - m), int(y_top))
        p.drawLine(int(s - m - s*0.1), int(y_top + s*0.08), int(s - m), int(y_top))
        # 下箭头 ←
        p.drawLine(int(m), int(y_bot), int(s - m), int(y_bot))
        p.drawLine(int(m + s*0.1), int(y_bot - s*0.08), int(m), int(y_bot))
        p.drawLine(int(m + s*0.1), int(y_bot + s*0.08), int(m), int(y_bot))
    return _create_icon(draw, color=color)


# ── 应用图标 ──

def app_icon():
    """应用图标 - 翻译气泡"""
    size = 256
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 背景渐变圆角矩形
    from PyQt6.QtGui import QLinearGradient
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor("#007AFF"))
    gradient.setColorAt(1, QColor("#5856D6"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(gradient))
    painter.drawRoundedRect(0, 0, size, size, size * 0.22, size * 0.22)

    # 文字气泡
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
    bubble = QPainterPath()
    bx, by, bw, bh = size*0.18, size*0.2, size*0.64, size*0.45
    bubble.addRoundedRect(bx, by, bw, bh, bw*0.15, bh*0.15)
    # 气泡尾巴
    tail = QPainterPath()
    tail.moveTo(bx + bw*0.25, by + bh)
    tail.lineTo(bx + bw*0.15, by + bh + size*0.12)
    tail.lineTo(bx + bw*0.45, by + bh)
    bubble = bubble.united(tail)
    painter.drawPath(bubble)

    # "译" 字
    painter.setPen(QPen(QColor("#007AFF"), 1))
    font = painter.font()
    font.setPixelSize(int(size * 0.22))
    font.setBold(True)
    painter.setFont(font)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    text_rect = QRectF(bx, by + size*0.02, bw, bh)
    painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, "译")

    # 小气泡
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(255, 255, 255, 180)))
    small = QPainterPath()
    sx, sy, sw, sh = size*0.52, size*0.62, size*0.32, size*0.22
    small.addRoundedRect(sx, sy, sw, sh, sw*0.2, sh*0.2)
    # 小尾巴
    st = QPainterPath()
    st.moveTo(sx + sw*0.6, sy + sh)
    st.lineTo(sx + sw*0.7, sy + sh + size*0.08)
    st.lineTo(sx + sw*0.85, sy + sh)
    small = small.united(st)
    painter.drawPath(small)

    # "A" 字
    painter.setPen(QPen(QColor("#5856D6"), 1))
    font2 = painter.font()
    font2.setPixelSize(int(size * 0.14))
    font2.setBold(True)
    painter.setFont(font2)
    small_rect = QRectF(sx, sy - size*0.01, sw, sh)
    painter.drawText(small_rect, Qt.AlignmentFlag.AlignCenter, "A")

    painter.end()

    icon = QIcon()
    icon.addPixmap(pixmap, QIcon.Mode.Normal, QIcon.State.Off)
    return icon
