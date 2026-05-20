import os
import json

DEFAULT_CONFIG = {
    "sensitivity_x": 1.5,
    "sensitivity_y": 1.5,
    "smoothing_factor": 0.25,
    "mode": "precision",
    "multi_hand_enabled": True,
    "left_hand_action": "SCROLL",
    "right_hand_action": "CURSOR",
    "use_ai_classification": False,
    "gesture_mappings": {
        "PINCH": "CLICK",
        "TWO_FINGERS": "RIGHT_CLICK",
        "FIST": "DRAG_AND_DROP",
        "PALM": "NEUTRAL"
    },
    "scroll_speed": 1.0,
    "precision_multiplier": 0.4,
    "fps_cap": 30,
    "camera_index": 0,
    "assistant_name": "JARVIS",
    "voice_enabled": True,
    "voice_commands": {
        "precision mode": {
            "action": "precision_mode",
            "desc": "Switch tracker to Precision mode",
            "speech_responses": ["Activating precision parameters, sir.", "Precision mode engaged, sir.", "Switching to precision sensors."]
        },
        "gaming mode": {
            "action": "gaming_mode",
            "desc": "Switch tracker to low-latency Gaming mode",
            "speech_responses": ["Low-latency gaming mode active, sir.", "Engaging maximum responsiveness.", "Gaming mode engaged."]
        },
        "start tracking": {
            "action": "start_tracking",
            "desc": "Activate hand tracking thread",
            "speech_responses": ["Engaging gesture systems, sir.", "Tracking systems are online.", "Gesture control active."]
        },
        "stop tracking": {
            "action": "stop_tracking",
            "desc": "Deactivate hand tracking thread",
            "speech_responses": ["Deactivating gesture systems. Going to sleep.", "Gesture tracking offline.", "Systems are now idle."]
        },
        "increase sensitivity": {
            "action": "increase_sensitivity",
            "desc": "Boost mouse sensitivity",
            "speech_responses": ["Increasing cursor responsiveness, sir.", "Sensitivity boosted.", "Target sensitivity increased."]
        },
        "decrease sensitivity": {
            "action": "decrease_sensitivity",
            "desc": "Lower mouse sensitivity",
            "speech_responses": ["Reducing cursor speed, sir.", "Sensitivity lowered.", "Target sensitivity reduced."]
        },
        "open notepad": {
            "action": "open_app:notepad.exe",
            "desc": "Launch Microsoft Notepad",
            "speech_responses": ["Launching notepad, sir.", "Opening notepad, as requested."]
        },
        "open calculator": {
            "action": "open_app:calc.exe",
            "desc": "Launch Windows Calculator",
            "speech_responses": ["Opening calculator, sir.", "Calculator launched."]
        },
        "open browser": {
            "action": "open_app:start msedge",
            "desc": "Launch Edge browser",
            "speech_responses": ["Opening Microsoft Edge, sir.", "Launching web browser."]
        },
        "hello": {
            "action": "say_hello",
            "desc": "Greet the user",
            "speech_responses": ["Hello, sir. SPyRaw systems are fully functional. How can I assist you?", "At your service, sir. All core channels are stable.", "Greetings, sir. I am monitoring your hand coordinates."]
        },
        "status report": {
            "action": "say_status",
            "desc": "Report system telemetries",
            "speech_responses": ["All systems are normal. Core speed is stable.", "Running self-diagnostic. All tracking channels operational."]
        }
    }
}

class ConfigManager:
    def __init__(self, filepath="config.json"):
        self.filepath = filepath
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    loaded = json.load(f)
                    # Merge loaded to ensure all default keys exist
                    for k, v in loaded.items():
                        self.config[k] = v
            except Exception as e:
                print(f"Error loading config, using defaults: {e}")
        else:
            self.save()

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save()
