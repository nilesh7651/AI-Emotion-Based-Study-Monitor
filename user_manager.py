"""
Multi-User Face Recognition Module for AI Study Monitor.
Handles user registration, recognition, and per-user time tracking.
"""

import json
import os
import pickle
import cv2
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Face recognition library
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Warning: face_recognition not installed. Multi-user mode disabled.")
    print("Install with: pip install face_recognition")
    print("Note: On Windows, you may need to install dlib first with conda or from wheels.")


USERS_FILE = "users.json"
ENCODINGS_FILE = "face_encodings.pkl"


@dataclass
class User:
    """Represents a registered user."""
    user_id: str
    name: str
    created_at: str = ""
    total_study_seconds: float = 0.0
    total_sessions: int = 0
    total_pomodoros: int = 0
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(**data)


@dataclass
class UserSession:
    """Tracks a user's current session."""
    user_id: str
    start_time: datetime
    study_seconds: float = 0.0
    break_seconds: float = 0.0
    pomodoros: int = 0
    emotion_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    

class UserManager:
    """Manages multiple users with face recognition."""
    
    def __init__(self, recognition_tolerance: float = 0.6):
        """
        Initialize the user manager.
        
        Args:
            recognition_tolerance: Face matching threshold (lower = stricter, default 0.6)
        """
        self.users: Dict[str, User] = {}  # user_id -> User
        self.face_encodings: Dict[str, List[np.ndarray]] = {}  # user_id -> list of encodings
        self.recognition_tolerance = recognition_tolerance
        
        # Current session tracking
        self.active_sessions: Dict[str, UserSession] = {}  # user_id -> UserSession
        self.current_user_id: Optional[str] = None
        self.last_recognition_time: float = 0
        self.recognition_interval: float = 1.0  # Seconds between recognition attempts
        
        # Recognition cache for stability
        self._cached_user_id: Optional[str] = None
        self._cache_confidence: float = 0.0
        self._consecutive_matches: int = 0
        self._min_consecutive_for_switch: int = 3  # Require 3 consecutive matches to switch users
        
        # Grace period for temporary face loss
        self._last_face_time: float = 0
        self._no_face_grace_period: float = 10.0  # Keep user for 10 seconds without face
        self._no_face_count: int = 0
        self._max_no_face_before_clear: int = 15  # ~15 recognition attempts without face = clear
        
        # Load existing data
        self._load_users()
        self._load_encodings()
    
    def _load_users(self):
        """Load users from JSON file."""
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r') as f:
                    data = json.load(f)
                for user_data in data:
                    user = User.from_dict(user_data)
                    self.users[user.user_id] = user
                print(f"Loaded {len(self.users)} registered users.")
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                print(f"Error loading users: {e}")
                self.users = {}
    
    def _save_users(self):
        """Save users to JSON file."""
        data = [user.to_dict() for user in self.users.values()]
        with open(USERS_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    
    def _load_encodings(self):
        """Load face encodings from pickle file."""
        if os.path.exists(ENCODINGS_FILE):
            try:
                with open(ENCODINGS_FILE, 'rb') as f:
                    self.face_encodings = pickle.load(f)
                print(f"Loaded face encodings for {len(self.face_encodings)} users.")
            except Exception as e:
                print(f"Error loading encodings: {e}")
                self.face_encodings = {}
    
    def _save_encodings(self):
        """Save face encodings to pickle file."""
        with open(ENCODINGS_FILE, 'wb') as f:
            pickle.dump(self.face_encodings, f)
    
    def register_user(self, name: str, frame: np.ndarray) -> Tuple[bool, str]:
        """
        Register a new user with their face from a video frame.
        
        Args:
            name: User's name
            frame: BGR frame from camera
            
        Returns:
            (success, message)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return False, "Face recognition library not available"
        
        # Convert BGR to RGB for face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces in the frame
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) == 0:
            return False, "No face detected. Please position your face clearly in the camera."
        
        if len(face_locations) > 1:
            return False, "Multiple faces detected. Please ensure only one person is in frame."
        
        # Get face encoding
        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if len(encodings) == 0:
            return False, "Could not encode face. Please try again."
        
        encoding = encodings[0]
        
        # Check if this face is already registered
        for existing_user_id, existing_encodings in self.face_encodings.items():
            matches = face_recognition.compare_faces(
                existing_encodings, encoding, tolerance=self.recognition_tolerance
            )
            if any(matches):
                existing_user = self.users.get(existing_user_id)
                if existing_user:
                    return False, f"This face is already registered as '{existing_user.name}'"
        
        # Generate unique user ID
        user_id = f"user_{len(self.users) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create user
        user = User(
            user_id=user_id,
            name=name,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        self.users[user_id] = user
        self.face_encodings[user_id] = [encoding]
        
        # Save data
        self._save_users()
        self._save_encodings()
        
        return True, f"Successfully registered '{name}'!"
    
    def add_face_sample(self, user_id: str, frame: np.ndarray) -> Tuple[bool, str]:
        """
        Add another face sample for an existing user (improves recognition).
        
        Args:
            user_id: User's ID
            frame: BGR frame from camera
            
        Returns:
            (success, message)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return False, "Face recognition library not available"
        
        if user_id not in self.users:
            return False, "User not found"
        
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if len(face_locations) != 1:
            return False, "Please ensure exactly one face is visible"
        
        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if len(encodings) == 0:
            return False, "Could not encode face"
        
        if user_id not in self.face_encodings:
            self.face_encodings[user_id] = []
        
        self.face_encodings[user_id].append(encodings[0])
        self._save_encodings()
        
        return True, f"Added face sample (total: {len(self.face_encodings[user_id])})"
    
    def recognize_user(self, frame: np.ndarray, force: bool = False) -> Optional[str]:
        """
        Recognize a user from a video frame.
        
        Args:
            frame: BGR frame from camera
            force: Force recognition even if interval hasn't passed
            
        Returns:
            user_id if recognized, None otherwise
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return None
        
        if len(self.users) == 0:
            return None
        
        import time
        now = time.time()
        
        # Rate limit recognition to save CPU
        if not force and (now - self.last_recognition_time) < self.recognition_interval:
            return self.current_user_id
        
        self.last_recognition_time = now
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Find faces (use faster model for real-time)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        
        if len(face_locations) == 0:
            # No face detected - handle grace period
            self._no_face_count += 1
            
            # Check if we should clear the current user
            time_since_face = now - self._last_face_time
            
            if self._no_face_count > self._max_no_face_before_clear or time_since_face > self._no_face_grace_period:
                # Too long without face - clear user but DON'T end session yet
                # (session ends only when app closes or user manually logs out)
                if self.current_user_id:
                    # Don't clear immediately, just stop accumulating time
                    pass
                return self.current_user_id  # Still return current user for display
            else:
                # Within grace period - keep current user
                return self.current_user_id
        
        # Face detected - reset no-face counter
        self._no_face_count = 0
        self._last_face_time = now
        
        # Use the largest face (closest to camera)
        if len(face_locations) > 1:
            face_locations = [max(face_locations, key=lambda loc: (loc[2]-loc[0]) * (loc[1]-loc[3]))]
        
        # Get encoding for the detected face
        encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if len(encodings) == 0:
            # Couldn't encode face - keep current user
            return self.current_user_id
        
        face_encoding = encodings[0]
        
        # Compare against all registered users
        best_match_id = None
        best_match_distance = float('inf')
        
        for user_id, user_encodings in self.face_encodings.items():
            if len(user_encodings) == 0:
                continue
            
            # Calculate face distances
            distances = face_recognition.face_distance(user_encodings, face_encoding)
            min_distance = min(distances)
            
            if min_distance < self.recognition_tolerance and min_distance < best_match_distance:
                best_match_distance = min_distance
                best_match_id = user_id
        
        # Smooth user switching with consecutive match requirement
        if best_match_id is not None:
            if best_match_id == self._cached_user_id:
                self._consecutive_matches += 1
            else:
                self._cached_user_id = best_match_id
                self._consecutive_matches = 1
            
            self._cache_confidence = 1.0 - best_match_distance
            
            # Only switch if we have enough consecutive matches
            if self._consecutive_matches >= self._min_consecutive_for_switch:
                if best_match_id != self.current_user_id:
                    self._on_user_change(best_match_id)
                return best_match_id
        
        return self.current_user_id
    
    def _on_user_change(self, new_user_id: str):
        """Handle user change event."""
        old_user_id = self.current_user_id
        
        # End previous user's session
        if old_user_id and old_user_id in self.active_sessions:
            self._end_session(old_user_id)
        
        # Start new user's session
        self.current_user_id = new_user_id
        if new_user_id not in self.active_sessions:
            self._start_session(new_user_id)
        
        if old_user_id:
            old_name = self.users.get(old_user_id, User("", "Unknown")).name
            new_name = self.users.get(new_user_id, User("", "Unknown")).name
            print(f"User switched: {old_name} -> {new_name}")
    
    def _start_session(self, user_id: str):
        """Start a new session for a user."""
        self.active_sessions[user_id] = UserSession(
            user_id=user_id,
            start_time=datetime.now()
        )
    
    def _end_session(self, user_id: str):
        """End a user's session and save stats."""
        if user_id not in self.active_sessions:
            return
        
        session = self.active_sessions[user_id]
        
        # Update user's session count and pomodoros (time is already updated live)
        if user_id in self.users:
            user = self.users[user_id]
            user.total_sessions += 1
            user.total_pomodoros += session.pomodoros
            self._save_users()
        
        del self.active_sessions[user_id]
    
    def update_session_time(self, user_id: str, study_seconds: float = 0, break_seconds: float = 0):
        """Update the current session's time tracking."""
        if user_id in self.active_sessions:
            self.active_sessions[user_id].study_seconds += study_seconds
            self.active_sessions[user_id].break_seconds += break_seconds
            
            # Also update user's running total for live display
            if user_id in self.users:
                self.users[user_id].total_study_seconds += study_seconds
        
        # Auto-save every 60 seconds of accumulated time
        if not hasattr(self, '_last_autosave'):
            self._last_autosave = 0
            self._accumulated_since_save = 0
        
        self._accumulated_since_save += study_seconds
        if self._accumulated_since_save >= 60:  # Save every minute of study
            self._save_users()
            self._accumulated_since_save = 0
    
    def add_pomodoro(self, user_id: str):
        """Add a completed pomodoro to user's session."""
        if user_id in self.active_sessions:
            self.active_sessions[user_id].pomodoros += 1
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.users.get(user_id)
    
    def get_current_user(self) -> Optional[User]:
        """Get the currently recognized user."""
        if self.current_user_id:
            return self.users.get(self.current_user_id)
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all registered users."""
        return list(self.users.values())
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive stats for a user."""
        user = self.users.get(user_id)
        if not user:
            return {}
        
        session = self.active_sessions.get(user_id)
        current_session_seconds = session.study_seconds if session else 0
        
        return {
            "name": user.name,
            "total_study_seconds": user.total_study_seconds + current_session_seconds,
            "total_sessions": user.total_sessions,
            "total_pomodoros": user.total_pomodoros,
            "current_session_seconds": current_session_seconds
        }
    
    def get_leaderboard(self) -> List[Dict]:
        """Get users sorted by total study time."""
        stats = []
        for user in self.users.values():
            session = self.active_sessions.get(user.user_id)
            current = session.study_seconds if session else 0
            stats.append({
                "user_id": user.user_id,
                "name": user.name,
                "total_seconds": user.total_study_seconds + current,
                "pomodoros": user.total_pomodoros + (session.pomodoros if session else 0)
            })
        
        return sorted(stats, key=lambda x: x["total_seconds"], reverse=True)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user and their face data."""
        if user_id not in self.users:
            return False
        
        # End any active session
        if user_id in self.active_sessions:
            del self.active_sessions[user_id]
        
        # Remove user
        del self.users[user_id]
        
        # Remove encodings
        if user_id in self.face_encodings:
            del self.face_encodings[user_id]
        
        # Clear current user if deleted
        if self.current_user_id == user_id:
            self.current_user_id = None
        
        self._save_users()
        self._save_encodings()
        
        return True
    
    def save_all_sessions(self):
        """Save all active sessions (call on app exit)."""
        for user_id in list(self.active_sessions.keys()):
            self._end_session(user_id)
        self._save_users()
    
    def is_available(self) -> bool:
        """Check if face recognition is available."""
        return FACE_RECOGNITION_AVAILABLE


# Singleton instance
_user_manager_instance: Optional[UserManager] = None


def get_user_manager() -> UserManager:
    """Get the singleton UserManager instance."""
    global _user_manager_instance
    if _user_manager_instance is None:
        _user_manager_instance = UserManager()
    return _user_manager_instance
