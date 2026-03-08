"""
Configuration module for the AI Study Monitor.
Handles loading/saving user preferences and app settings.
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Dict, List

CONFIG_FILE = "config.json"

@dataclass
class Config:
    """Application configuration with defaults."""
    
    # Pomodoro Settings
    pomodoro_duration_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    pomodoros_before_long_break: int = 4
    
    # Emotion Detection Thresholds
    focus_trigger_seconds: float = 5.0
    stress_trigger_seconds: float = 20.0
    no_face_pause_seconds: float = 5.0  # Pause quickly when no face detected
    
    # Model Settings
    model_backend: str = "fer"  # "fer" (default) or "deepface" (better but slower)
    use_mtcnn: bool = True  # Better face detection (slower but more accurate)
    smoothing_window: int = 5  # Frames to average (reduces jitter)
    confidence_threshold: float = 0.3  # Minimum confidence to classify
    
    # UI Settings
    always_on_top: bool = True
    theme: str = "dark"  # "dark" or "light"
    show_emotion_bars: bool = True
    show_camera: bool = True
    mirror_camera: bool = True
    
    # Audio Settings
    voice_enabled: bool = True
    sound_enabled: bool = True
    volume: float = 0.7
    
    # Camera Settings
    camera_index: int = 0
    frame_skip: int = 5
    
    # Session Settings
    auto_save_sessions: bool = True
    session_history_days: int = 30
    
    # Multi-User Settings
    multi_user_enabled: bool = True
    face_recognition_tolerance: float = 0.6  # Lower = stricter matching
    recognition_interval: float = 1.0  # Seconds between recognition attempts
    show_user_leaderboard: bool = True
    
    def save(self):
        """Save config to JSON file."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(asdict(self), f, indent=4)
    
    @classmethod
    def load(cls) -> 'Config':
        """Load config from JSON file, or return defaults."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()


@dataclass
class SessionStats:
    """Statistics for a single study session."""
    start_time: str = ""
    end_time: str = ""
    total_study_seconds: float = 0.0
    total_break_seconds: float = 0.0
    pomodoros_completed: int = 0
    emotion_breakdown: Dict[str, float] = field(default_factory=dict)
    focus_percentage: float = 0.0
    
    def to_dict(self):
        return asdict(self)


class SessionHistory:
    """Manages historical session data."""
    
    HISTORY_FILE = "session_history.json"
    
    def __init__(self):
        self.sessions: List[Dict] = []
        self.load()
    
    def load(self):
        """Load session history from file."""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    self.sessions = json.load(f)
            except (json.JSONDecodeError, TypeError):
                self.sessions = []
    
    def save(self):
        """Save session history to file."""
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump(self.sessions, f, indent=4)
    
    def add_session(self, stats: SessionStats):
        """Add a completed session to history."""
        self.sessions.append(stats.to_dict())
        self.save()
    
    def get_today_stats(self) -> Dict:
        """Get aggregated stats for today."""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        total_study = 0.0
        total_pomodoros = 0
        
        for session in self.sessions:
            if session.get("start_time", "").startswith(today):
                total_study += session.get("total_study_seconds", 0)
                total_pomodoros += session.get("pomodoros_completed", 0)
        
        return {
            "date": today,
            "total_study_seconds": total_study,
            "total_pomodoros": total_pomodoros
        }
    
    def get_weekly_stats(self) -> List[Dict]:
        """Get daily breakdown for the last 7 days."""
        from datetime import datetime, timedelta
        
        stats = []
        for i in range(7):
            day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_study = 0.0
            day_pomodoros = 0
            
            for session in self.sessions:
                if session.get("start_time", "").startswith(day):
                    day_study += session.get("total_study_seconds", 0)
                    day_pomodoros += session.get("pomodoros_completed", 0)
            
            stats.append({
                "date": day,
                "total_study_seconds": day_study,
                "total_pomodoros": day_pomodoros
            })
        
        return stats


# Global config instance
config = Config.load()
