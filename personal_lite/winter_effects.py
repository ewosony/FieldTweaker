"""Lightweight, offline festive decorations for FIELD 1.2.1.

Only paints over existing widgets; it never handles mouse input and never changes
Windows/system settings. A timer runs only while the winter theme is visible.
"""
from __future__ import annotations

import math
import random

from PySide6.QtCore import QEvent, QPointF, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class WinterOverlay(QWidget):
    """Transparent, mouse-click-through layer with snow and string lights."""

    SNOW_COUNT = 58
    COLORS = ('#ffcf78', '#fff5df', '#70dec6', '#ff767d', '#9ad4ff')

    def __init__(self, parent: QWidget, active: bool = True):
        super().__init__(parent)
        self.setObjectName('fieldWinterOverlay')
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._rng = random.Random(120121)
        self._flakes = [self._flake(new=True) for _ in range(self.SNOW_COUNT)]
        self._frame = 0
        self._active = bool(active)
        self._timer = QTimer(self)
        self._timer.setInterval(55)  # ~18 fps, low overhead
        self._timer.timeout.connect(self._animate)
        parent.installEventFilter(self)
        self.setGeometry(parent.rect())
        self.setVisible(self._active)
        if self._active:
            self._timer.start()
        self.raise_()

    def _flake(self, new: bool = False):
        return {
            'x': self._rng.random(),
            'y': self._rng.random() if new else -self._rng.uniform(0.0, 0.12),
            'radius': self._rng.uniform(1.0, 2.7),
            'speed': self._rng.uniform(0.00065, 0.0021),
            'drift': self._rng.uniform(0.00012, 0.00042),
            'phase': self._rng.uniform(0, math.tau),
            'alpha': self._rng.randint(95, 185),
        }

    def set_winter(self, active: bool):
        self._active = bool(active)
        self.setVisible(self._active)
        if self._active:
            self.setGeometry(self.parentWidget().rect())
            self.raise_()
            if not self._timer.isActive():
                self._timer.start()
            self.update()
        else:
            self._timer.stop()

    def eventFilter(self, watched, event):
        if watched is self.parentWidget():
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
                self.setGeometry(watched.rect())
                if self._active:
                    self.raise_()
            elif event.type() == QEvent.Type.Hide:
                self._timer.stop()
        return super().eventFilter(watched, event)

    def showEvent(self, event):
        super().showEvent(event)
        if self._active and not self._timer.isActive():
            self._timer.start()

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _animate(self):
        if not self._active or not self.isVisible():
            return
        self._frame += 1
        for f in self._flakes:
            f['y'] += f['speed']
            f['x'] += math.sin(self._frame * 0.025 + f['phase']) * f['drift']
            if f['y'] > 1.025:
                f.update(self._flake())
            if f['x'] > 1.03:
                f['x'] = -0.03
            elif f['x'] < -0.03:
                f['x'] = 1.03
        self.update()

    def paintEvent(self, event):
        if not self._active:
            return
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self._paint_garlands(painter, w)
        painter.setPen(Qt.PenStyle.NoPen)
        for f in self._flakes:
            x, y = f['x'] * w, f['y'] * h
            # Keep the working area's text legible: snow is deliberately subtle.
            painter.setBrush(QColor(243, 251, 255, f['alpha']))
            painter.drawEllipse(QPointF(x, y), f['radius'], f['radius'])
        painter.end()

    def _paint_garlands(self, painter: QPainter, width: int):
        # Slack cable, on the upper edge of the shell. Bulbs pulse gently.
        if width < 130:
            return
        segments = max(8, int(width / 56))
        path = QPainterPath(QPointF(0, 8))
        for i in range(segments):
            start = i * width / segments
            end = (i + 1) * width / segments
            mid = (start + end) / 2
            path.quadTo(QPointF(mid, 28), QPointF(end, 8))
        painter.setPen(QPen(QColor('#365c57'), 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        for i in range(segments):
            x = (i + 0.5) * width / segments
            y = 18.5
            color = QColor(self.COLORS[i % len(self.COLORS)])
            pulse = (math.sin(self._frame * 0.06 + i * 1.8) + 1) / 2
            halo = QColor(color)
            halo.setAlpha(int(17 + pulse * 22))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(halo)
            painter.drawEllipse(QPointF(x, y + 4), 9.5, 10.5)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(x, y + 4), 3.8, 5.4)
            painter.setBrush(QColor('#48665d'))
            painter.drawRoundedRect(int(x - 2), int(y - 3), 4, 5, 1, 1)
