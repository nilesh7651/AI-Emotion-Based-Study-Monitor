"""
Eye Strain Detection Module for AI Study Monitor

Features:
- Blink rate detection
- Eye strain warning system
- Distance-from-screen estimation
- Fatigue detection based on facial features
- Sound and voice warnings
"""

import time
import threading
from collections import deque
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
import numpy as np

# Try importing sound libraries
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Try importing required libraries
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import dlib
    DLIB_AVAILABLE = True
except ImportError:
    DLIB_AVAILABLE = False

try:
    from scipy.spatial import distance as dist
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


@dataclass
class EyeMetrics:
    """Container for eye-related metrics."""
    blink_rate_per_minute: float
    eye_aspect_ratio: float
    is_blinking: bool
    eyes_detected: bool
    fatigue_level: str  # 'low', 'medium', 'high'
    time_since_last_blink: float
    warning: Optional[str] = None


class EyeStrainDetector:
    """
    Detects eye strain indicators from webcam feed.
    
    Uses Eye Aspect Ratio (EAR) to detect blinks:
    - Normal EAR: ~0.3
    - Blink EAR: < 0.2
    """
    
    # Thresholds
    EAR_THRESHOLD = 0.21  # Below this = closed eyes
    BLINK_CONSECUTIVE_FRAMES = 2  # Frames eyes must be closed for blink
    
    # Health thresholds
    HEALTHY_BLINK_RATE = 15  # Blinks per minute (normal is 15-20)
    LOW_BLINK_WARNING = 10  # Warn if below this
    
    # Fatigue thresholds (based on slow blinks - longer closure time)
    SLOW_BLINK_DURATION = 0.5  # Seconds - blinks longer than this suggest fatigue
    
    def __init__(self, 
                 shape_predictor_path: str = None,
                 on_strain_warning: Callable = None,
                 enable_voice: bool = True,
                 enable_sound: bool = True):
        """
        Initialize eye strain detector.
        
        Args:
            shape_predictor_path: Path to dlib shape predictor model
            on_strain_warning: Callback when eye strain is detected
            enable_voice: Enable voice warnings
            enable_sound: Enable sound effects
        """
        self.on_strain_warning = on_strain_warning
        self._initialized = False
        self.enable_voice = enable_voice and PYTTSX3_AVAILABLE
        self.enable_sound = enable_sound and PYGAME_AVAILABLE
        
        # Initialize voice engine
        self._tts_engine = None
        if self.enable_voice:
            try:
                self._tts_engine = pyttsx3.init()
                self._tts_engine.setProperty('rate', 150)
            except:
                self.enable_voice = False
        
        # Initialize pygame for sound
        if self.enable_sound:
            try:
                pygame.mixer.init()
            except:
                self.enable_sound = False
        
        # Tracking variables
        self.blink_counter = 0
        self.blink_timestamps = deque(maxlen=60)  # Store last 60 blinks
        self.ear_history = deque(maxlen=30)  # For smoothing
        
        self.frame_counter = 0
        self.blink_start_frame = 0
        self.is_currently_blinking = False
        self.last_blink_time = time.time()
        
        # Counters for warning system
        self.warning_cooldown = 0
        self.consecutive_low_blink_minutes = 0
        
        # Initialize face/eye detection
        self._init_detector(shape_predictor_path)
    
    def _init_detector(self, shape_predictor_path: str = None):
        """Initialize the face landmark detector."""
        if not CV2_AVAILABLE:
            print("Warning: OpenCV not available for eye strain detection")
            return
        
        # Try dlib first (more accurate)
        if DLIB_AVAILABLE and shape_predictor_path:
            try:
                self.detector = dlib.get_frontal_face_detector()
                self.predictor = dlib.shape_predictor(shape_predictor_path)
                self._initialized = True
                self._method = "dlib"
                return
            except:
                pass
        
        # Fallback to OpenCV Haar cascades
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            self._initialized = True
            self._method = "opencv"
        except:
            print("Warning: Could not initialize eye detectors")
            self._initialized = False
    
    def _eye_aspect_ratio(self, eye_points) -> float:
        """
        Calculate Eye Aspect Ratio (EAR).
        
        EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        
        Where p1-p6 are the 6 eye landmark points.
        """
        if not SCIPY_AVAILABLE:
            return 0.3  # Default open eye value
        
        # Compute euclidean distances
        A = dist.euclidean(eye_points[1], eye_points[5])
        B = dist.euclidean(eye_points[2], eye_points[4])
        C = dist.euclidean(eye_points[0], eye_points[3])
        
        # Calculate EAR
        ear = (A + B) / (2.0 * C)
        return ear
    
    def detect_blink_dlib(self, frame) -> Tuple[bool, float]:
        """Detect blinks using dlib landmarks."""
        if not hasattr(self, 'predictor'):
            return False, 0.3
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)
        
        if len(faces) == 0:
            return False, 0.3
        
        face = faces[0]
        shape = self.predictor(gray, face)
        
        # Eye landmark indices (dlib 68-point model)
        LEFT_EYE = list(range(36, 42))
        RIGHT_EYE = list(range(42, 48))
        
        # Get eye points
        left_eye = [(shape.part(i).x, shape.part(i).y) for i in LEFT_EYE]
        right_eye = [(shape.part(i).x, shape.part(i).y) for i in RIGHT_EYE]
        
        # Calculate EAR for both eyes
        left_ear = self._eye_aspect_ratio(left_eye)
        right_ear = self._eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        
        return ear < self.EAR_THRESHOLD, ear
    
    def detect_blink_opencv(self, frame) -> Tuple[bool, float]:
        """Detect blinks using OpenCV (less accurate but no extra models needed)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5,
            minSize=(100, 100)
        )
        
        if len(faces) == 0:
            return False, 0.3
        
        # Get largest face
        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face
        
        # Region of interest for eyes (upper half of face)
        roi_gray = gray[y:y+int(h*0.6), x:x+w]
        
        # Detect eyes in face region
        eyes = self.eye_cascade.detectMultiScale(
            roi_gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20)
        )
        
        # If less than 2 eyes detected, consider it a potential blink
        eyes_detected = len(eyes) >= 2
        
        # Simple EAR approximation based on eye detection
        ear = 0.3 if eyes_detected else 0.1
        is_blinking = not eyes_detected
        
        return is_blinking, ear
    
    def process_frame(self, frame) -> EyeMetrics:
        """
        Process a video frame to detect eye strain indicators.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            EyeMetrics with blink rate and strain indicators
        """
        if not self._initialized or frame is None:
            return EyeMetrics(
                blink_rate_per_minute=15.0,
                eye_aspect_ratio=0.3,
                is_blinking=False,
                eyes_detected=False,
                fatigue_level='low',
                time_since_last_blink=0.0
            )
        
        self.frame_counter += 1
        current_time = time.time()
        
        # Detect blink based on method
        if self._method == "dlib":
            is_blinking, ear = self.detect_blink_dlib(frame)
        else:
            is_blinking, ear = self.detect_blink_opencv(frame)
        
        # Update EAR history for smoothing
        self.ear_history.append(ear)
        smoothed_ear = sum(self.ear_history) / len(self.ear_history)
        
        # Blink detection state machine
        if is_blinking and not self.is_currently_blinking:
            # Blink started
            self.is_currently_blinking = True
            self.blink_start_frame = self.frame_counter
        
        elif not is_blinking and self.is_currently_blinking:
            # Blink ended
            self.is_currently_blinking = False
            blink_duration_frames = self.frame_counter - self.blink_start_frame
            
            # Only count as blink if eyes were closed for minimum frames
            if blink_duration_frames >= self.BLINK_CONSECUTIVE_FRAMES:
                self.blink_counter += 1
                self.blink_timestamps.append(current_time)
                self.last_blink_time = current_time
        
        # Calculate blink rate (blinks in last 60 seconds)
        one_minute_ago = current_time - 60
        recent_blinks = sum(1 for t in self.blink_timestamps if t > one_minute_ago)
        blink_rate = recent_blinks
        
        # Time since last blink
        time_since_blink = current_time - self.last_blink_time
        
        # Determine fatigue level
        fatigue_level = self._assess_fatigue(blink_rate, time_since_blink, smoothed_ear)
        
        # Check for warnings
        warning = self._check_warnings(blink_rate, time_since_blink, current_time)
        
        return EyeMetrics(
            blink_rate_per_minute=blink_rate,
            eye_aspect_ratio=smoothed_ear,
            is_blinking=is_blinking,
            eyes_detected=True,
            fatigue_level=fatigue_level,
            time_since_last_blink=time_since_blink,
            warning=warning
        )
    
    def _assess_fatigue(self, blink_rate: float, time_since_blink: float, ear: float) -> str:
        """Assess fatigue level based on eye metrics."""
        fatigue_score = 0
        
        # Low blink rate increases fatigue score
        if blink_rate < 10:
            fatigue_score += 2
        elif blink_rate < 12:
            fatigue_score += 1
        
        # Long time without blinking
        if time_since_blink > 10:
            fatigue_score += 2
        elif time_since_blink > 5:
            fatigue_score += 1
        
        # Low EAR (droopy eyes)
        if ear < 0.25:
            fatigue_score += 2
        elif ear < 0.28:
            fatigue_score += 1
        
        if fatigue_score >= 4:
            return 'high'
        elif fatigue_score >= 2:
            return 'medium'
        return 'low'
    
    def _check_warnings(self, blink_rate: float, time_since_blink: float, 
                        current_time: float) -> Optional[str]:
        """Check if any warnings should be triggered."""
        # Cooldown between warnings (5 minutes)
        if self.warning_cooldown > 0:
            self.warning_cooldown -= 1
            return None
        
        warning = None
        
        # Long time without blinking
        if time_since_blink > 30:
            warning = "You haven't blinked in a while! Blink naturally to refresh your eyes."
            self.warning_cooldown = 300  # 5 minutes at ~1fps
        
        # Consistently low blink rate
        elif blink_rate < self.LOW_BLINK_WARNING:
            warning = f"Low blink rate ({blink_rate}/min). Look away from screen briefly."
            self.warning_cooldown = 300
        
        # Trigger warnings with sound/voice
        if warning:
            self._play_warning(warning)
            if self.on_strain_warning:
                self.on_strain_warning(warning)
        
        return warning
    
    def _play_warning(self, message: str):
        """Play warning sound and voice."""
        # Play alert sound
        if self.enable_sound:
            self._play_alert_sound()
        
        # Speak warning
        if self.enable_voice:
            self._speak_warning(message)
    
    def _play_alert_sound(self):
        """Play alert sound effect."""
        if not PYGAME_AVAILABLE:
            return
        try:
            # Generate a simple beep if no sound file
            import numpy as np
            sample_rate = 44100
            duration = 0.3
            frequency = 800
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t) * 0.3
            wave = (wave * 32767).astype(np.int16)
            stereo = np.column_stack((wave, wave))
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
        except:
            pass
    
    def _speak_warning(self, message: str):
        """Speak warning using text-to-speech."""
        if not self._tts_engine:
            return
        
        def speak():
            try:
                self._tts_engine.say(message)
                self._tts_engine.runAndWait()
            except:
                pass
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=speak, daemon=True)
        thread.start()
    
    def get_summary(self) -> dict:
        """Get summary of eye strain metrics."""
        one_minute_ago = time.time() - 60
        recent_blinks = sum(1 for t in self.blink_timestamps if t > one_minute_ago)
        
        return {
            'total_blinks': self.blink_counter,
            'blinks_per_minute': recent_blinks,
            'avg_ear': sum(self.ear_history) / len(self.ear_history) if self.ear_history else 0.3,
            'time_since_last_blink': time.time() - self.last_blink_time
        }
    
    def estimate_distance(self, face_width_pixels: int, frame_width: int) -> float:
        """
        Estimate distance from screen based on face size.
        
        Args:
            face_width_pixels: Width of detected face in pixels
            frame_width: Total frame width
            
        Returns:
            Estimated distance in cm (approximate)
        """
        # Average face width is ~15cm
        # Using simple proportion: larger face = closer
        AVG_FACE_WIDTH_CM = 15
        REFERENCE_FACE_RATIO = 0.3  # Face should be ~30% of frame at 50cm
        REFERENCE_DISTANCE = 50  # cm
        
        face_ratio = face_width_pixels / frame_width
        
        if face_ratio > 0:
            distance = (REFERENCE_FACE_RATIO / face_ratio) * REFERENCE_DISTANCE
            return max(20, min(150, distance))  # Clamp to reasonable range
        return REFERENCE_DISTANCE
    
    def get_distance_warning(self, distance_cm: float) -> Optional[str]:
        """Get warning if too close to screen."""
        if distance_cm < 30:
            return "You're too close to the screen! Move back for better eye health."
        elif distance_cm < 40:
            return "Consider moving a bit further from the screen."
        return None
    
    def reset(self):
        """Reset all counters."""
        self.blink_counter = 0
        self.blink_timestamps.clear()
        self.ear_history.clear()
        self.frame_counter = 0
        self.last_blink_time = time.time()
        self.warning_cooldown = 0


class SimpleEyeStrainMonitor:
    """
    Simplified eye strain monitor without dlib dependency.
    Uses heuristics and timing-based detection.
    """
    
    def __init__(self, on_warning: Callable = None):
        self.on_warning = on_warning
        
        # Timing
        self.start_time = time.time()
        self.last_break_time = time.time()
        self.last_warning_time = 0
        
        # Thresholds
        self.warning_interval = 30 * 60  # 30 minutes
        self.break_reminder_interval = 20 * 60  # 20 minutes
        
        # Face detection
        self.face_detected_count = 0
        self.total_frames = 0
    
    def process_frame(self, frame, face_detected: bool = True) -> dict:
        """Process frame with simple heuristics."""
        self.total_frames += 1
        if face_detected:
            self.face_detected_count += 1
        
        current_time = time.time()
        time_since_start = current_time - self.start_time
        time_since_break = current_time - self.last_break_time
        
        warning = None
        
        # Time-based eye strain reminder
        if time_since_break > self.break_reminder_interval:
            if current_time - self.last_warning_time > self.warning_interval:
                warning = "You've been studying for a while. Follow the 20-20-20 rule!"
                self.last_warning_time = current_time
                
                if self.on_warning:
                    self.on_warning(warning)
        
        # Face presence ratio (if user is looking away a lot, that's good!)
        face_ratio = self.face_detected_count / max(self.total_frames, 1)
        
        return {
            'session_duration': time_since_start,
            'time_since_break': time_since_break,
            'face_presence_ratio': face_ratio,
            'warning': warning,
            'suggestion': self._get_suggestion(time_since_break)
        }
    
    def _get_suggestion(self, time_since_break: float) -> Optional[str]:
        """Get contextual suggestion."""
        if time_since_break > 25 * 60:
            return "Take a break! Look at something 20 feet away for 20 seconds."
        elif time_since_break > 15 * 60:
            return "Consider closing your eyes briefly to rest them."
        return None
    
    def mark_break(self):
        """Mark that user took a break."""
        self.last_break_time = time.time()
    
    def get_eye_health_score(self) -> int:
        """Get an eye health score 0-100."""
        time_since_break = time.time() - self.last_break_time
        
        # Score decreases as time without break increases
        max_comfortable = 20 * 60  # 20 minutes
        
        if time_since_break <= max_comfortable:
            return 100
        elif time_since_break <= 30 * 60:
            return 80
        elif time_since_break <= 45 * 60:
            return 60
        elif time_since_break <= 60 * 60:
            return 40
        else:
            return 20


def test_eye_strain():
    """Test eye strain detection with webcam."""
    if not CV2_AVAILABLE:
        print("OpenCV not available")
        return
    
    def on_warning(msg):
        print(f"\n⚠️ EYE STRAIN WARNING: {msg}\n")
    
    detector = EyeStrainDetector(on_strain_warning=on_warning)
    cap = cv2.VideoCapture(0)
    
    print("Eye Strain Detection Test")
    print("Press 'q' to quit")
    print("-" * 40)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Process frame
        metrics = detector.process_frame(frame)
        
        # Display metrics on frame
        status = f"Blink Rate: {metrics.blink_rate_per_minute}/min | EAR: {metrics.eye_aspect_ratio:.2f}"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        fatigue_color = {'low': (0, 255, 0), 'medium': (0, 255, 255), 'high': (0, 0, 255)}
        cv2.putText(frame, f"Fatigue: {metrics.fatigue_level}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, fatigue_color[metrics.fatigue_level], 2)
        
        if metrics.warning:
            cv2.putText(frame, "WARNING!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        cv2.imshow("Eye Strain Detection", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\nSession Summary:")
    print(f"  Total blinks: {detector.blink_counter}")


if __name__ == "__main__":
    test_eye_strain()
