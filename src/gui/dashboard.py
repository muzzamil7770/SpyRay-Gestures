import numpy as np
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QStackedWidget, QSlider, 
                             QComboBox, QCheckBox, QTextEdit, QProgressBar, QGridLayout, 
                             QSpacerItem, QSizePolicy, QGroupBox, QLineEdit, QTableWidget,
                             QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt, Slot, QTimer, QPointF
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush, QRadialGradient
from src.config import ConfigManager
from src.mouse_controller import WinMouseController
from src.hand_tracker import HandTrackerThread
from src.gui.camera_widget import CameraWidget
from src.gui.theme import Theme
from src.voice_assistant import VoiceAssistantThread
import time
import subprocess
import random


class JarvisOrbWidget(QWidget):
    """Futuristic glowing neon orb representing JARVIS / FRIDAY core."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(220, 220)
        self.angle = 0.0
        self.status = "IDLE"  # IDLE, LISTENING, PROCESSING, SPEAKING
        self.pulse = 1.0
        self.pulse_dir = 0.02
        
        # Timer for rotation and pulse animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(25)  # 40 FPS

    def set_status(self, status):
        self.status = status
        self.update()

    def animate(self):
        # Rotate notches
        self.angle += 1.5
        if self.angle >= 360:
            self.angle = 0
            
        # Pulse core
        self.pulse += self.pulse_dir
        if self.status == "LISTENING":
            if self.pulse > 1.12 or self.pulse < 0.90:
                self.pulse_dir = -self.pulse_dir
        elif self.status == "PROCESSING":
            if self.pulse > 1.18 or self.pulse < 0.85:
                self.pulse_dir = -self.pulse_dir * 1.5
        elif self.status == "SPEAKING":
            if self.pulse > 1.15 or self.pulse < 0.88:
                self.pulse_dir = -self.pulse_dir * 1.2
        else:
            if self.pulse > 1.05 or self.pulse < 0.95:
                self.pulse_dir = -self.pulse_dir * 0.5
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center = QPointF(width / 2.0, height / 2.0)
        radius = min(width, height) / 3.0 * self.pulse
        
        # Colors tailored to match the JARVIS status and cyberpunk theme
        if self.status == "LISTENING":
            orb_color = QColor(0, 255, 127)      # Neon Green
            ring_color = QColor(0, 255, 127, 80)
        elif self.status == "PROCESSING":
            orb_color = QColor(255, 0, 127)      # Neon Pink
            ring_color = QColor(255, 0, 127, 80)
        elif self.status == "SPEAKING":
            orb_color = QColor(0, 240, 255)      # Neon Cyan
            ring_color = QColor(0, 240, 255, 80)
        else:
            orb_color = QColor(100, 116, 139)    # Muted Gray-Slate
            ring_color = QColor(100, 116, 139, 45)
            
        # 1. Outer Radial Glow
        glow_grad = QRadialGradient(center, radius * 1.6)
        glow_grad.setColorAt(0.0, QColor(orb_color.red(), orb_color.green(), orb_color.blue(), 55))
        glow_grad.setColorAt(0.6, QColor(orb_color.red(), orb_color.green(), orb_color.blue(), 18))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 1.6, radius * 1.6)
        
        # 2. Concentric Rotating Arcs (Technical Interface HUD design)
        pen = QPen(ring_color, 3.5)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(center.x() - radius, center.y() - radius, radius * 2, radius * 2, int(self.angle * 16), int(110 * 16))
        painter.drawArc(center.x() - radius, center.y() - radius, radius * 2, radius * 2, int((self.angle + 180) * 16), int(110 * 16))
        
        # Draw counter-rotating outer thin circle
        painter.setPen(QPen(QColor(orb_color.red(), orb_color.green(), orb_color.blue(), 40), 1))
        painter.drawArc(center.x() - radius * 1.2, center.y() - radius * 1.2, radius * 2.4, radius * 2.4, int(-self.angle * 12), int(260 * 16))
        
        # 3. Solid Inner ring
        painter.setPen(QPen(orb_color, 1.2))
        painter.drawEllipse(center, radius * 0.75, radius * 0.75)
        
        # 4. Core Radial Spark Glow
        core_grad = QRadialGradient(center, radius * 0.45)
        core_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        core_grad.setColorAt(0.4, QColor(orb_color.red(), orb_color.green(), orb_color.blue(), 230))
        core_grad.setColorAt(1.0, QColor(orb_color.red(), orb_color.green(), orb_color.blue(), 0))
        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 0.45, radius * 0.45)


class DashboardWindow(QMainWindow):
    def __init__(self, config_manager: ConfigManager, mouse_controller: WinMouseController):
        super().__init__()
        self.config = config_manager
        self.mouse = mouse_controller
        self.tracker = None
        self.assistant = None
        
        self.setWindowTitle("SPyRaw Gestures Control Panel")
        self.resize(1150, 780)
        self.setStyleSheet(Theme.QSS)
        
        # Main central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Root layout
        self.root_layout = QHBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)
        
        # Navigation sidebar buttons
        self.sidebar_buttons = []
        
        # Build UI and Threads
        self.init_tracker_thread()
        self.init_voice_assistant()
        self.init_sidebar()
        self.init_main_content()

        # Initial page selection (Console Console)
        self.switch_page(0)
        
        # Append startup logs
        self.log("SPyRaw Gestures Engine v1.1 initialized.")
        self.log("Qt GUI loaded with holographic glassmorphism design system.")
        self.log("Voice Assistant module loaded. SAPI native TTS ready.")
        self.log("Click 'START ENGAGEMENT' or speak 'wake up' to activate tracking.")

    def init_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title header
        title_box = QFrame()
        title_box.setStyleSheet("background-color: #060812; border-bottom: 1px solid rgba(0, 240, 255, 0.1);")
        title_box_layout = QVBoxLayout(title_box)
        title_box_layout.setContentsMargins(20, 25, 20, 25)
        
        logo = QLabel("SPYRAW")
        logo.setObjectName("header_title")
        logo.setStyleSheet("font-size: 28px; font-weight: 900; letter-spacing: 3px;")
        
        sub_logo = QLabel("GESTURE SYSTEMS")
        sub_logo.setStyleSheet(f"color: {Theme.ACCENT_PINK}; font-size: 9px; font-weight: bold; letter-spacing: 2px;")
        
        title_box_layout.addWidget(logo)
        title_box_layout.addWidget(sub_logo)
        layout.addWidget(title_box)
        
        # Navigation buttons
        nav_items = [
            ("🎥 Tracking Console", 0),
            ("⚙️ Gesture Mapping", 1),
            ("🧠 AI Classifier Trainer", 2),
            ("⚡ System Tweaks", 3),
            ("🎙️ Voice Assistant", 4)
        ]
        
        layout.addSpacing(15)
        for label, index in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("sidebar_btn")
            btn.setProperty("page_index", index)
            btn.clicked.connect(self.on_sidebar_click)
            layout.addWidget(btn)
            self.sidebar_buttons.append(btn)
            
        layout.addStretch()
        
        # System status card at the bottom of sidebar
        status_card = QFrame()
        status_card.setStyleSheet("background-color: #060812; border-top: 1px solid rgba(0, 240, 255, 0.1);")
        sc_layout = QVBoxLayout(status_card)
        sc_layout.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_overall_status = QLabel("CORE ENGINE: IDLE")
        self.lbl_overall_status.setStyleSheet("color: #FF007F; font-size: 11px; font-weight: bold;")
        sc_layout.addWidget(self.lbl_overall_status)
        
        layout.addWidget(status_card)
        self.root_layout.addWidget(sidebar)

    def init_main_content(self):
        # Container for the pages
        self.main_container = QFrame()
        main_layout = QVBoxLayout(self.main_container)
        main_layout.setContentsMargins(30, 25, 30, 25)
        main_layout.setSpacing(20)
        
        # Header bar
        header_bar = QHBoxLayout()
        self.lbl_page_title = QLabel("TRACKING CONSOLE")
        self.lbl_page_title.setObjectName("section_title")
        self.lbl_page_title.setStyleSheet("font-size: 18px;")
        header_bar.addWidget(self.lbl_page_title)
        
        header_bar.addStretch()
        
        self.btn_power = QPushButton("START ENGAGEMENT")
        self.btn_power.setStyleSheet(f"font-size: 12px; min-width: 150px; background-color: rgba(57, 255, 20, 0.08); border-color: #39FF14; color: #39FF14;")
        self.btn_power.clicked.connect(self.toggle_tracking)
        header_bar.addWidget(self.btn_power)
        
        main_layout.addLayout(header_bar)
        
        # Stacked pages widget
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)
        
        # Build pages
        self.create_tracking_page()
        self.create_mapping_page()
        self.create_trainer_page()
        self.create_tweaks_page()
        self.create_voice_page()
        
        # Bottom Console/Log area (Globally visible at bottom of content)
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(120)
        self.log_console.setPlaceholderText("SYSTEM TELEMETRY CONSOLE...")
        main_layout.addWidget(self.log_console)
        
        self.root_layout.addWidget(self.main_container, 1)

    def create_tracking_page(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Left side: Live Camera Stream Card
        cam_card = QFrame()
        cam_card.setObjectName("card_panel_highlight")
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(8, 8, 8, 8)
        
        self.camera_view = CameraWidget()
        self.camera_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cam_layout.addWidget(self.camera_view)
        
        layout.addWidget(cam_card, 2)
        
        # Right side: Live telemetry widgets
        telemetry_card = QFrame()
        telemetry_card.setObjectName("card_panel")
        telemetry_card.setFixedWidth(280)
        tel_layout = QVBoxLayout(telemetry_card)
        tel_layout.setContentsMargins(20, 20, 20, 20)
        tel_layout.setSpacing(15)
        
        title = QLabel("LIVE TELEMETRY")
        title.setStyleSheet("color: #00F0FF; font-size: 14px; font-weight: bold;")
        tel_layout.addWidget(title)
        
        # Telemetry stats
        self.lbl_fps = QLabel("Processing FPS: 0.0")
        self.lbl_fps.setObjectName("status_label")
        tel_layout.addWidget(self.lbl_fps)
        
        self.lbl_cursor_pos = QLabel("Cursor Pos: (0, 0)")
        self.lbl_cursor_pos.setObjectName("status_label")
        tel_layout.addWidget(self.lbl_cursor_pos)
        
        tel_layout.addSpacing(10)
        
        # Right Hand Gesture status box
        self.right_hand_box = QGroupBox("RIGHT HAND (CURSOR)")
        self.right_hand_box.setStyleSheet("QGroupBox { border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 6px; font-weight: bold; margin-top: 10px; color: #00F0FF; } QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }")
        rh_layout = QVBoxLayout(self.right_hand_box)
        rh_layout.setContentsMargins(10, 15, 10, 10)
        self.lbl_right_gesture = QLabel("Gesture: NONE")
        self.lbl_right_gesture.setStyleSheet("font-size: 14px; font-weight: bold; color: #E2E8F0;")
        rh_layout.addWidget(self.lbl_right_gesture)
        tel_layout.addWidget(self.right_hand_box)

        # Left Hand Gesture status box
        self.left_hand_box = QGroupBox("LEFT HAND (SCROLL)")
        self.left_hand_box.setStyleSheet("QGroupBox { border: 1px solid rgba(255, 0, 127, 0.15); border-radius: 6px; font-weight: bold; margin-top: 10px; color: #FF007F; } QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }")
        lh_layout = QVBoxLayout(self.left_hand_box)
        lh_layout.setContentsMargins(10, 15, 10, 10)
        self.lbl_left_gesture = QLabel("Gesture: NONE")
        self.lbl_left_gesture.setStyleSheet("font-size: 14px; font-weight: bold; color: #E2E8F0;")
        lh_layout.addWidget(self.lbl_left_gesture)
        tel_layout.addWidget(self.left_hand_box)
        
        # Mode quick toggles
        tel_layout.addSpacing(10)
        mode_label = QLabel("TRACKING PROFILE")
        mode_label.setStyleSheet("color: #FF007F; font-size: 11px; font-weight: bold;")
        tel_layout.addWidget(mode_label)
        
        self.btn_precision_mode = QPushButton("PRECISION (SMOOTH)")
        self.btn_precision_mode.clicked.connect(lambda: self.change_mode("precision"))
        tel_layout.addWidget(self.btn_precision_mode)
        
        self.btn_gaming_mode = QPushButton("GAMING (LOW LATENCY)")
        self.btn_gaming_mode.clicked.connect(lambda: self.change_mode("gaming"))
        tel_layout.addWidget(self.btn_gaming_mode)
        
        self.update_mode_buttons_style()
        tel_layout.addStretch()
        
        layout.addWidget(telemetry_card)
        self.stacked_widget.addWidget(page)

    def create_mapping_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QFrame()
        card.setObjectName("card_panel")
        grid = QGridLayout(card)
        grid.setContentsMargins(25, 25, 25, 25)
        grid.setSpacing(15)
        
        title = QLabel("GESTURE ACTION MAPPINGS")
        title.setStyleSheet("color: #00F0FF; font-size: 16px; font-weight: bold;")
        grid.addWidget(title, 0, 0, 1, 2)
        
        desc = QLabel("Assign custom operating system mouse triggers to hand gestures:")
        desc.setStyleSheet("color: #64748B; font-size: 12px;")
        grid.addWidget(desc, 1, 0, 1, 2)
        
        # Hand gestures we support mapping
        self.gesture_combos = {}
        gestures = [
            ("PINCH", "Action mapped to Single Finger Pinch:"),
            ("TWO_FINGERS", "Action mapped to Two Fingers pointing up:"),
            ("FIST", "Action mapped to folded FIST:"),
            ("PALM", "Action mapped to Neutral Open Palm:")
        ]
        
        actions = ["CLICK", "RIGHT_CLICK", "DRAG_AND_DROP", "SCROLL", "NONE"]
        
        row = 2
        for key, description in gestures:
            lbl = QLabel(description)
            lbl.setStyleSheet("font-weight: 500;")
            grid.addWidget(lbl, row, 0)
            
            combo = QComboBox()
            combo.addItems(actions)
            # Set currently saved value
            current_mapping = self.config.get("gesture_mappings", {}).get(key, "NONE")
            combo.setCurrentText(current_mapping)
            combo.currentTextChanged.connect(self.save_mappings)
            grid.addWidget(combo, row, 1)
            
            self.gesture_combos[key] = combo
            row += 1
            
        grid.addWidget(QLabel(""), row, 0, 1, 2)  # spacer
        
        # Sensitivity sliders in same layout
        row += 1
        grid.addWidget(QLabel("CURSORS & SCROLLING CONFIGS"), row, 0, 1, 2)
        grid.itemAtPosition(row, 0).widget().setStyleSheet("color: #FF007F; font-weight: bold; margin-top: 10px;")
        
        # Sensitivity X Slider
        row += 1
        grid.addWidget(QLabel("Horizontal Mouse Speed (Sensitivity X):"), row, 0)
        self.slider_sens_x = QSlider(Qt.Horizontal)
        self.slider_sens_x.setRange(5, 40)  # maps to 0.5 - 4.0
        self.slider_sens_x.setValue(int(self.config.get("sensitivity_x", 1.5) * 10))
        self.slider_sens_x.valueChanged.connect(self.save_sens_sliders)
        grid.addWidget(self.slider_sens_x, row, 1)
        
        # Sensitivity Y Slider
        row += 1
        grid.addWidget(QLabel("Vertical Mouse Speed (Sensitivity Y):"), row, 0)
        self.slider_sens_y = QSlider(Qt.Horizontal)
        self.slider_sens_y.setRange(5, 40)  # maps to 0.5 - 4.0
        self.slider_sens_y.setValue(int(self.config.get("sensitivity_y", 1.5) * 10))
        self.slider_sens_y.valueChanged.connect(self.save_sens_sliders)
        grid.addWidget(self.slider_sens_y, row, 1)
        
        # Scroll Speed Slider
        row += 1
        grid.addWidget(QLabel("Vertical Scroll Speed:"), row, 0)
        self.slider_scroll = QSlider(Qt.Horizontal)
        self.slider_scroll.setRange(1, 30)  # maps to 0.1 - 3.0
        self.slider_scroll.setValue(int(self.config.get("scroll_speed", 1.0) * 10))
        self.slider_scroll.valueChanged.connect(self.save_sens_sliders)
        grid.addWidget(self.slider_scroll, row, 1)
        
        grid.setRowStretch(row + 1, 1)
        layout.addWidget(card)
        self.stacked_widget.addWidget(page)

    def create_trainer_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QFrame()
        card.setObjectName("card_panel")
        grid = QGridLayout(card)
        grid.setContentsMargins(25, 25, 25, 25)
        grid.setSpacing(15)
        
        title = QLabel("NEURAL NETWORK GESTURE TRAINING")
        title.setStyleSheet("color: #00F0FF; font-size: 16px; font-weight: bold;")
        grid.addWidget(title, 0, 0, 1, 3)
        
        desc = QLabel("Collect camera frame data and train custom Deep Learning classifier parameters:")
        desc.setStyleSheet("color: #64748B; font-size: 12px;")
        grid.addWidget(desc, 1, 0, 1, 3)
        
        # AI Mode Activation Checkbox
        self.chk_use_ai = QCheckBox("Enable AI Gesture Classifier (Uncheck to fallback to Rule-Based)")
        self.chk_use_ai.setChecked(self.config.get("use_ai_classification", False))
        self.chk_use_ai.stateChanged.connect(self.toggle_ai_classification)
        grid.addWidget(self.chk_use_ai, 2, 0, 1, 3)
        
        grid.addWidget(QLabel("DATA COLLECTION STATUS"), 3, 0, 1, 3)
        grid.itemAtPosition(3, 0).widget().setStyleSheet("color: #FF007F; font-weight: bold; margin-top: 10px;")
        
        # Dropdown to select class to record
        grid.addWidget(QLabel("Target gesture to train:"), 4, 0)
        self.combo_train_label = QComboBox()
        self.combo_train_label.addItems(["PALM", "PINCH", "TWO_FINGERS", "FIST", "SCROLL"])
        grid.addWidget(self.combo_train_label, 4, 1)
        
        # Action buttons for recording data
        btn_record = QPushButton("⏺️ RECORD SAMPLES (RIGHT HAND)")
        btn_record.clicked.connect(self.record_gesture_samples)
        grid.addWidget(btn_record, 4, 2)
        
        # Class stats progress bars list
        self.stat_bars = {}
        row = 5
        
        labels_info = [
            ("PALM", "PALM (Neutral) samples:"),
            ("PINCH", "PINCH (Click) samples:"),
            ("TWO_FINGERS", "TWO FINGERS (Right-click) samples:"),
            ("FIST", "FIST (Drag & scroll) samples:"),
            ("SCROLL", "SCROLL samples:")
        ]
        
        for key, text in labels_info:
            lbl = QLabel(text)
            grid.addWidget(lbl, row, 0)
            
            pbar = QProgressBar()
            pbar.setRange(0, 100)
            pbar.setStyleSheet("QProgressBar { background: #14192E; border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 4px; text-align: center; } QProgressBar::chunk { background: #00F0FF; }")
            grid.addWidget(pbar, row, 1)
            self.stat_bars[key] = pbar
            
            btn_clear = QPushButton("Reset Class")
            btn_clear.setObjectName("danger_btn")
            btn_clear.setFixedWidth(100)
            btn_clear.clicked.connect(lambda checked=False, k=key: self.clear_gesture_class(k))
            grid.addWidget(btn_clear, row, 2)
            row += 1
            
        # Model training launcher
        grid.addWidget(QLabel("MODEL CONTROLS"), row, 0, 1, 3)
        grid.itemAtPosition(row, 0).widget().setStyleSheet("color: #FF007F; font-weight: bold; margin-top: 10px;")
        
        row += 1
        self.btn_run_training = QPushButton("🧠 EXECUTE MODEL TRAINING (ADAM BACKPROP)")
        self.btn_run_training.setStyleSheet("background-color: rgba(0, 240, 255, 0.15); border-color: #00F0FF; font-size: 13px; height: 35px;")
        self.btn_run_training.clicked.connect(self.execute_training)
        grid.addWidget(self.btn_run_training, row, 0, 1, 3)
        
        grid.setRowStretch(row + 1, 1)
        self.update_trainer_stats()
        
        layout.addWidget(card)
        self.stacked_widget.addWidget(page)

    def create_tweaks_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        
        card = QFrame()
        card.setObjectName("card_panel")
        grid = QGridLayout(card)
        grid.setContentsMargins(25, 25, 25, 25)
        grid.setSpacing(15)
        
        title = QLabel("SYSTEM PERFORMANCE & CAPABILITIES")
        title.setStyleSheet("color: #00F0FF; font-size: 16px; font-weight: bold;")
        grid.addWidget(title, 0, 0, 1, 2)
        
        # Multi-hand toggle
        row = 1
        self.chk_multihand = QCheckBox("Enable Multi-Hand Separation Control")
        self.chk_multihand.setChecked(self.config.get("multi_hand_enabled", True))
        self.chk_multihand.stateChanged.connect(self.save_tweaks)
        grid.addWidget(self.chk_multihand, row, 0, 1, 2)
        
        # Left/Right hand roles
        row += 1
        grid.addWidget(QLabel("Right Hand Operating Role:"), row, 0)
        self.combo_right_role = QComboBox()
        self.combo_right_role.addItems(["CURSOR", "NONE"])
        self.combo_right_role.setCurrentText(self.config.get("right_hand_action", "CURSOR"))
        self.combo_right_role.currentTextChanged.connect(self.save_tweaks)
        grid.addWidget(self.combo_right_role, row, 1)
        
        row += 1
        grid.addWidget(QLabel("Left Hand Operating Role:"), row, 0)
        self.combo_left_role = QComboBox()
        self.combo_left_role.addItems(["SCROLL", "NONE"])
        self.combo_left_role.setCurrentText(self.config.get("left_hand_action", "SCROLL"))
        self.combo_left_role.currentTextChanged.connect(self.save_tweaks)
        grid.addWidget(self.combo_left_role, row, 1)
        
        row += 1
        grid.addWidget(QLabel("Camera Device Index:"), row, 0)
        self.combo_camera_idx = QComboBox()
        self.combo_camera_idx.addItems(["0 (Primary Built-in)", "1 (External Web Camera)", "2", "3"])
        self.combo_camera_idx.setCurrentIndex(min(3, int(self.config.get("camera_index", 0))))
        self.combo_camera_idx.currentIndexChanged.connect(self.save_tweaks)
        grid.addWidget(self.combo_camera_idx, row, 1)
        
        row += 1
        grid.addWidget(QLabel("Smoothing Filter Factor (EMA):"), row, 0)
        self.slider_smoothing = QSlider(Qt.Horizontal)
        self.slider_smoothing.setRange(5, 95)  # maps to 0.05 - 0.95
        self.slider_smoothing.setValue(int(self.config.get("smoothing_factor", 0.25) * 100))
        self.slider_smoothing.valueChanged.connect(self.save_tweaks)
        grid.addWidget(self.slider_smoothing, row, 1)
        
        row += 1
        grid.addWidget(QLabel("Frames Per Second Cap:"), row, 0)
        self.combo_fps_cap = QComboBox()
        self.combo_fps_cap.addItems(["15 FPS (Ultra Low CPU)", "30 FPS (Standard Smooth)", "60 FPS (Ultra Low Latency Gaming)"])
        fps_mapping = {15: 0, 30: 1, 60: 2}
        self.combo_fps_cap.setCurrentIndex(fps_mapping.get(self.config.get("fps_cap", 30), 1))
        self.combo_fps_cap.currentIndexChanged.connect(self.save_tweaks)
        grid.addWidget(self.combo_fps_cap, row, 1)
        
        grid.setRowStretch(row + 1, 1)
        layout.addWidget(card)
        self.stacked_widget.addWidget(page)

    def create_voice_page(self):
        """Voice Assistant Control page (IRONMAN JARVIS / FRIDAY theme)."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Left Panel: Pulse visualizer & core details
        visual_card = QFrame()
        visual_card.setObjectName("card_panel_highlight")
        visual_card.setMinimumWidth(320)
        v_layout = QVBoxLayout(visual_card)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.setSpacing(15)
        
        lbl_core_title = QLabel("ASSISTANT NEURAL CORE")
        lbl_core_title.setStyleSheet("color: #00F0FF; font-size: 14px; font-weight: bold; letter-spacing: 1px;")
        v_layout.addWidget(lbl_core_title, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Concentric glowing orb widget
        self.orb_widget = JarvisOrbWidget()
        v_layout.addWidget(self.orb_widget, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Audio input toggle
        self.btn_mic = QPushButton("ENABLE VOICE CHANNELS")
        self.btn_mic.setStyleSheet("background-color: rgba(0, 240, 255, 0.08); border-color: #00F0FF; color: #00F0FF; font-size: 12px; height: 35px;")
        self.btn_mic.clicked.connect(self.toggle_voice_listening)
        v_layout.addWidget(self.btn_mic)
        
        # Assistant status indicators
        self.lbl_mic_status = QLabel("MIC CHANNEL: OFFLINE")
        self.lbl_mic_status.setStyleSheet("color: #FF007F; font-size: 11px; font-weight: bold; font-family: monospace;")
        self.lbl_mic_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v_layout.addWidget(self.lbl_mic_status)
        
        # Assistant Settings
        settings_box = QGroupBox("CORE PREFERENCES")
        settings_box.setStyleSheet("QGroupBox { border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 6px; font-weight: bold; color: #00F0FF; } QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }")
        sb_layout = QGridLayout(settings_box)
        sb_layout.setContentsMargins(10, 15, 10, 10)
        sb_layout.setSpacing(10)
        
        sb_layout.addWidget(QLabel("Assistant Personality:"), 0, 0)
        self.combo_personality = QComboBox()
        self.combo_personality.addItems(["JARVIS", "FRIDAY"])
        self.combo_personality.setCurrentText(self.config.get("assistant_name", "JARVIS"))
        self.combo_personality.currentTextChanged.connect(self.change_assistant_name)
        sb_layout.addWidget(self.combo_personality, 0, 1)
        
        self.chk_voice_output = QCheckBox("Voice Feedback Synthesis")
        self.chk_voice_output.setChecked(self.config.get("voice_enabled", True))
        self.chk_voice_output.stateChanged.connect(self.toggle_voice_output)
        sb_layout.addWidget(self.chk_voice_output, 1, 0, 1, 2)
        
        v_layout.addWidget(settings_box)
        
        # Live Assistant spoken transcript box
        self.txt_transcript = QTextEdit()
        self.txt_transcript.setReadOnly(True)
        self.txt_transcript.setPlaceholderText("Jarvis voice transcript stream...")
        self.txt_transcript.setMaximumHeight(140)
        v_layout.addWidget(self.txt_transcript)
        
        layout.addWidget(visual_card, 1)
        
        # Right Panel: Dynamic command manager table and creator
        cmd_card = QFrame()
        cmd_card.setObjectName("card_panel")
        cmd_layout = QVBoxLayout(cmd_card)
        cmd_layout.setContentsMargins(20, 20, 20, 20)
        cmd_layout.setSpacing(12)
        
        lbl_mgr_title = QLabel("DYNAMIC VOICE COMMAND MANAGER")
        lbl_mgr_title.setStyleSheet("color: #00F0FF; font-size: 15px; font-weight: bold;")
        cmd_layout.addWidget(lbl_mgr_title)
        
        lbl_mgr_desc = QLabel("Edit voice triggers, actions, and custom spoken audio replies in real-time:")
        lbl_mgr_desc.setStyleSheet("color: #64748B; font-size: 12px;")
        cmd_layout.addWidget(lbl_mgr_desc)
        
        # List of existing commands
        self.cmd_table = QTableWidget()
        self.cmd_table.setColumnCount(3)
        self.cmd_table.setHorizontalHeaderLabels(["Voice Phrase Trigger", "Mapped System Action", "Action"])
        self.cmd_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cmd_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.cmd_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.cmd_table.setStyleSheet("QTableWidget { background: #0C0F1D; border: 1px solid rgba(0, 240, 255, 0.15); border-radius: 6px; selection-background-color: rgba(0, 240, 255, 0.15); } QHeaderView::section { background-color: #101424; color: #00F0FF; padding: 5px; border: 1px solid rgba(0, 240, 255, 0.1); }")
        self.cmd_table.verticalHeader().setVisible(False)
        cmd_layout.addWidget(self.cmd_table)
        
        # Dynamic voice command adding UI
        add_box = QGroupBox("ADD / MODIFY ASSISTANT TRIGGER")
        add_box.setStyleSheet("QGroupBox { border: 1px solid rgba(255, 0, 127, 0.15); border-radius: 6px; font-weight: bold; color: #FF007F; } QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 3px; }")
        add_layout = QGridLayout(add_box)
        add_layout.setContentsMargins(10, 15, 10, 10)
        add_layout.setSpacing(10)
        
        add_layout.addWidget(QLabel("Voice Phrase Trigger:"), 0, 0)
        self.txt_voice_phrase = QLineEdit()
        self.txt_voice_phrase.setPlaceholderText("e.g. open browser, status check")
        add_layout.addWidget(self.txt_voice_phrase, 0, 1)
        
        add_layout.addWidget(QLabel("Mapped System Action:"), 1, 0)
        self.combo_voice_action = QComboBox()
        self.combo_voice_action.addItems([
            "say_hello", "say_status", "precision_mode", "gaming_mode", 
            "start_tracking", "stop_tracking", "increase_sensitivity", "decrease_sensitivity",
            "open_app (Extra Command below)", "custom_cmd (Extra Shell CMD below)"
        ])
        self.combo_voice_action.currentTextChanged.connect(self.toggle_extra_cmd_box)
        add_layout.addWidget(self.combo_voice_action, 1, 1)
        
        self.lbl_extra_cmd = QLabel("Executable Path / CMD:")
        self.lbl_extra_cmd.setVisible(False)
        add_layout.addWidget(self.lbl_extra_cmd, 2, 0)
        
        self.txt_extra_cmd = QLineEdit()
        self.txt_extra_cmd.setPlaceholderText("e.g. notepad.exe, dir /s")
        self.txt_extra_cmd.setVisible(False)
        add_layout.addWidget(self.txt_extra_cmd, 2, 1)
        
        add_layout.addWidget(QLabel("Jarvis Spoken Response:"), 3, 0)
        self.txt_voice_response = QLineEdit()
        self.txt_voice_response.setPlaceholderText("e.g. Yes sir, launching MS Edge browser.")
        add_layout.addWidget(self.txt_voice_response, 3, 1)
        
        self.btn_save_cmd = QPushButton("💾 SAVE DYNAMIC COMMAND")
        self.btn_save_cmd.clicked.connect(self.save_voice_command)
        add_layout.addWidget(self.btn_save_cmd, 4, 0, 1, 2)
        
        cmd_layout.addWidget(add_box)
        layout.addWidget(cmd_card, 2)
        
        self.stacked_widget.addWidget(page)
        self.refresh_voice_commands_table()

    def toggle_extra_cmd_box(self, text):
        visible = "open_app" in text or "custom_cmd" in text
        self.lbl_extra_cmd.setVisible(visible)
        self.txt_extra_cmd.setVisible(visible)

    def refresh_voice_commands_table(self):
        """Populate voice commands list with delete buttons dynamically."""
        commands = self.config.get("voice_commands", {})
        self.cmd_table.setRowCount(len(commands))
        
        for index, (trigger, info) in enumerate(commands.items()):
            # 1. Trigger word
            self.cmd_table.setItem(index, 0, QTableWidgetItem(trigger))
            
            # 2. Mapped Action
            action = info.get("action", "")
            self.cmd_table.setItem(index, 1, QTableWidgetItem(action))
            
            # 3. Action column containing Delete button
            btn_del = QPushButton("❌ Remove")
            btn_del.setStyleSheet("min-height: 18px; padding: 2px 8px; font-size: 11px;")
            btn_del.setObjectName("danger_btn")
            btn_del.clicked.connect(lambda checked=False, t=trigger: self.remove_voice_command(t))
            self.cmd_table.setCellWidget(index, 2, btn_del)

    def save_voice_command(self):
        phrase = self.txt_voice_phrase.text().strip().lower()
        action_type = self.combo_voice_action.currentText()
        response = self.txt_voice_response.text().strip()
        
        if not phrase:
            self.log("ERROR: Voice trigger phrase cannot be empty.")
            return
            
        # Parse action path
        if "open_app" in action_type:
            extra = self.txt_extra_cmd.text().strip()
            if not extra:
                self.log("ERROR: App executable path is required.")
                return
            action = f"open_app:{extra}"
        elif "custom_cmd" in action_type:
            extra = self.txt_extra_cmd.text().strip()
            if not extra:
                self.log("ERROR: Custom shell CMD script is required.")
                return
            action = f"custom_cmd:{extra}"
        else:
            action = action_type
            
        if not response:
            response = "Instruction acknowledged, sir."
            
        # Write to config database
        commands = self.config.get("voice_commands", {})
        commands[phrase] = {
            "action": action,
            "desc": f"Custom voice trigger: {phrase}",
            "speech_responses": [response]
        }
        self.config.set("voice_commands", commands)
        self.log(f"Dynamic voice trigger match saved: \"{phrase}\" -> \"{action}\"")
        
        # Reset fields
        self.txt_voice_phrase.clear()
        self.txt_extra_cmd.clear()
        self.txt_voice_response.clear()
        self.refresh_voice_commands_table()

    def remove_voice_command(self, phrase):
        commands = self.config.get("voice_commands", {})
        if phrase in commands:
            del commands[phrase]
            self.config.set("voice_commands", commands)
            self.log(f"Voice trigger \"{phrase}\" removed from active database.")
            self.refresh_voice_commands_table()

    def change_assistant_name(self, name):
        self.config.set("assistant_name", name)
        self.log(f"Assistant speech matrix personality loaded: {name}")

    def toggle_voice_output(self, state):
        enabled = state == Qt.Checked
        self.config.set("voice_enabled", enabled)
        if hasattr(self, "assistant") and self.assistant:
            if not enabled:
                self.assistant.stop_speech()
                self.assistant.tts = None
                self.log("Asynchronous text-to-speech module DISABLED.")
            else:
                self.assistant.init_tts()
                self.log("Asynchronous text-to-speech module ENABLED.")

    def toggle_voice_listening(self):
        if not self.assistant:
            self.log("Voice Engine not initialized.")
            return
            
        if self.assistant.listening:
            self.assistant.listening = False
            self.btn_mic.setText("ENABLE VOICE CHANNELS")
            self.btn_mic.setStyleSheet("background-color: rgba(0, 240, 255, 0.08); border-color: #00F0FF; color: #00F0FF; font-size: 12px; height: 35px;")
            self.lbl_mic_status.setText("MIC CHANNEL: OFFLINE")
            self.lbl_mic_status.setStyleSheet("color: #FF007F; font-size: 11px; font-weight: bold; font-family: monospace;")
            self.orb_widget.set_status("IDLE")
            self.log("Assistant microphone channels closed.")
        else:
            self.assistant.listening = True
            self.btn_mic.setText("DISABLE VOICE CHANNELS")
            self.btn_mic.setStyleSheet("background-color: rgba(255, 0, 127, 0.08); border-color: #FF007F; color: #FF007F; font-size: 12px; height: 35px;")
            self.lbl_mic_status.setText("MIC CHANNEL: LISTENING")
            self.lbl_mic_status.setStyleSheet("color: #39FF14; font-size: 11px; font-weight: bold; font-family: monospace;")
            self.orb_widget.set_status("LISTENING")
            self.log("Microphone voice channels activated. Waiting for wake trigger...")

    def init_tracker_thread(self):
        """Initializes the background thread for camera frame parsing."""
        self.tracker = HandTrackerThread(self.config, self.mouse)
        self.tracker.frame_ready.connect(self.on_frame_processed)
        self.tracker.log_message.connect(self.log)
        self.tracker.fps_updated.connect(self.on_fps_updated)

    def init_voice_assistant(self):
        """Initializes voice assistant listener thread (independent SAPI-sounddevice engine)."""
        self.assistant = VoiceAssistantThread(self.config)
        self.assistant.status_updated.connect(self.on_voice_status_changed)
        self.assistant.speech_detected.connect(self.on_voice_speech_heard)
        self.assistant.command_executed.connect(self.on_voice_command_executed)
        self.assistant.assistant_spoke.connect(self.on_voice_assistant_spoke)
        self.assistant.log_message.connect(self.log)
        self.assistant.start()

    @Slot(str)
    def on_voice_status_changed(self, status):
        """Callback from voice thread when status changes (LISTENING, IDLE, PROCESSING, SPEAKING)."""
        self.orb_widget.set_status(status)
        if status == "LISTENING":
            self.lbl_mic_status.setText("MIC CHANNEL: LISTENING")
            self.lbl_mic_status.setStyleSheet("color: #39FF14; font-size: 11px; font-weight: bold; font-family: monospace;")
        elif status == "PROCESSING":
            self.lbl_mic_status.setText("CORE THINKING...")
            self.lbl_mic_status.setStyleSheet("color: #FF007F; font-size: 11px; font-weight: bold; font-family: monospace;")
        elif status == "SPEAKING":
            self.lbl_mic_status.setText("CORE SPEAKING")
            self.lbl_mic_status.setStyleSheet("color: #00F0FF; font-size: 11px; font-weight: bold; font-family: monospace;")
        else:
            self.lbl_mic_status.setText("MIC CHANNEL: IDLE")
            self.lbl_mic_status.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold; font-family: monospace;")

    @Slot(str)
    def on_voice_speech_heard(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.txt_transcript.append(f"[{timestamp}] User: \"{text}\"")

    @Slot(str)
    def on_voice_assistant_spoke(self, text):
        timestamp = time.strftime("%H:%M:%S")
        name = self.config.get("assistant_name", "JARVIS")
        self.txt_transcript.append(f"[{timestamp}] {name}: \"{text}\"")

    @Slot(str, str, str)
    def on_voice_command_executed(self, trigger, action, response):
        """Executes actual OS commands and configurations when dynamic voice triggers match."""
        self.log(f"[Voice Command Triggered]: \"{trigger}\" -> Action: \"{action}\"")
        
        # 1. Action Matching
        if action == "precision_mode":
            self.change_mode("precision")
        elif action == "gaming_mode":
            self.change_mode("gaming")
        elif action == "start_tracking":
            if not self.tracker.isRunning():
                self.toggle_tracking()
        elif action == "stop_tracking":
            if self.tracker.isRunning():
                self.toggle_tracking()
        elif action == "increase_sensitivity":
            new_x = min(4.0, self.config.get("sensitivity_x", 1.5) + 0.5)
            new_y = min(4.0, self.config.get("sensitivity_y", 1.5) + 0.5)
            self.config.set("sensitivity_x", new_x)
            self.config.set("sensitivity_y", new_y)
            # Sync slider GUI elements
            self.slider_sens_x.setValue(int(new_x * 10))
            self.slider_sens_y.setValue(int(new_y * 10))
            self.log(f"Sensitivity scaled up to X:{new_x:.1f}, Y:{new_y:.1f}")
        elif action == "decrease_sensitivity":
            new_x = max(0.5, self.config.get("sensitivity_x", 1.5) - 0.5)
            new_y = max(0.5, self.config.get("sensitivity_y", 1.5) - 0.5)
            self.config.set("sensitivity_x", new_x)
            self.config.set("sensitivity_y", new_y)
            # Sync slider GUI elements
            self.slider_sens_x.setValue(int(new_x * 10))
            self.slider_sens_y.setValue(int(new_y * 10))
            self.log(f"Sensitivity scaled down to X:{new_x:.1f}, Y:{new_y:.1f}")
        elif action.startswith("open_app:"):
            cmd = action.split(":", 1)[1]
            try:
                subprocess.Popen(cmd, shell=True)
                self.log(f"Asynchronous application launch initiated: {cmd}")
            except Exception as e:
                self.log(f"Failed to launch command {cmd}: {e}")
        elif action.startswith("custom_cmd:"):
            cmd = action.split(":", 1)[1]
            try:
                subprocess.Popen(cmd, shell=True)
                self.log(f"Custom shell command executed in background: {cmd}")
            except Exception as e:
                self.log(f"Failed to run shell script: {e}")
        elif action == "say_hello":
            # Handled internally in thread by voice synthesis response, logging only
            pass
        elif action == "say_status":
            fps = self.tracker.status_info.get("fps", 0.0) if hasattr(self.tracker, "status_info") else 0.0
            tracking_state = "active and tracking" if self.tracker.isRunning() else "inactive and idle"
            status_report = f"SPyRaw core reports: tracking engine is {tracking_state}. Voice assistant listening channels are active. System sensitivity is scaled at {self.config.get('sensitivity_x', 1.5)}."
            self.assistant.speak(status_report)

    @Slot(int)
    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            
        page_titles = [
            "TRACKING CONSOLE", "GESTURE MAPPING MANAGER", 
            "AI NEURAL NET CLASS TRAINER", "SYSTEM TWEAKS PANEL",
            "PERSONAL VOICE ASSISTANT"
        ]
        if index < len(page_titles):
            self.lbl_page_title.setText(page_titles[index])

    def on_sidebar_click(self):
        btn = self.sender()
        page_idx = btn.property("page_index")
        self.switch_page(page_idx)

    def toggle_tracking(self):
        if self.tracker.isRunning():
            self.log("Stopping gesture tracking engine...")
            self.tracker.running = False
            self.tracker.wait()
            self.btn_power.setText("START ENGAGEMENT")
            self.btn_power.setStyleSheet("font-size: 12px; min-width: 150px; background-color: rgba(57, 255, 20, 0.08); border-color: #39FF14; color: #39FF14;")
            self.lbl_overall_status.setText("CORE ENGINE: IDLE")
            self.lbl_overall_status.setStyleSheet("color: #FF007F; font-size: 11px; font-weight: bold;")
            self.camera_view.update_frame(None, 0.0)
            self.log("Tracking engine shut down successfully.")
        else:
            self.log("Starting gesture tracking engine thread...")
            self.btn_power.setText("STOP ENGAGEMENT")
            self.btn_power.setStyleSheet("font-size: 12px; min-width: 150px; background-color: rgba(255, 0, 127, 0.08); border-color: #FF007F; color: #FF007F;")
            self.lbl_overall_status.setText("CORE ENGINE: TRACKING")
            self.lbl_overall_status.setStyleSheet("color: #39FF14; font-size: 11px; font-weight: bold;")
            self.tracker.start()

    def change_mode(self, mode):
        self.config.set("mode", mode)
        self.update_mode_buttons_style()
        self.log(f"Switched system mode profile to: {mode.upper()}")

    def update_mode_buttons_style(self):
        mode = self.config.get("mode", "precision")
        if mode == "precision":
            self.btn_precision_mode.setStyleSheet(f"border-color: {Theme.ACCENT_CYAN}; color: {Theme.ACCENT_CYAN}; background-color: rgba(0, 240, 255, 0.15);")
            self.btn_gaming_mode.setStyleSheet("")
        else:
            self.btn_gaming_mode.setStyleSheet(f"border-color: {Theme.ACCENT_PINK}; color: {Theme.ACCENT_PINK}; background-color: rgba(255, 0, 127, 0.15);")
            self.btn_precision_mode.setStyleSheet("")

    def save_mappings(self):
        mappings = {}
        for key, combo in self.gesture_combos.items():
            mappings[key] = combo.currentText()
        self.config.set("gesture_mappings", mappings)
        self.log("Custom gesture mappings updated successfully.")

    def save_sens_sliders(self):
        val_x = self.slider_sens_x.value() / 10.0
        val_y = self.slider_sens_y.value() / 10.0
        val_scroll = self.slider_scroll.value() / 10.0
        
        self.config.set("sensitivity_x", val_x)
        self.config.set("sensitivity_y", val_y)
        self.config.set("scroll_speed", val_scroll)

    def save_tweaks(self):
        self.config.set("multi_hand_enabled", self.chk_multihand.isChecked())
        self.config.set("right_hand_action", self.combo_right_role.currentText())
        self.config.set("left_hand_action", self.combo_left_role.currentText())
        
        cam_text = self.combo_camera_idx.currentText()
        camera_idx = int(cam_text.split(" ")[0])
        self.config.set("camera_index", camera_idx)
        
        smooth_val = self.slider_smoothing.value() / 100.0
        self.config.set("smoothing_factor", smooth_val)
        
        fps_text = self.combo_fps_cap.currentText()
        fps_cap = int(fps_text.split(" ")[0])
        self.config.set("fps_cap", fps_cap)
        
        self.log("System configuration modifications applied.")

    def toggle_ai_classification(self, state):
        use_ai = state == Qt.Checked
        self.config.set("use_ai_classification", use_ai)
        if use_ai:
            if not self.tracker.model_loaded:
                self.log("WARNING: AI model not trained. Please train the model before enabling.")
                self.chk_use_ai.setChecked(False)
                self.config.set("use_ai_classification", False)
            else:
                self.log("Neural network classification mode ENABLED.")
        else:
            self.log("Neural network classification mode DISABLED. Rule-based fallback active.")

    def record_gesture_samples(self):
        if not self.tracker.isRunning():
            self.log("Cannot record samples: Capture thread is not running. Click 'START ENGAGEMENT' first.")
            return
            
        label = self.combo_train_label.currentText()
        self.tracker.start_data_collection(label, count=100)

    def clear_gesture_class(self, label_name):
        self.tracker.dataset_manager.clear_class(label_name)
        self.update_trainer_stats()
        self.log(f"Cleared all recorded data samples for class: '{label_name}'")

    def update_trainer_stats(self):
        stats = self.tracker.dataset_manager.get_stats()
        for label, bar in self.stat_bars.items():
            count = stats.get(label, 0)
            bar.setValue(min(100, count))
            bar.setFormat(f"%v / 100 samples")

    def execute_training(self):
        stats = self.tracker.dataset_manager.get_stats()
        for k in ["PALM", "PINCH", "TWO_FINGERS", "FIST", "SCROLL"]:
            if stats.get(k, 0) < 15:
                self.log(f"CRITICAL: Cannot train. Class '{k}' has insufficient samples ({stats.get(k, 0)}/15 min).")
                return
                
        self.btn_run_training.setEnabled(False)
        self.btn_run_training.setText("TRAINING NEURAL NETWORK MODEL...")
        QTimer.singleShot(100, self._run_training_payload)

    def _run_training_payload(self):
        success = self.tracker.trigger_model_training()
        self.btn_run_training.setEnabled(True)
        self.btn_run_training.setText("🧠 EXECUTE MODEL TRAINING (ADAM BACKPROP)")
        self.update_trainer_stats()

    @Slot(np.ndarray, list, dict)
    def on_frame_processed(self, frame, landmarks, status):
        # Update live feed widget
        self.camera_view.update_frame(
            frame, 
            status["fps"],
            self.tracker.collecting_data,
            self.tracker.collect_label,
            self.tracker.collected_samples_count,
            self.tracker.collect_target_count
        )
        
        # Update telemetry labels
        self.lbl_fps.setText(f"Processing FPS: {status['fps']:.1f}")
        self.lbl_cursor_pos.setText(f"Cursor Pos: ({status['cursor_pos'][0]}, {status['cursor_pos'][1]})")
        self.lbl_right_gesture.setText(f"Gesture: {status['right_hand_gesture']}")
        self.lbl_left_gesture.setText(f"Gesture: {status['left_hand_gesture']}")
        
        if self.tracker.collecting_data:
            self.update_trainer_stats()

    @Slot(float)
    def on_fps_updated(self, fps):
        pass

    @Slot(str)
    def log(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.log_console.append(f"[{timestamp}] >> {text}")
        self.log_console.moveCursor(self.log_console.textCursor().MoveOperation.End)

    def closeEvent(self, event):
        """Clean up thread resources on exit."""
        if self.tracker and self.tracker.isRunning():
            self.tracker.running = False
            self.tracker.wait()
        if self.assistant and self.assistant.isRunning():
            self.assistant.running = False
            self.assistant.listening = False
            self.assistant.wait()
        event.accept()
