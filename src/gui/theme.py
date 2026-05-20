class Theme:
    # Futuristic Hologram Color Palette
    BG_DARK = "#090C15"
    CARD_BG = "#101424"
    ACCENT_CYAN = "#00F0FF"
    ACCENT_PINK = "#FF007F"
    TEXT_LIGHT = "#E2E8F0"
    TEXT_MUTED = "#64748B"
    BORDER_COLOR = "rgba(0, 240, 255, 0.18)"
    
    QSS = """
    QMainWindow {
        background-color: #090C15;
    }
    
    QWidget {
        color: #E2E8F0;
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
        font-size: 13px;
    }
    
    /* Neon Hologram Glassmorphism Cards */
    QFrame#card_panel {
        background-color: #101424;
        border: 1px solid rgba(0, 240, 255, 0.18);
        border-radius: 12px;
    }
    
    QFrame#card_panel_highlight {
        background-color: #14192E;
        border: 1px solid rgba(0, 240, 255, 0.35);
        border-radius: 12px;
    }

    /* Left Sidebar Navigation */
    QFrame#sidebar {
        background-color: #0C0F1D;
        border-right: 1px solid rgba(0, 240, 255, 0.1);
    }
    
    /* Headers & Typography */
    QLabel#header_title {
        color: #00F0FF;
        font-size: 22px;
        font-weight: bold;
        letter-spacing: 1px;
    }
    
    QLabel#section_title {
        color: #FF007F;
        font-size: 16px;
        font-weight: bold;
        letter-spacing: 0.5px;
    }
    
    QLabel#status_label {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 12px;
    }

    /* Holographic Custom Buttons */
    QPushButton {
        background-color: rgba(0, 240, 255, 0.07);
        color: #00F0FF;
        border: 1px solid rgba(0, 240, 255, 0.4);
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
        min-height: 20px;
    }
    
    QPushButton:hover {
        background-color: rgba(0, 240, 255, 0.18);
        border: 1px solid #00F0FF;
    }
    
    QPushButton:pressed {
        background-color: rgba(0, 240, 255, 0.3);
    }
    
    QPushButton#danger_btn {
        background-color: rgba(255, 0, 127, 0.07);
        color: #FF007F;
        border: 1px solid rgba(255, 0, 127, 0.4);
    }
    
    QPushButton#danger_btn:hover {
        background-color: rgba(255, 0, 127, 0.18);
        border: 1px solid #FF007F;
    }
    
    QPushButton#danger_btn:pressed {
        background-color: rgba(255, 0, 127, 0.3);
    }

    QPushButton#sidebar_btn {
        background-color: transparent;
        color: #64748B;
        border: none;
        border-radius: 0px;
        padding: 12px 20px;
        text-align: left;
        font-size: 14px;
    }
    
    QPushButton#sidebar_btn:hover {
        color: #00F0FF;
        background-color: rgba(0, 240, 255, 0.05);
    }
    
    QPushButton#sidebar_btn[active="true"] {
        color: #00F0FF;
        background-color: rgba(0, 240, 255, 0.1);
        border-left: 3px solid #00F0FF;
    }

    /* Sliders */
    QSlider::groove:horizontal {
        height: 6px;
        background: #14192E;
        border-radius: 3px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    QSlider::sub-page:horizontal {
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                    stop: 0 #FF007F, stop: 1 #00F0FF);
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        background: #00F0FF;
        border: 2px solid #E2E8F0;
        width: 14px;
        margin-top: -5px;
        margin-bottom: -5px;
        border-radius: 7px;
    }
    
    QSlider::handle:horizontal:hover {
        background: #E2E8F0;
        border-color: #00F0FF;
    }

    /* Dropdowns (ComboBoxes) */
    QComboBox {
        background-color: #101424;
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 6px;
        padding: 6px 12px;
        color: #E2E8F0;
    }
    
    QComboBox:hover {
        border-color: #00F0FF;
    }
    
    QComboBox::drop-down {
        border: none;
        width: 20px;
    }
    
    QComboBox::down-arrow {
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid #00F0FF;
        margin-right: 10px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #101424;
        border: 1px solid rgba(0, 240, 255, 0.3);
        selection-background-color: rgba(0, 240, 255, 0.15);
        selection-color: #00F0FF;
        color: #E2E8F0;
    }

    /* Scrollbars */
    QScrollBar:vertical {
        border: none;
        background: #090C15;
        width: 8px;
        margin: 0px;
    }
    
    QScrollBar::handle:vertical {
        background: rgba(0, 240, 255, 0.25);
        min-height: 20px;
        border-radius: 4px;
    }
    
    QScrollBar::handle:vertical:hover {
        background: rgba(0, 240, 255, 0.5);
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    /* Logs & Text Console */
    QTextEdit {
        background-color: #0C0F1D;
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 8px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 11px;
        color: #00FFB0; /* Matrix glowing green text */
    }

    /* Checkbox */
    QCheckBox {
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid rgba(0, 240, 255, 0.3);
        background-color: #101424;
    }
    
    QCheckBox::indicator:hover {
        border-color: #00F0FF;
    }
    
    QCheckBox::indicator:checked {
        background-color: #00F0FF;
        border-color: #00F0FF;
        image: none; /* Can draw a custom dot */
    }
    
    QCheckBox::indicator:checked:hover {
        background-color: #E2E8F0;
    }
    """
