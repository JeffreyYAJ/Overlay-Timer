"""
sage       : python3 Timer.py [--minutes 10] [--seconds 0]
"""

import sys
import argparse
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QDialog, QFrame
)
from PyQt6.QtCore import (
    Qt, QTimer, QPoint, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QRect
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontDatabase,
    QLinearGradient, QPen, QBrush
)

class SetupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⏱ Timer Overlay — Configuration")
        self.setFixedSize(320, 200)
        self.setStyleSheet("""
            QDialog {
                background: #0f0f14;
                color: #e8e8f0;
                border-radius: 12px;
            }
            QLabel {
                color: #a0a0c0;
                font-size: 13px;
                font-family: 'Courier New', monospace;
            }
            QLabel#title {
                color: #e0e0ff;
                font-size: 16px;
                font-weight: bold;
            }
            QSpinBox {
                background: #1a1a2e;
                color: #e0e0ff;
                border: 1px solid #3a3a5e;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 20px;
                font-family: 'Courier New', monospace;
                min-width: 60px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background: #2a2a4e;
                border: none;
                width: 20px;
            }
            QPushButton {
                background: #4040a0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 28px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5050c0; }
            QPushButton:pressed { background: #303080; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("⏱ Timer Overlay")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Sélecteurs min / sec
        time_layout = QHBoxLayout()
        time_layout.setSpacing(12)

        lbl_min = QLabel("min")
        self.spin_min = QSpinBox()
        self.spin_min.setRange(0, 99)
        self.spin_min.setValue(10)

        lbl_sep = QLabel(":")
        lbl_sep.setStyleSheet("font-size: 22px; color: #6060a0;")

        lbl_sec = QLabel("sec")
        self.spin_sec = QSpinBox()
        self.spin_sec.setRange(0, 59)
        self.spin_sec.setValue(0)

        for w in (self.spin_min, lbl_sep, self.spin_sec):
            time_layout.addWidget(w, alignment=Qt.AlignmentFlag.AlignVCenter)

        label_row = QHBoxLayout()
        label_row.addWidget(lbl_min)
        label_row.addSpacing(52)
        label_row.addWidget(lbl_sec)

        layout.addLayout(time_layout)
        layout.addLayout(label_row)

        btn = QPushButton("▶  Démarrer")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def get_seconds(self):
        return self.spin_min.value() * 60 + self.spin_sec.value()


# ──────────────────────────────────────────────
#  Overlay principal : transparent + always-on-top
# ──────────────────────────────────────────────
class TimerOverlay(QWidget):
    def __init__(self, total_seconds: int):
        super().__init__()

        self.total_seconds = total_seconds
        self.remaining = total_seconds
        self.running = True
        self._drag_pos = QPoint()
        self._pulse = 0.0          # animation urgence
        self._pulse_dir = 1

        # ── Flags fenêtre ───────────────────────────────────────────────
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint          # sans bordure
            | Qt.WindowType.WindowStaysOnTopHint       # toujours devant
            | Qt.WindowType.Tool                       # pas dans la taskbar
            | Qt.WindowType.X11BypassWindowManagerHint # bypass WM = overlay pur
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._click_through = False

        self.setFixedSize(220, 100)

        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 240, 40)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(33)

        self.show()

    def _tick(self):
        if not self.running:
            return
        if self.remaining > 0:
            self.remaining -= 1
            self.update()
        else:
            self._timer.stop()
            self._notify()
            self.update()

    def _animate(self):
        """Pulse rouge quand < 60s restantes."""
        if self.remaining < 60 and self.running:
            self._pulse += 0.05 * self._pulse_dir
            if self._pulse >= 1.0:
                self._pulse_dir = -1
            elif self._pulse <= 0.0:
                self._pulse_dir = 1
            self.update()

    def _notify(self):
        try:
            import subprocess
            subprocess.Popen([
                "notify-send",
                "--urgency=critical",
                "--icon=alarm-clock",
                "⏱ Timer Overlay",
                "Le temps est écoulé !"
            ])
        except Exception:
            pass  

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        elapsed_ratio = 1.0 - (self.remaining / max(self.total_seconds, 1))
        done = self.remaining == 0

        if done:
            bg = QColor(180, 30, 30, 200)
        elif self.remaining < 60:
            r = int(20 + self._pulse * 60)
            bg = QColor(r, 20, 60, 210)
        else:
            bg = QColor(15, 15, 30, 200)

        p.setBrush(QBrush(bg))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, w, h, 16, 16)

        bar_h = 5
        bar_y = h - bar_h - 6
        bar_w = int((w - 20) * (1.0 - elapsed_ratio))

        p.setBrush(QColor(40, 40, 70, 180))
        p.drawRoundedRect(10, bar_y, w - 20, bar_h, 2, 2)

        if bar_w > 0:
            if done:
                bar_color = QColor(255, 80, 80)
            elif self.remaining < 60:
                r = int(200 + self._pulse * 55)
                bar_color = QColor(r, 60, 60)
            else:
                bar_color = QColor(100, 140, 255)
            p.setBrush(QBrush(bar_color))
            p.drawRoundedRect(10, bar_y, bar_w, bar_h, 2, 2)

        mins = self.remaining // 60
        secs = self.remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"

        font = QFont("Courier New", 28, QFont.Weight.Bold)
        p.setFont(font)

        if done:
            text_color = QColor(255, 200, 200)
            time_str = "00:00 ✓"
            font.setPointSize(20)
            p.setFont(font)
        elif self.remaining < 60:
            intensity = int(200 + self._pulse * 55)
            text_color = QColor(intensity, 80, 80)
        else:
            text_color = QColor(220, 220, 255)

        p.setPen(text_color)
        p.drawText(
            QRect(0, 8, w, 56),
            Qt.AlignmentFlag.AlignCenter,
            time_str
        )

        p.setFont(QFont("Monospace", 7))
        hint = "⏸" if not self.running else ""
        if self._click_through:
            hint += " [clic-through]"
        p.setPen(QColor(100, 100, 140))
        p.drawText(QRect(0, bar_y - 14, w, 12), Qt.AlignmentFlag.AlignCenter, hint)

        p.end()

    def keyPressEvent(self, e):
        key = e.key()
        if key == Qt.Key.Key_Space:
            self.running = not self.running
            self.update()
        elif key == Qt.Key.Key_T:
            self._toggle_click_through()
        elif key in (Qt.Key.Key_Q, Qt.Key.Key_Escape):
            self.close()

    def _toggle_click_through(self):
        """Bascule le mode transparent aux clics."""
        self._click_through = not self._click_through
        if self._click_through:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        else:
            self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.update()

    # ── Drag pour déplacer l'overlay ────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseDoubleClickEvent(self, _):
        """Double-clic → pause/reprise."""
        self.running = not self.running
        self.update()


def main():
    parser = argparse.ArgumentParser(description="Timer Overlay Linux")
    parser.add_argument("--minutes", type=int, default=-1)
    parser.add_argument("--seconds", type=int, default=0)
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Timer Overlay")

    if args.minutes >= 0:
        total = args.minutes * 60 + args.seconds
    else:
        dialog = SetupDialog()
        if dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)
        total = dialog.get_seconds()

    if total <= 0:
        total = 600  # fallback 10 min

    overlay = TimerOverlay(total)
    overlay.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
