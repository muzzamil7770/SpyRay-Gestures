<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/MediaPipe-0.10+-green?logo=google&logoColor=white" alt="MediaPipe">
  <img src="https://img.shields.io/badge/OpenCV-4.8+-red?logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/PySide6-Qt%20GUI-41CD52?logo=qt&logoColor=white" alt="Qt">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

# SPyRaw Gestures

<p align="center">
  <strong>Control your PC cursor with hand gestures using real-time computer vision</strong>
</p>

<p align="center">
  A high-performance, AI-powered hand gesture recognition system that transforms your webcam into a touchless input device. Built with MediaPipe, OpenCV, and a futuristic cyberpunk-themed dashboard UI.
</p>

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| **🖱️ Cursor Control** | Smooth, jitter-free mouse movement via index finger tracking with EMA smoothing |
| **👆 Click Detection** | Pinch gesture (thumb + index) triggers left-click with debounce protection |
| **🖱️ Right Click** | Two-finger tap gesture with 800ms cooldown |
| **📜 Scroll** | Left-hand vertical movement for natural page scrolling |
| **✊ Drag & Drop** | Hold pinch to start dragging, release to drop |
| **🧠 AI Classification** | Optional TensorFlow Lite MLP model for custom gesture recognition |
| **📊 Rule-Based Fallback** | Robust geometric gesture detection (no training needed) |
| **🎯 Gesture Profiles** | Configurable mapping: `PINCH → CLICK`, `TWO_FINGERS → RIGHT_CLICK`, etc. |
| **🤲 Multi-Hand Support** | Left hand for scrolling, right hand for cursor — simultaneously |
| **⚡ FPS Optimization** | Low-latency pipeline with camera buffer minimization |
| **🎨 Cyberpunk HUD** | Futuristic holographic overlay with neon landmarks and target reticle |
| **🔧 Config Panel** | Real-time sensitivity, smoothing, and gesture mapping adjustments |
| **🖥️ System Tray** | Runs in background with tray icon for quick access |
| **📦 Standalone EXE** | PyInstaller-compiled single-file Windows executable |

---

## 📸 Screenshots

> *Coming soon — run the app and see the futuristic holographic HUD in action!*

---

## 🏗️ Architecture

```
# SPyRaw Gestures Repositoryc/
│   ├── main.py                 # Application entry point + system tray
│   ├── config.py               # YAML-based configuration manager
│   ├── hand_tracker.py         # Core hand tracking engine (MediaPipe)
│   ├── mouse_controller.py     # Low-level Windows mouse control (ctypes)
│   ├── ai_classifier.py        # MLP gesture classifier + dataset manager
│   └── gui/
│       ├── dashboard.py        # Main PySide6 dashboard window
│       ├── camera_widget.py    # Live camera feed widget
│       └── theme.py            # Cyberpunk dark theme styling
├── .gitignore
├── requirements.txt
├── run_app.bat                 # Quick-launch batch script
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** (tested with 3.14)
- **Windows 10/11** (uses native `ctypes` for mouse control)
- **Webcam** (built-in or USB)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/spyraw-gestures.git
cd spyraw-gestures

# 2. Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1   # PowerShell
# or: .\venv\Scripts\activate.bat   # CMD

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python src/main.py
```

### Build Standalone Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="SPyRawGestures" src/main.py
# Output: dist/SPyRawGestures.exe
```

---

## 🎮 Gesture Reference

| Gesture | Hand | Action | Visual |
|---------|------|--------|--------|
| **Open Palm + Move** | Right | Move cursor | 🖐️ |
| **Pinch (Thumb + Index)** | Right | Left click | 🤏 |
| **Two Fingers Extended** | Right | Right click | ✌️ |
| **Closed Fist** | Right | Drag & drop (hold) | ✊ |
| **Palm Up/Down** | Left | Scroll up/down | 🤚↕️ |
| **Open Palm (Left)** | Left | Scroll mode | 🖐️ |

---

## ⚙️ Configuration

The config panel (gear icon in the dashboard) lets you adjust:

| Setting | Default | Range |
|---------|---------|-------|
| `cursor_sensitivity` | `1.5` | `0.5 – 5.0` |
| `smoothing_factor` | `0.3` | `0.1 – 0.9` |
| `scroll_speed` | `1.0` | `0.5 – 3.0` |
| `click_cooldown_ms` | `300` | `100 – 1000` |
| `camera_index` | `0` | `0, 1, 2...` |
| `use_ai_classification` | `false` | `true/false` |
| `multi_hand_enabled` | `true` | `true/false` |

Settings are persisted in `config.yaml` (auto-generated on first run).

---

## 🧠 AI Training (Optional)

The built-in gesture training system lets you create custom gesture models:

1. **Open the Training Panel** in the dashboard
2. **Select a gesture label** (e.g., `THUMBS_UP`)
3. **Record samples** — perform the gesture 100 times (5–10 seconds)
4. **Train the MLP model** — click "Train" to fit the neural network
5. **Enable AI mode** in settings → the model replaces rule-based detection

The trained model is saved as both PyTorch (`.pth`) and TFLite (`.tflite`) formats.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Hand Tracking** | Google MediaPipe (Tasks API / Solutions API) |
| **Computer Vision** | OpenCV 4.x |
| **GUI Framework** | PySide6 (Qt 6) |
| **Mouse Control** | Windows `ctypes` (user32.dll) |
| **AI Model** | Custom MLP (PyTorch → TFLite) |
| **Packaging** | PyInstaller |
| **Config** | YAML |

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-gesture`
3. **Commit** your changes: `git commit -m "Add amazing gesture support"`
4. **Push** to your branch: `git push origin feature/amazing-gesture`
5. **Open** a Pull Request

---

## 📝 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Google MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker) — Hand landmark detection
- [OpenCV](https://opencv.org/) — Real-time computer vision
- [Qt/PySide6](https://www.qt.io/) — Cross-platform GUI framework

---

<p align="center">
  <strong>Built with ❤️ and Computer Vision</strong>
</p>
