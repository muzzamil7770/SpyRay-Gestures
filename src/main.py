import sys
import os

# Add parent directory of src to sys.path to allow running this script directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from src.config import ConfigManager
from src.mouse_controller import WinMouseController
from src.gui.dashboard import DashboardWindow


def main():
    # Set high DPI scaling properties for modern high-resolution screens
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray if window is closed

    # Load configuration manager
    config_manager = ConfigManager()

    # Load low-latency ctypes mouse controller
    mouse_controller = WinMouseController()

    # Create dashboard UI window
    window = DashboardWindow(config_manager, mouse_controller)
    window.show()

    # Add a system tray icon for background operation (SaaS layout ready)
    # Since we might not have a local icon.png, we will use a standard fallback Qt icon
    tray_icon = QSystemTrayIcon(parent=app)
    
    # We can retrieve a default system icon for the tray
    style = app.style()
    default_icon = style.standardIcon(style.StandardPixmap.SP_ComputerIcon)
    tray_icon.setIcon(default_icon)
    tray_icon.setToolTip("SPyRaw Gestures Engine")

    # Create system tray menu
    menu = QMenu()
    
    show_action = QAction("Open Control Panel", parent=app)
    show_action.triggered.connect(window.showNormal)
    menu.addAction(show_action)

    toggle_action = QAction("Start/Stop Tracking", parent=app)
    toggle_action.triggered.connect(window.toggle_tracking)
    menu.addAction(toggle_action)

    menu.addSeparator()

    exit_action = QAction("Exit Engine", parent=app)
    exit_action.triggered.connect(lambda: exit_app(window, tray_icon, app))
    menu.addAction(exit_action)

    tray_icon.setContextMenu(menu)
    tray_icon.show()

    # Double click on tray icon restores the window
    tray_icon.activated.connect(lambda reason: on_tray_activated(reason, window))

    sys.exit(app.exec())


def on_tray_activated(reason, window):
    if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
        window.showNormal()
        window.activateWindow()


def exit_app(window, tray_icon, app):
    # Properly shutdown tracking and voice assistant threads
    if window.tracker and window.tracker.isRunning():
        window.tracker.running = False
        window.tracker.wait()
    if hasattr(window, "assistant") and window.assistant.isRunning():
        window.assistant.running = False
        window.assistant.listening = False
        window.assistant.wait()
    tray_icon.hide()
    app.quit()


if __name__ == "__main__":
    main()
