import ctypes
import time

# Mouse Event Flags
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_WHEEL = 0x0800

class WinMouseController:
    def __init__(self):
        # Load user32 dll
        self.user32 = ctypes.windll.user32
        
        # Get screen width and height
        self.screen_width = self.user32.GetSystemMetrics(0)
        self.screen_height = self.user32.GetSystemMetrics(1)
        
        self.is_drag_holding = False

    def get_position(self):
        """Get current mouse position."""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        self.user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def move_to(self, x, y):
        """Move cursor to absolute pixel coordinates, bound by screen limits."""
        x = max(0, min(int(x), self.screen_width - 1))
        y = max(0, min(int(y), self.screen_height - 1))
        self.user32.SetCursorPos(x, y)

    def click(self):
        """Perform a standard left click."""
        self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.01)  # brief hold for OS recognition
        self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def right_click(self):
        """Perform a standard right click."""
        self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.01)
        self.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    def double_click(self):
        """Perform a double click."""
        self.click()
        time.sleep(0.1)
        self.click()

    def start_drag(self):
        """Hold the left mouse button down if not already holding."""
        if not self.is_drag_holding:
            self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            self.is_drag_holding = True

    def end_drag(self):
        """Release the left mouse button if holding."""
        if self.is_drag_holding:
            self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.is_drag_holding = False

    def scroll(self, amount):
        """
        Scroll the mouse wheel.
        amount > 0 scrolls UP, amount < 0 scrolls DOWN.
        On Windows, a scroll delta of 120 is one notch.
        """
        # Scale scroll amount
        delta = int(amount * 120)
        self.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, delta, 0)
