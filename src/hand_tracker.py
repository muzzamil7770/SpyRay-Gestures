import cv2
import mediapipe as mp
import numpy as np
import time
import math
import os
from PySide6.QtCore import QThread, Signal
from src.config import ConfigManager
from src.mouse_controller import WinMouseController
from src.ai_classifier import HandGestureMLP, normalize_landmarks, GestureDatasetManager

class HandTrackerThread(QThread):
    # Signals to communicate with the GUI
    frame_ready = Signal(np.ndarray, list, dict)  # frame (RGB), landmarks list, status_info
    log_message = Signal(str)
    fps_updated = Signal(float)
    gesture_detected = Signal(str, str)  # hand_label ("Left"/"Right"), gesture_name

    def __init__(self, config_manager: ConfigManager, mouse_controller: WinMouseController):
        super().__init__()
        self.config = config_manager
        self.mouse = mouse_controller
        self.running = False
        
        # Check which MediaPipe API is available
        self.use_tasks_api = not hasattr(mp, 'solutions')
        
        # MediaPipe Hands setup
        self.hands = None
        self.mp_hands = None
        self.mp_draw = None
        self.mp_drawing_styles = None
        
        if not self.use_tasks_api:
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles

        # AI Model setup
        self.model = HandGestureMLP()
        self.dataset_manager = GestureDatasetManager()
        self.label_to_idx = {"PALM": 0, "PINCH": 1, "TWO_FINGERS": 2, "FIST": 3, "SCROLL": 4}
        self.idx_to_label = {v: k for k, v in self.label_to_idx.items()}
        self.model_loaded = False
        self.load_model()
        
        # Cursor smoothing variables
        self.prev_x, self.prev_y = 0.0, 0.0
        self.smooth_x, self.smooth_y = 0.0, 0.0
        self.has_prev_pos = False
        
        # Deadzone tremor filter and click-lock timestamp
        self.click_lock_until = 0.0
        
        # Gesture state history (for click/drag stabilization - temporal hysteresis)
        self.gesture_history = {"Left": [], "Right": []}
        self.history_len = 3  # Frames required to confirm a gesture transition
        
        # State variables for mouse control
        self.last_pinch_state = False
        self.pinch_start_time = 0.0
        self.drag_active = False
        self.right_click_cooldown = 0.0
        self.scroll_anchor_y = None
        
        # Calibration / scaling variables
        self.screen_width = self.mouse.screen_width
        self.screen_height = self.mouse.screen_height

        # Data collection variables
        self.collecting_data = False
        self.collect_label = None
        self.collected_samples_count = 0
        self.collect_target_count = 100

    def load_model(self):
        """Attempts to load the neural network model."""
        if self.model.load("gesture_model.json"):
            self.model_loaded = True
            print("AI Gesture Classification model loaded successfully.")
        else:
            self.model_loaded = False
            print("AI model not found. Using Rule-Based gesture tracking.")

    def trigger_model_training(self):
        """Train the MLP neural net on current dataset."""
        X, y = self.dataset_manager.get_training_data(self.label_to_idx)
        if X is None or len(X) == 0:
            self.log_message.emit("Training failed: Dataset is empty.")
            return False
            
        self.log_message.emit(f"Starting training on {len(X)} samples...")
        self.model.reset_weights()
        
        epochs = 150
        batch_size = 8
        num_samples = len(X)
        
        for epoch in range(epochs):
            indices = np.arange(num_samples)
            np.random.shuffle(indices)
            X_shuffled = X[indices]
            y_shuffled = y[indices]
            
            for i in range(0, num_samples, batch_size):
                xb = X_shuffled[i : i + batch_size]
                yb = y_shuffled[i : i + batch_size]
                self.model.train_step(xb, yb)
                
            if epoch % 30 == 0 or epoch == epochs - 1:
                preds, _ = self.model.predict(X)
                targets = np.argmax(y, axis=1)
                acc = np.mean(preds == targets) * 100
                self.log_message.emit(f"Epoch {epoch}/{epochs} - Accuracy: {acc:.1f}%")
                
        self.model.save("gesture_model.json")
        self.model_loaded = True
        self.log_message.emit("AI Model trained and saved as 'gesture_model.json' successfully!")
        
        tflite_path = "gesture_model.tflite"
        if self.model.export_to_tflite_if_possible(tflite_path):
            self.log_message.emit(f"Model also exported to TFLite format at '{tflite_path}'.")
            
        return True

    def start_data_collection(self, label_name, count=100):
        self.collect_label = label_name
        self.collect_target_count = count
        self.collected_samples_count = 0
        self.collecting_data = True
        self.log_message.emit(f"Starting collection for gesture '{label_name}' (Target: {count} samples). Move hand slowly.")

    def run(self):
        self.running = True
        camera_idx = int(self.config.get("camera_index", 0))
        cap = cv2.VideoCapture(camera_idx)
        
        # Set buffer size to minimum for low-latency
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not cap.isOpened():
            self.log_message.emit("CRITICAL: Could not open web camera. Check camera index.")
            self.running = False
            return

        if self.use_tasks_api:
            if not os.path.exists("hand_landmarker.task"):
                self.log_message.emit("Model file hand_landmarker.task not found! Attempting download...")
                try:
                    import urllib.request
                    url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                    urllib.request.urlretrieve(url, "hand_landmarker.task")
                    self.log_message.emit("Model downloaded successfully!")
                except Exception as e:
                    self.log_message.emit(f"CRITICAL: Failed to download model file: {e}")
                    self.running = False
                    cap.release()
                    return
            
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
            options = vision.HandLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.VIDEO,
                num_hands=2,
                min_hand_detection_confidence=0.7,
                min_hand_presence_confidence=0.7,
                min_tracking_confidence=0.7
            )
            self.hands = vision.HandLandmarker.create_from_options(options)
        else:
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=2,
                model_complexity=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.7
            )

        fps_prev_time = time.time()
        fps_frame_counter = 0
        self.log_message.emit("Hand Gesture tracking thread started successfully.")

        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            frame = cv2.flip(frame, 1)
            h, w, c = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            multi_hand_landmarks = []
            multi_handedness = []
            
            if self.use_tasks_api:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                timestamp_ms = int(time.time() * 1000)
                results = self.hands.detect_for_video(mp_image, timestamp_ms)
                multi_hand_landmarks = results.hand_landmarks
                for hand_cats in results.handedness:
                    if hand_cats:
                        multi_handedness.append(hand_cats[0])
            else:
                results = self.hands.process(rgb_frame)
                if results.multi_hand_landmarks and results.multi_handedness:
                    multi_hand_landmarks = results.multi_hand_landmarks
                    multi_handedness = results.multi_handedness

            status_info = {
                "hands_detected": 0,
                "right_hand_gesture": "NONE",
                "left_hand_gesture": "NONE",
                "cursor_pos": (0, 0),
                "fps": 0.0,
                "ai_mode": self.config.get("use_ai_classification", False) and self.model_loaded
            }

            detected_landmarks = []
            
            if multi_hand_landmarks and multi_handedness:
                status_info["hands_detected"] = len(multi_hand_landmarks)
                
                for hand_landmarks, handedness in zip(multi_hand_landmarks, multi_handedness):
                    if hasattr(handedness, 'classification'):
                        hand_label = handedness.classification[0].label
                    else:
                        hand_label = handedness.category_name
                        
                    hand_label = "Left" if hand_label == "Right" else "Right"
                    landmarks_list = hand_landmarks.landmark if hasattr(hand_landmarks, 'landmark') else hand_landmarks
                    
                    norm_features = normalize_landmarks(landmarks_list)
                    detected_landmarks.append((landmarks_list, hand_label))

                    detected_gesture = "NEUTRAL"
                    
                    if self.collecting_data and self.collect_label and hand_label == "Right":
                        self.dataset_manager.add_sample(self.collect_label, norm_features)
                        self.collected_samples_count += 1
                        if self.collected_samples_count >= self.collect_target_count:
                            self.collecting_data = False
                            self.log_message.emit(f"Finished collecting data for '{self.collect_label}'. Ready to train!")
                        else:
                            if self.collected_samples_count % 10 == 0:
                                self.log_message.emit(f"Recorded {self.collected_samples_count}/{self.collect_target_count} samples for '{self.collect_label}'...")

                    if self.config.get("use_ai_classification", False) and self.model_loaded:
                        preds, confs = self.model.predict(norm_features)
                        pred_idx = preds[0]
                        confidence = confs[0]
                        if confidence > 0.65:
                            detected_gesture = self.idx_to_label.get(pred_idx, "NEUTRAL")
                    else:
                        detected_gesture = self.classify_rule_based(landmarks_list)
                    
                    self.gesture_history[hand_label].append(detected_gesture)
                    if len(self.gesture_history[hand_label]) > self.history_len:
                        self.gesture_history[hand_label].pop(0)
                        
                    stable_gesture = max(set(self.gesture_history[hand_label]), key=self.gesture_history[hand_label].count)
                    
                    if hand_label == "Right":
                        status_info["right_hand_gesture"] = stable_gesture
                    else:
                        status_info["left_hand_gesture"] = stable_gesture
                        
                    self.gesture_detected.emit(hand_label, stable_gesture)

                    if self.config.get("multi_hand_enabled", True):
                        if hand_label == "Left" and self.config.get("left_hand_action") == "SCROLL":
                            self.handle_scrolling(landmarks_list)
                        elif hand_label == "Right" and self.config.get("right_hand_action") == "CURSOR":
                            self.handle_cursor_control(landmarks_list, stable_gesture)
                    else:
                        if hand_label == "Right":
                            self.handle_cursor_control(landmarks_list, stable_gesture)

            self.draw_hologram_overlays(frame, multi_hand_landmarks, multi_handedness)

            fps_frame_counter += 1
            now = time.time()
            elapsed = now - fps_prev_time
            if elapsed >= 1.0:
                fps = fps_frame_counter / elapsed
                self.fps_updated.emit(fps)
                fps_prev_time = now
                fps_frame_counter = 0
                status_info["fps"] = round(fps, 1)
            else:
                status_info["fps"] = round(fps_frame_counter / max(0.001, elapsed), 1)

            status_info["cursor_pos"] = self.mouse.get_position()
            self.frame_ready.emit(frame, detected_landmarks, status_info)

            fps_cap = self.config.get("fps_cap", 30)
            time.sleep(max(0.003, 1.0 / fps_cap - 0.005))

        cap.release()
        if self.hands:
            self.hands.close()
        self.mouse.end_drag()

    def classify_rule_based(self, lms):
        hand_scale = math.hypot(lms[9].x - lms[0].x, lms[9].y - lms[0].y)
        if hand_scale < 1e-6:
            hand_scale = 1e-6
            
        pinch_dist = math.hypot(lms[8].x - lms[4].x, lms[8].y - lms[4].y) / hand_scale
        
        tips = [8, 12, 16, 20]
        folded = []
        for tip in tips:
            dist = math.hypot(lms[tip].x - lms[0].x, lms[tip].y - lms[0].y) / hand_scale
            folded.append(dist < 1.35)
            
        if all(folded):
            return "FIST"
            
        if pinch_dist < 0.28:
            return "PINCH"
            
        if not folded[0] and not folded[1] and folded[2] and folded[3]:
            return "TWO_FINGERS"
            
        if not folded[0] and not folded[1] and not folded[2] and folded[3]:
            return "SCROLL"
            
        return "PALM"

    def handle_cursor_control(self, lms, gesture):
        """
        Ultra-responsive speed-sensitive cursor control.
        Includes deadzone tremor filters and 120ms click drift cursor lock.
        """
        mode = self.config.get("mode", "precision")
        sensitivity_x = self.config.get("sensitivity_x", 1.5)
        sensitivity_y = self.config.get("sensitivity_y", 1.5)
        smoothing_factor = self.config.get("smoothing_factor", 0.25)
        
        if mode == "precision":
            sensitivity_x *= self.config.get("precision_multiplier", 0.4)
            sensitivity_y *= self.config.get("precision_multiplier", 0.4)
            smoothing_factor *= 0.65  # Muted reactivity for fine controls
            
        anchor_x = lms[5].x
        anchor_y = lms[5].y
        
        # Camera Active Zone
        x_min, x_max = 0.28, 0.72
        y_min, y_max = 0.28, 0.72
        
        norm_x = max(0.0, min(1.0, (anchor_x - x_min) / (x_max - x_min)))
        norm_y = max(0.0, min(1.0, (anchor_y - y_min) / (y_max - y_min)))
        
        target_x = norm_x * self.screen_width * sensitivity_x
        target_y = norm_y * self.screen_height * sensitivity_y
        
        center_offset_x = (self.screen_width * (sensitivity_x - 1.0)) / 2.0
        center_offset_y = (self.screen_height * (sensitivity_y - 1.0)) / 2.0
        target_x -= center_offset_x
        target_y -= center_offset_y
        
        if not self.has_prev_pos:
            self.smooth_x = target_x
            self.smooth_y = target_y
            self.has_prev_pos = True
        else:
            # 1. Jitter Deadzone Tremor Filter
            displacement = math.hypot(target_x - self.smooth_x, target_y - self.smooth_y)
            if displacement < 2.2:
                # Discard micro hand vibrations entirely when steady
                target_x = self.smooth_x
                target_y = self.smooth_y
                displacement = 0.0
                
            # 2. Adaptive Velocity Smoothing
            # High speed -> 0ms lag tracking (alpha approaches 0.88)
            # Hovering -> highly dampened smoothing (alpha scales down to smoothing_factor)
            speed_factor = min(1.0, displacement / 120.0)
            adaptive_alpha = smoothing_factor * (1.0 - speed_factor) + 0.88 * speed_factor
            
            self.smooth_x = self.smooth_x * (1 - adaptive_alpha) + target_x * adaptive_alpha
            self.smooth_y = self.smooth_y * (1 - adaptive_alpha) + target_y * adaptive_alpha
            
        # 3. Click Drift Cursor Lock Hysteresis
        # Freezes mouse coordinate updates briefly during click execution to keep cursors rock-solid
        if time.time() >= self.click_lock_until:
            self.mouse.move_to(self.smooth_x, self.smooth_y)
        
        # Handle Action mappings
        action = self.config.get("gesture_mappings", {}).get(gesture, "NONE")
        
        if action == "CLICK":
            if not self.last_pinch_state:
                self.mouse.click()
                self.pinch_start_time = time.time()
                self.last_pinch_state = True
                # Lock mouse coordinates for 120ms to prevent click coordinate shifting
                self.click_lock_until = time.time() + 0.12
        elif action == "DRAG_AND_DROP" or gesture == "FIST":
            self.mouse.start_drag()
            self.drag_active = True
        else:
            if self.last_pinch_state:
                self.last_pinch_state = False
            if self.drag_active:
                self.mouse.end_drag()
                self.drag_active = False

        if action == "RIGHT_CLICK":
            now = time.time()
            if now - self.right_click_cooldown > 0.8:
                self.mouse.right_click()
                self.right_click_cooldown = now

    def handle_scrolling(self, lms):
        index_tip_y = lms[8].y
        wrist_y = lms[0].y
        finger_length = wrist_y - index_tip_y
        
        if self.scroll_anchor_y is None:
            self.scroll_anchor_y = finger_length
        else:
            diff = finger_length - self.scroll_anchor_y
            if abs(diff) > 0.04:
                scroll_amount = diff * 6.0 * self.config.get("scroll_speed", 1.0)
                self.mouse.scroll(scroll_amount)
                self.scroll_anchor_y = self.scroll_anchor_y * 0.85 + finger_length * 0.15
            else:
                self.scroll_anchor_y = self.scroll_anchor_y * 0.94 + finger_length * 0.06

    HAND_CONNECTIONS = [
        (0,1),(1,2),(2,3),(3,4),
        (0,5),(5,6),(6,7),(7,8),
        (5,9),(9,10),(10,11),(11,12),
        (9,13),(13,14),(14,15),(15,16),
        (13,17),(17,18),(18,19),(19,20),
        (0,17)
    ]

    def draw_hologram_overlays(self, frame, multi_hand_landmarks, multi_handedness):
        h, w, c = frame.shape
        
        # Draw background grids
        cv2.line(frame, (int(w * 0.28), 0), (int(w * 0.28), h), (255, 240, 0), 1)
        cv2.line(frame, (int(w * 0.72), 0), (int(w * 0.72), h), (255, 240, 0), 1)
        cv2.line(frame, (0, int(h * 0.28)), (w, int(h * 0.28)), (255, 240, 0), 1)
        cv2.line(frame, (0, int(h * 0.72)), (w, int(h * 0.72)), (255, 240, 0), 1)
        
        color_neon = (255, 240, 0)
        len_corner = 20
        cv2.line(frame, (int(w*0.28), int(h*0.28)), (int(w*0.28) + len_corner, int(h*0.28)), color_neon, 2)
        cv2.line(frame, (int(w*0.28), int(h*0.28)), (int(w*0.28), int(h*0.28) + len_corner), color_neon, 2)
        cv2.line(frame, (int(w*0.72), int(h*0.28)), (int(w*0.72) - len_corner, int(h*0.28)), color_neon, 2)
        cv2.line(frame, (int(w*0.72), int(h*0.28)), (int(w*0.72), int(h*0.28) + len_corner), color_neon, 2)
        cv2.line(frame, (int(w*0.28), int(h*0.72)), (int(w*0.28) + len_corner, int(h*0.72)), color_neon, 2)
        cv2.line(frame, (int(w*0.28), int(h*0.72)), (int(w*0.28), int(h*0.72) - len_corner), color_neon, 2)
        cv2.line(frame, (int(w*0.72), int(h*0.72)), (int(w*0.72) - len_corner, int(h*0.72)), color_neon, 2)
        cv2.line(frame, (int(w*0.72), int(h*0.72)), (int(w*0.72), int(h*0.72) - len_corner), color_neon, 2)
        
        sub_img = frame[int(h*0.28):int(h*0.72), int(w*0.28):int(w*0.72)]
        white_rect = np.zeros(sub_img.shape, dtype=np.uint8)
        white_rect[:] = [255, 240, 0]
        res = cv2.addWeighted(sub_img, 0.90, white_rect, 0.10, 0)
        frame[int(h*0.28):int(h*0.72), int(w*0.28):int(w*0.72)] = res

        if not multi_hand_landmarks:
            return
            
        for hand_landmarks, handedness in zip(multi_hand_landmarks, multi_handedness):
            if hasattr(handedness, 'classification'):
                hand_label = handedness.classification[0].label
            else:
                hand_label = handedness.category_name
            hand_label = "Left" if hand_label == "Right" else "Right"
            
            node_color = (255, 240, 0) if hand_label == "Right" else (255, 0, 127)
            conn_color = (200, 180, 0) if hand_label == "Right" else (200, 0, 100)
            lms = hand_landmarks.landmark if hasattr(hand_landmarks, 'landmark') else hand_landmarks

            for start_idx, end_idx in self.HAND_CONNECTIONS:
                if start_idx < len(lms) and end_idx < len(lms):
                    pt1 = (int(lms[start_idx].x * w), int(lms[start_idx].y * h))
                    pt2 = (int(lms[end_idx].x * w), int(lms[end_idx].y * h))
                    cv2.line(frame, pt1, pt2, conn_color, 2)
            
            for idx, lm in enumerate(lms):
                cx, cy = int(lm.x * w), int(lm.y * h)
                if idx in [0, 4, 8, 12, 16, 20]:
                    cv2.circle(frame, (cx, cy), 6, node_color, -1)
                    cv2.circle(frame, (cx, cy), 9, node_color, 1)
                else:
                    cv2.circle(frame, (cx, cy), 4, node_color, -1)
                    
                if idx == 5 and hand_label == "Right":
                    cv2.circle(frame, (cx, cy), 12, (0, 0, 255), 2)
                    cv2.line(frame, (cx - 16, cy), (cx + 16, cy), (0, 0, 255), 1)
                    cv2.line(frame, (cx, cy - 16), (cx, cy + 16), (0, 0, 255), 1)
