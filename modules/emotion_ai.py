import cv2
import numpy as np
import mediapipe as mp
import tensorflow as tf
from pathlib import Path

class EmotionAI:
    """
    Affective Mirror - Real-time emotion detection using MediaPipe and Mini-Xception
    
    This module:
    1. Detects faces using MediaPipe Face Detection (optimized for edge devices)
    2. Preprocesses face regions (grayscale, 48x48, normalized)
    3. Predicts emotions using Mini-Xception TFLite model
    4. Returns emotion label and confidence scores
    """
    
    # Emotion labels for FER-2013 dataset (7 emotions)
    EMOTIONS = ['Angry', "Contempt",'Disgust', 'Fear', 'Happy', 'Neutral','Sad', 'Surprise']
    
    def __init__(self, model_path='models/mini_xception.tflite'):
        """
        Initialize the Emotion AI module
        
        Args:
            model_path: Path to the Mini-Xception TFLite model
        """
        self.model_path = Path(model_path)
        self.interpreter = None
        self.keras_model = None  # Fallback for H5 model
        self.input_details = None
        self.output_details = None
        self.using_h5 = False  # Track which model type is loaded
        self.input_size = 48  # Default, will be updated from model
        
        # Initialize MediaPipe Face Detection
        # min_detection_confidence: Lower for better detection on edge devices
        # model_selection: 0 for short-range (< 2m), 1 for full-range
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=0.5,
            model_selection=0  # Short-range model (faster)
        )
        
        # Load TFLite model (or H5 as fallback)
        self._load_model()
        
        # Cache for smoothing predictions
        self.emotion_history = []
        self.history_size = 5  # Number of frames to average
        
    def _load_model(self):
        """Load the TFLite Mini-Xception model (or H5 as fallback)"""
        try:
            # Try TFLite first
            if self.model_path.exists():
                print(f"📦 Loading TFLite model from {self.model_path}...")
                self.interpreter = tf.lite.Interpreter(model_path=str(self.model_path))
                self.interpreter.allocate_tensors()
                
                # Get input and output tensors
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                
                # Get input size from model (height dimension)
                input_shape = self.input_details[0]['shape']
                self.input_size = input_shape[1]  # Assuming shape is [batch, height, width, channels]
                
                print(f"✅ TFLite model loaded successfully")
                print(f"   Input shape: {input_shape}")
                print(f"   Expected input size: {self.input_size}x{self.input_size}")
                print(f"   Output shape: {self.output_details[0]['shape']}")
                return
            
            # Fallback to H5 if TFLite doesn't exist
            h5_path = Path("models/mini_xception.h5")
            if h5_path.exists():
                print(f"⚠️  TFLite model not found, using H5 model as fallback...")
                print(f"📦 Loading H5 model from {h5_path}...")
                
                # Load Keras model without compiling
                self.keras_model = tf.keras.models.load_model(str(h5_path), compile=False)
                self.using_h5 = True
                
                # Get input size from model
                input_shape = self.keras_model.input_shape
                self.input_size = input_shape[1]  # Assuming shape is (None, height, width, channels)
                
                print(f"✅ H5 model loaded successfully")
                print(f"   Input shape: {input_shape}")
                print(f"   Expected input size: {self.input_size}x{self.input_size}")
                print(f"   Output shape: {self.keras_model.output_shape}")
                print(f"   💡 Tip: Run 'python convert_model.py' to create TFLite model for better performance")
                return
            
            # No model found
            print(f"⚠️  No model found!")
            print(f"   TFLite: {self.model_path} - Not found")
            print(f"   H5: {h5_path} - Not found")
            print(f"   Please run 'python download_model.py' to download the model")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            import traceback
            traceback.print_exc()
            self.interpreter = None
            self.keras_model = None
    
    def detect_face(self, frame):
        
        if frame is None or frame.size == 0:
            return None, None
        
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect faces
        results = self.face_detection.process(rgb_frame)
        
        if not results.detections:
            return None, None
        
        # Get the first (most confident) face detection
        detection = results.detections[0]
        
        # Get bounding box
        bboxC = detection.location_data.relative_bounding_box
        h, w, _ = frame.shape
        
        # Convert relative coordinates to absolute pixels
        x = int(bboxC.xmin * w)
        y = int(bboxC.ymin * h)
        width = int(bboxC.width * w)
        height = int(bboxC.height * h)
        
        # Add padding (10% on each side) for better emotion detection
        padding = int(0.1 * max(width, height))
        x = max(0, x - padding)
        y = max(0, y - padding)
        width = min(w - x, width + 2 * padding)
        height = min(h - y, height + 2 * padding)
        
        # Extract face ROI
        face_roi = frame[y:y+height, x:x+width]
        
        return face_roi, (x, y, width, height)

    def preprocess_face(self, face_roi):
        """Preprocess face for Mini‑Xception model.

        Steps:
        1. Convert to grayscale.
        2. Resize to model's expected input size (dynamic based on loaded model).
        3. Keep pixel values as uint8 (0‑255) for integer‑quantized TFLite model.
        4. Expand dimensions to (1, H, W, 1).
        """
        if face_roi is None or face_roi.size == 0:
            return None
        gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        target = (self.input_size, self.input_size)
        resized = cv2.resize(gray, target, interpolation=cv2.INTER_AREA)
        preprocessed = np.expand_dims(resized, axis=0)   # (1, H, W)
        preprocessed = np.expand_dims(preprocessed, axis=-1)  # (1, H, W, 1)
        return preprocessed.astype(np.uint8)

    def predict_emotion(self, preprocessed_face):
        """Run inference and return (emotion, confidence, probabilities)."""
        if preprocessed_face is None:
            return "Neutral", 0.0, {}
        if self.interpreter is None and self.keras_model is None:
            return "Neutral", 0.0, {}
        try:
            if self.using_h5 and self.keras_model is not None:
                preds = self.keras_model.predict(preprocessed_face, verbose=0)[0]
            else:
                self.interpreter.set_tensor(self.input_details[0]['index'], preprocessed_face.astype(np.uint8))
                self.interpreter.invoke()
                preds = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
            idx = int(np.argmax(preds))
            emotion = self.EMOTIONS[idx]
            confidence = float(preds[idx])
            probabilities = {self.EMOTIONS[i]: float(preds[i]) for i in range(len(self.EMOTIONS))}
            return emotion, confidence, probabilities
        except Exception as e:
            print(f"❌ Error during prediction: {e}")
            import traceback
            traceback.print_exc()
            return "Neutral", 0.0, {}

    def smooth_prediction(self, emotion, confidence):
        """Smooth predictions over recent frames to reduce jitter."""
        self.emotion_history.append((emotion, confidence))
        if len(self.emotion_history) > self.history_size:
            self.emotion_history.pop(0)
        counts = {}
        total_conf = 0.0
        for emo, conf in self.emotion_history:
            counts[emo] = counts.get(emo, 0) + 1
            total_conf += conf
        smoothed_emotion = max(counts, key=counts.get)
        smoothed_confidence = total_conf / len(self.emotion_history)
        return smoothed_emotion, smoothed_confidence
    
    def predict(self, frame):
        
        # Detect face
        face_roi, bbox = self.detect_face(frame)
        
        if face_roi is None:
            return {
                'emotion': 'No Face',
                'confidence': 0.0,
                'probabilities': {},
                'bbox': None,
                'face_detected': False
            }
        
        # Preprocess face
        preprocessed = self.preprocess_face(face_roi)
        
        # Predict emotion
        emotion, confidence, probabilities = self.predict_emotion(preprocessed)
        
        # Smooth prediction
        smoothed_emotion, smoothed_confidence = self.smooth_prediction(emotion, confidence)
        
        return {
            'emotion': smoothed_emotion,
            'confidence': smoothed_confidence,
            'probabilities': probabilities,
            'bbox': bbox,
            'face_detected': True
        }
    
    def draw_results(self, frame, result):
        """
        Draw emotion prediction results on frame
        
        Args:
            frame: BGR image to draw on
            result: Prediction result dictionary from predict()
            
        Returns:
            annotated_frame: Frame with annotations
        """
        annotated_frame = frame.copy()
        
        if not result['face_detected']:
            # Draw "No Face Detected" message
            cv2.putText(
                annotated_frame,
                "No Face Detected",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2
            )
            return annotated_frame
        
        # Draw bounding box
        bbox = result['bbox']
        if bbox:
            x, y, w, h = bbox
            cv2.rectangle(annotated_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Draw emotion label and confidence
        emotion = result['emotion']
        confidence = result['confidence']
        label = f"{emotion}: {confidence:.2%}"
        
        # Background for text
        (text_width, text_height), _ = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2
        )
        cv2.rectangle(
            annotated_frame,
            (10, 10),
            (20 + text_width, 40 + text_height),
            (0, 255, 0),
            -1
        )
        
        # Text
        cv2.putText(
            annotated_frame,
            label,
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 0),
            2
        )
        
        return annotated_frame
    
    def cleanup(self):
        """Release resources"""
        if self.face_detection:
            self.face_detection.close()
