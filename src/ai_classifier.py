import numpy as np
import json
import os

class HandGestureMLP:
    def __init__(self, layer_sizes=[63, 64, 32, 5], learning_rate=0.01):
        """
        A lightweight Neural Network (MLP) built from scratch in NumPy.
        Input size: 63 (21 landmarks x 3 coordinates: x, y, z)
        Output size: number of gesture classes (e.g., 5: Neutral, Pinch, Two Fingers, Fist, Scroll)
        """
        self.layer_sizes = layer_sizes
        self.lr = learning_rate
        self.weights = []
        self.biases = []
        self.reset_weights()

    def reset_weights(self):
        self.weights = []
        self.biases = []
        # He (Kaiming) initialization for ReLU, Xavier for Softmax
        for i in range(len(self.layer_sizes) - 1):
            n_in = self.layer_sizes[i]
            n_out = self.layer_sizes[i+1]
            limit = np.sqrt(2.0 / n_in)
            self.weights.append(np.random.randn(n_in, n_out) * limit)
            self.biases.append(np.zeros((1, n_out)))

    def relu(self, x):
        return np.maximum(0, x)

    def relu_derivative(self, x):
        return (x > 0).astype(float)

    def softmax(self, x):
        # Stable softmax
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def forward(self, X):
        """Forward pass. Returns activation of all layers."""
        activations = [X]
        zs = []
        
        a = X
        # Hidden layers with ReLU
        for i in range(len(self.weights) - 1):
            z = np.dot(a, self.weights[i]) + self.biases[i]
            zs.append(z)
            a = self.relu(z)
            activations.append(a)
            
        # Output layer with Softmax
        z_out = np.dot(a, self.weights[-1]) + self.biases[-1]
        zs.append(z_out)
        a_out = self.softmax(z_out)
        activations.append(a_out)
        
        return activations, zs

    def predict(self, X):
        """X can be shape (63,) or (N, 63). Returns predicted class index and confidence."""
        if X.ndim == 1:
            X = X.reshape(1, -1)
        activations, _ = self.forward(X)
        probs = activations[-1]
        preds = np.argmax(probs, axis=1)
        confidences = np.max(probs, axis=1)
        return preds, confidences

    def train_step(self, X, y_onehot):
        """Perform one backpropagation training step (batch gradient descent)."""
        m = X.shape[0]
        activations, zs = self.forward(X)
        
        # Output error
        a_out = activations[-1]
        d_out = (a_out - y_onehot) / m  # derivative of cross-entropy with softmax
        
        # Gradients list
        dw = [None] * len(self.weights)
        db = [None] * len(self.biases)
        
        # Backpropagate error
        d = d_out
        for i in reversed(range(len(self.weights))):
            dw[i] = np.dot(activations[i].T, d)
            db[i] = np.sum(d, axis=0, keepdims=True)
            if i > 0:
                # Backprop error to previous layer
                d = np.dot(d, self.weights[i].T) * self.relu_derivative(zs[i-1])
                
        # Update weights and biases with momentum/simple SGD
        for i in range(len(self.weights)):
            self.weights[i] -= self.lr * dw[i]
            self.biases[i] -= self.lr * db[i]

    def save(self, filepath):
        """Save weights and metadata to JSON."""
        data = {
            "layer_sizes": self.layer_sizes,
            "weights": [w.tolist() for w in self.weights],
            "biases": [b.tolist() for b in self.biases]
        }
        with open(filepath, "w") as f:
            json.dump(data, f)

    def load(self, filepath):
        """Load weights from JSON."""
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            self.layer_sizes = data["layer_sizes"]
            self.weights = [np.array(w) for w in data["weights"]]
            self.biases = [np.array(b) for b in data["biases"]]
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def export_to_tflite_if_possible(self, tflite_filepath):
        """
        Attempts to build a Keras model from current weights,
        converts it, and saves it as a TensorFlow Lite model.
        Returns True on success, False if tensorflow is not installed.
        """
        try:
            import tensorflow as tf
            
            # Recreate MLP structure in Keras
            model = tf.keras.Sequential()
            model.add(tf.keras.layers.Input(shape=(self.layer_sizes[0],)))
            for size in self.layer_sizes[1:-1]:
                model.add(tf.keras.layers.Dense(size, activation='relu'))
            model.add(tf.keras.layers.Dense(self.layer_sizes[-1], activation='softmax'))
            
            # Build and copy weights
            model.build((None, self.layer_sizes[0]))
            
            keras_weights = []
            for w, b in zip(self.weights, self.biases):
                keras_weights.append(w.astype(np.float32))
                keras_weights.append(b.squeeze().astype(np.float32))
            model.set_weights(keras_weights)
            
            # Convert to TFLite
            converter = tf.lite.TFLiteConverter.from_keras_model(model)
            tflite_model = converter.convert()
            
            with open(tflite_filepath, 'wb') as f:
                f.write(tflite_model)
            return True
        except Exception as e:
            print(f"Failed to export to TFLite (TensorFlow likely missing or version mismatch): {e}")
            return False


def normalize_landmarks(landmarks):
    """
    Standardize 21 MediaPipe hand landmarks to make them translation & scale invariant.
    landmarks: shape (21, 3) or list of landmarks with x, y, z
    Returns: flattened shape (63,) normalized coordinates.
    """
    if isinstance(landmarks, list):
        # Convert landmarks list of objects to numpy array
        coords = np.array([[lm.x, lm.y, lm.z] for lm in landmarks])
    else:
        coords = np.array(landmarks)
        
    # 1. Translation Invariance: Shift wrist (landmark 0) to origin
    wrist = coords[0]
    shifted_coords = coords - wrist
    
    # 2. Scale Invariance: Divide by the Euclidean distance between wrist (0) and middle finger knuckle (9)
    dist = np.linalg.norm(shifted_coords[9])
    if dist < 1e-6:
        dist = 1e-6
    scaled_coords = shifted_coords / dist
    
    # 3. Flatten to 63-dimensional feature vector
    return scaled_coords.flatten()


class GestureDatasetManager:
    def __init__(self, filepath="gesture_dataset.json"):
        self.filepath = filepath
        self.dataset = {}  # key: label_name, value: list of normalized landmark vectors
        self.load()

    def add_sample(self, label_name, normalized_lm):
        """Append a normalized feature vector to the dataset."""
        if label_name not in self.dataset:
            self.dataset[label_name] = []
        self.dataset[label_name].append(normalized_lm.tolist())
        self.save()

    def clear_class(self, label_name):
        """Remove all samples for a specific gesture class."""
        if label_name in self.dataset:
            del self.dataset[label_name]
            self.save()

    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    self.dataset = json.load(f)
            except Exception as e:
                print(f"Error loading dataset: {e}")
                self.dataset = {}

    def save(self):
        try:
            with open(self.filepath, "w") as f:
                json.dump(self.dataset, f)
        except Exception as e:
            print(f"Error saving dataset: {e}")

    def get_stats(self):
        return {k: len(v) for k, v in self.dataset.items()}

    def get_training_data(self, label_to_idx):
        """
        Prepare dataset for model training.
        Returns:
            X: np.ndarray shape (N, 63)
            y_onehot: np.ndarray shape (N, num_classes)
        """
        X = []
        y = []
        num_classes = len(label_to_idx)
        
        for label_name, samples in self.dataset.items():
            if label_name in label_to_idx:
                idx = label_to_idx[label_name]
                for sample in samples:
                    X.append(sample)
                    y.append(idx)
                    
        if not X:
            return None, None
            
        X = np.array(X)
        y = np.array(y)
        
        # One-hot encoding
        y_onehot = np.zeros((y.size, num_classes))
        y_onehot[np.arange(y.size), y] = 1
        
        return X, y_onehot
