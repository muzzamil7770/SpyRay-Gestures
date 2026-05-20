import cv2
import numpy as np
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QImage, QColor, QPen, QFont
from PySide6.QtCore import Qt, QPoint

class CameraWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.is_recording = False
        self.recording_label = ""
        self.recorded_count = 0
        self.record_target = 100
        self.fps = 0.0
        
        # Set background
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)

    def update_frame(self, frame, fps, is_rec=False, rec_label="", rec_count=0, rec_target=100):
        """Called when a new frame is captured from the camera."""
        self.fps = fps
        self.is_recording = is_rec
        self.recording_label = rec_label
        self.recorded_count = rec_count
        self.record_target = rec_target
        
        # Convert BGR (OpenCV) to RGB
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        
        # Convert OpenCV frame to Qt QImage
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_BGR888)
        self.image = q_img.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.update()  # Request repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # If no image is captured yet, show fallback hologram scanner screen
        if self.image is None:
            painter.fillRect(self.rect(), QColor("#090C15"))
            
            # Draw futuristic scanning line animation
            pen = QPen(QColor("rgba(0, 240, 255, 0.4)"), 1)
            painter.setPen(pen)
            
            # draw crosshairs
            cx, cy = self.width() // 2, self.height() // 2
            painter.drawLine(cx - 30, cy, cx + 30, cy)
            painter.drawLine(cx, cy - 30, cx, cy + 30)
            
            painter.setPen(QColor("#00F0FF"))
            font = QFont("Consolas", 12, QFont.Bold)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, "INITIALIZING HOLOGRAM SENSORS...")
            return

        # Center the image inside the widget area
        x = (self.width() - self.image.width()) // 2
        y = (self.height() - self.image.height()) // 2
        painter.drawImage(QPoint(x, y), self.image)

        # Draw Futuristic Holographic HUD Overlay over the live stream
        font_hud = QFont("Consolas", 10, QFont.Bold)
        painter.setFont(font_hud)

        # 1. Active Indicator in top-left
        painter.setPen(QColor("#00F0FF"))
        painter.drawText(x + 15, y + 25, "SYS_STATUS: ACTIVE")
        
        # 2. FPS Indicator in top-right
        fps_text = f"INF_FPS: {self.fps:.1f}"
        painter.setPen(QColor("#FF007F"))
        painter.drawText(self.image.width() + x - 110, y + 25, fps_text)
        
        # 3. Hologram frame corners overlay
        pen_hud = QPen(QColor("rgba(0, 240, 255, 0.7)"), 2)
        painter.setPen(pen_hud)
        w_img, h_img = self.image.width(), self.image.height()
        gap = 15
        
        # Top-Left HUD Bracket
        painter.drawLine(x + gap, y + gap, x + gap + 20, y + gap)
        painter.drawLine(x + gap, y + gap, x + gap, y + gap + 20)
        # Top-Right HUD Bracket
        painter.drawLine(x + w_img - gap, y + gap, x + w_img - gap - 20, y + gap)
        painter.drawLine(x + w_img - gap, y + gap, x + w_img - gap, y + gap + 20)
        # Bottom-Left HUD Bracket
        painter.drawLine(x + gap, y + h_img - gap, x + gap + 20, y + h_img - gap)
        painter.drawLine(x + gap, y + h_img - gap, x + gap, y + h_img - gap - 20)
        # Bottom-Right HUD Bracket
        painter.drawLine(x + w_img - gap, y + h_img - gap, x + w_img - gap - 20, y + h_img - gap)
        painter.drawLine(x + w_img - gap, y + h_img - gap, x + w_img - gap, y + h_img - gap - 20)

        # 4. Recording Overlay
        if self.is_recording:
            # Pulsing red circle indicator
            from time import time
            pulse = int((time() * 2) % 2)
            
            if pulse == 0:
                painter.setBrush(QColor("#FF007F"))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(x + 15, y + 45, 10, 10)
                
            painter.setPen(QColor("#FF007F"))
            painter.drawText(x + 35, y + 55, f"REC: {self.recording_label} ({self.recorded_count}/{self.record_target})")
