from fer.fer import FER
import cv2
import numpy as np
from collections import deque

class EmotionClassifier:
    def __init__(self, use_mtcnn=True, smoothing_window=5, confidence_threshold=0.3):
        """
        Initialize the emotion classifier with improved settings.
        
        Args:
            use_mtcnn: Use MTCNN for better face detection (slower but more accurate)
            smoothing_window: Number of frames to average emotions over (reduces jitter)
            confidence_threshold: Minimum confidence to accept a classification
        """
        # Use MTCNN for better face detection accuracy
        # MTCNN is slower but much more accurate than Haarcascade
        print(f"Initializing FER with MTCNN={use_mtcnn}...")
        self.detector = FER(mtcnn=use_mtcnn)
        
        self.confidence_threshold = confidence_threshold
        self.smoothing_window = smoothing_window
        
        # Emotion history for temporal smoothing
        self.emotion_history = deque(maxlen=smoothing_window)
        
        # Weighted mapping of emotions to study states
        # Higher weight = more influence on final state
        self.emotion_weights = {
            'neutral': {'state': 'Focused', 'weight': 1.0},
            'happy': {'state': 'Focused', 'weight': 1.2},  # Happy is good for focus
            'angry': {'state': 'Stressed', 'weight': 1.5},  # Strong stress indicator
            'disgust': {'state': 'Stressed', 'weight': 1.2},
            'fear': {'state': 'Stressed', 'weight': 1.3},
            'sad': {'state': 'Bored', 'weight': 1.4},  # Often indicates fatigue
            'surprise': {'state': 'Distracted', 'weight': 0.8}  # Less reliable
        }
        
        # State priority (higher = more concerning, triggers action sooner)
        self.state_priority = {
            'Stressed': 3,
            'Bored': 2,
            'Distracted': 1,
            'Focused': 0
        }
        
        # Face tracking
        self.last_box = None
        self.no_face_count = 0
        self.max_no_face_frames = 3  # Quickly detect no face (3 frames ~0.3 sec)
        
    def _preprocess_frame(self, frame):
        """Preprocess frame for better detection."""
        # Apply slight Gaussian blur to reduce noise
        frame = cv2.GaussianBlur(frame, (3, 3), 0)
        
        # Enhance contrast using CLAHE (improves detection in poor lighting)
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def _check_face_quality(self, frame, box):
        """Check if detected face has sufficient quality."""
        if box is None:
            return False, "No face"
        
        x, y, w, h = box
        
        # Check face size (too small = unreliable)
        min_face_size = 60
        if w < min_face_size or h < min_face_size:
            return False, "Face too small"
        
        # Extract face region
        face_region = frame[max(0, y):min(frame.shape[0], y+h), 
                           max(0, x):min(frame.shape[1], x+w)]
        
        if face_region.size == 0:
            return False, "Invalid region"
        
        # Check blur using Laplacian variance
        gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        if blur_score < 50:  # Too blurry
            return False, "Face too blurry"
        
        return True, "OK"
    
    def _smooth_emotions(self, current_emotions):
        """Apply temporal smoothing to reduce jitter."""
        if current_emotions is None:
            return None
        
        self.emotion_history.append(current_emotions)
        
        if len(self.emotion_history) < 2:
            return current_emotions
        
        # Average emotions over history window
        smoothed = {}
        for emotion in current_emotions.keys():
            values = [h.get(emotion, 0) for h in self.emotion_history]
            # Use weighted average (recent frames have more weight)
            weights = np.linspace(0.5, 1.0, len(values))
            smoothed[emotion] = np.average(values, weights=weights)
        
        return smoothed
    
    def _calculate_study_state(self, emotions):
        """Calculate study state using weighted scoring."""
        if emotions is None:
            return "No Face Detected"
        
        # Calculate weighted scores for each state
        state_scores = {'Focused': 0, 'Stressed': 0, 'Bored': 0, 'Distracted': 0}
        
        for emotion, confidence in emotions.items():
            if emotion in self.emotion_weights:
                state = self.emotion_weights[emotion]['state']
                weight = self.emotion_weights[emotion]['weight']
                state_scores[state] += confidence * weight
        
        # Find dominant state
        max_state = max(state_scores, key=state_scores.get)
        max_score = state_scores[max_state]
        
        # Apply confidence threshold
        if max_score < self.confidence_threshold:
            return "Uncertain"
        
        # If scores are close, prefer more concerning state
        for state in ['Stressed', 'Bored', 'Distracted']:
            if state != max_state and state_scores[state] > max_score * 0.8:
                # Close competition - use priority
                if self.state_priority[state] > self.state_priority[max_state]:
                    max_state = state
        
        return max_state
    
    def analyze_frame(self, frame):
        """
        Analyzes a single BGR frame with improved detection.
        Returns box, raw emotions, and study state.
        """
        # Preprocess for better detection
        processed_frame = self._preprocess_frame(frame)
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
        
        # Detect emotions
        result = self.detector.detect_emotions(rgb_frame)
        
        if not result:
            self.no_face_count += 1
            if self.no_face_count > self.max_no_face_frames:
                self.emotion_history.clear()
                return self.last_box, None, "No Face Detected"
            # Return last known state briefly
            return self.last_box, None, "No Face Detected"
        
        self.no_face_count = 0
        
        # Get the largest/closest face if multiple detected
        if len(result) > 1:
            result = sorted(result, key=lambda x: x['box'][2] * x['box'][3], reverse=True)
        
        face = result[0]
        emotions = face['emotions']
        box = tuple(face['box'])  # Ensure it's a tuple
        
        # Validate face quality
        quality_ok, quality_msg = self._check_face_quality(frame, box)
        if not quality_ok:
            return box, emotions, f"Low Quality: {quality_msg}"
        
        self.last_box = box
        
        # Apply temporal smoothing
        smoothed_emotions = self._smooth_emotions(emotions)
        
        # Calculate study state with weighted scoring
        study_state = self._calculate_study_state(smoothed_emotions)
        
        return box, smoothed_emotions, study_state
    
    def get_raw_emotions(self, frame):
        """Get raw emotion scores without smoothing (for debugging)."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.detector.detect_emotions(rgb_frame)
        
        if not result:
            return None
        
        return result[0]['emotions']
    
    def reset_history(self):
        """Reset emotion history (e.g., when user returns after break)."""
        self.emotion_history.clear()
        self.no_face_count = 0


class DeepFaceClassifier:
    """
    Alternative emotion classifier using DeepFace library.
    DeepFace supports multiple models: VGG-Face, Facenet, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace.
    The emotion analysis uses a separate model trained on facial emotions.
    """
    
    def __init__(self, smoothing_window=5, confidence_threshold=0.3):
        """
        Initialize DeepFace-based classifier.
        
        Args:
            smoothing_window: Number of frames to average emotions over
            confidence_threshold: Minimum confidence to accept classification
        """
        print("Initializing DeepFace classifier...")
        
        # Import DeepFace - this is optional, so we handle import errors
        try:
            from deepface import DeepFace
            self.DeepFace = DeepFace
            self.available = True
        except ImportError:
            print("Warning: DeepFace not installed. Run: pip install deepface")
            self.available = False
            return
        
        self.confidence_threshold = confidence_threshold
        self.smoothing_window = smoothing_window
        
        # Emotion history for temporal smoothing
        self.emotion_history = deque(maxlen=smoothing_window)
        
        # DeepFace emotion names to our mapping
        self.emotion_weights = {
            'neutral': {'state': 'Focused', 'weight': 1.0},
            'happy': {'state': 'Focused', 'weight': 1.2},
            'angry': {'state': 'Stressed', 'weight': 1.5},
            'disgust': {'state': 'Stressed', 'weight': 1.2},
            'fear': {'state': 'Stressed', 'weight': 1.3},
            'sad': {'state': 'Bored', 'weight': 1.4},
            'surprise': {'state': 'Distracted', 'weight': 0.8}
        }
        
        self.state_priority = {
            'Stressed': 3,
            'Bored': 2,
            'Distracted': 1,
            'Focused': 0
        }
        
        self.last_box = None
        self.no_face_count = 0
        self.max_no_face_frames = 3  # Quickly detect no face
        
        # Pre-warm the model
        print("Pre-warming DeepFace model (first run is slow)...")
        try:
            # Create a dummy image to warm up the model
            dummy = np.zeros((224, 224, 3), dtype=np.uint8)
            self.DeepFace.analyze(dummy, actions=['emotion'], enforce_detection=False, silent=True)
        except:
            pass
        print("DeepFace initialized successfully!")
    
    def _smooth_emotions(self, current_emotions):
        """Apply temporal smoothing."""
        if current_emotions is None:
            return None
        
        self.emotion_history.append(current_emotions)
        
        if len(self.emotion_history) < 2:
            return current_emotions
        
        smoothed = {}
        for emotion in current_emotions.keys():
            values = [h.get(emotion, 0) for h in self.emotion_history]
            weights = np.linspace(0.5, 1.0, len(values))
            smoothed[emotion] = np.average(values, weights=weights)
        
        return smoothed
    
    def _calculate_study_state(self, emotions):
        """Calculate study state using weighted scoring."""
        if emotions is None:
            return "No Face Detected"
        
        state_scores = {'Focused': 0, 'Stressed': 0, 'Bored': 0, 'Distracted': 0}
        
        for emotion, confidence in emotions.items():
            emotion_lower = emotion.lower()
            if emotion_lower in self.emotion_weights:
                state = self.emotion_weights[emotion_lower]['state']
                weight = self.emotion_weights[emotion_lower]['weight']
                # DeepFace returns percentages (0-100), normalize to 0-1
                state_scores[state] += (confidence / 100.0) * weight
        
        max_state = max(state_scores, key=state_scores.get)
        max_score = state_scores[max_state]
        
        if max_score < self.confidence_threshold:
            return "Uncertain"
        
        for state in ['Stressed', 'Bored', 'Distracted']:
            if state != max_state and state_scores[state] > max_score * 0.8:
                if self.state_priority[state] > self.state_priority[max_state]:
                    max_state = state
        
        return max_state
    
    def analyze_frame(self, frame):
        """Analyze a frame using DeepFace."""
        if not self.available:
            return None, None, "DeepFace not available"
        
        try:
            # DeepFace.analyze expects BGR image (OpenCV format) or file path
            result = self.DeepFace.analyze(
                frame, 
                actions=['emotion'],
                enforce_detection=False,  # Don't throw error if no face
                silent=True,
                detector_backend='opencv'  # Faster than default
            )
            
            if not result:
                self.no_face_count += 1
                if self.no_face_count > self.max_no_face_frames:
                    self.emotion_history.clear()
                return self.last_box, None, "No Face Detected"
            
            self.no_face_count = 0
            
            # DeepFace returns a list or dict depending on version
            if isinstance(result, list):
                result = result[0]
            
            # Extract emotions
            emotions = result.get('emotion', {})
            
            # Extract face region
            region = result.get('region', {})
            if region:
                box = (region.get('x', 0), region.get('y', 0), 
                       region.get('w', 0), region.get('h', 0))
            else:
                box = self.last_box
            
            if box and box[2] > 0:
                self.last_box = box
            
            # Apply smoothing
            smoothed = self._smooth_emotions(emotions)
            
            # Calculate study state
            study_state = self._calculate_study_state(smoothed)
            
            return box, smoothed, study_state
            
        except Exception as e:
            return self.last_box, None, f"Error: {str(e)[:30]}"
    
    def reset_history(self):
        """Reset emotion history."""
        self.emotion_history.clear()
        self.no_face_count = 0


def create_classifier(backend='fer', **kwargs):
    """
    Factory function to create the appropriate classifier.
    
    Args:
        backend: 'fer' (default) or 'deepface'
        **kwargs: Additional arguments for the classifier
    
    Returns:
        EmotionClassifier or DeepFaceClassifier instance
    """
    if backend.lower() == 'deepface':
        return DeepFaceClassifier(**kwargs)
    else:
        return EmotionClassifier(**kwargs)
