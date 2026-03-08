import time
from datetime import datetime
from config import config, SessionStats, SessionHistory
from collections import defaultdict

class StudyLogic:
    def __init__(self):
        self.state = "STOPPED"  # STOPPED, STUDYING, PAUSED, BREAK
        self.study_duration_seconds = 0
        self.break_duration_seconds = 0
        self.last_tick = time.time()
        
        # Track the active emotion
        self.current_emotion = "No Face"
        self.emotion_start_time = time.time()
        
        # Pomodoro settings from config
        self.pomodoro_limit = config.pomodoro_duration_minutes * 60
        self.short_break_limit = config.short_break_minutes * 60
        self.long_break_limit = config.long_break_minutes * 60
        
        # Pomodoro tracking
        self.pomodoros_completed = 0
        self.current_break_limit = self.short_break_limit
        
        # Emotion statistics
        self.emotion_counts = defaultdict(int)
        self.total_emotion_samples = 0
        
        # Session tracking
        self.session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.no_face_start = None
        
        # Break timer
        self.break_remaining = 0
        self.in_break_countdown = False
        
        # Session history
        self.history = SessionHistory()
        
    def start_manual(self):
        """Manually start the study timer."""
        if self.state in ["STOPPED", "PAUSED"]:
            self.state = "STUDYING"
            self.last_tick = time.time()
            return "START_STUDY"
        return None
    
    def pause_manual(self):
        """Manually pause the study timer."""
        if self.state == "STUDYING":
            self.state = "PAUSED"
            return "PAUSE"
        return None
    
    def reset_timer(self):
        """Reset the current timer."""
        self.study_duration_seconds = 0
        self.state = "STOPPED"
        return "RESET"
    
    def start_break(self, is_long=False):
        """Start a break countdown."""
        self.state = "BREAK"
        self.break_remaining = self.long_break_limit if is_long else self.short_break_limit
        self.in_break_countdown = True
        return "BREAK_START"
    
    def skip_break(self):
        """Skip the current break."""
        self.in_break_countdown = False
        self.break_remaining = 0
        self.state = "STOPPED"
        return "BREAK_SKIP"
    
    def get_emotion_stats(self):
        """Get emotion breakdown percentages."""
        if self.total_emotion_samples == 0:
            return {}
        return {
            emotion: (count / self.total_emotion_samples) * 100
            for emotion, count in self.emotion_counts.items()
        }
    
    def get_focus_percentage(self):
        """Calculate focus percentage."""
        focused = self.emotion_counts.get("Focused", 0)
        if self.total_emotion_samples == 0:
            return 0.0
        return (focused / self.total_emotion_samples) * 100
        
    def update(self, detected_emotion):
        """
        Called every frame/cycle with the newly detected emotion.
        Returns the new state of the stopwatch, current duration, and an optional action trigger.
        """
        now = time.time()
        action_trigger = None
        elapsed = now - self.last_tick
        
        # Track emotion statistics
        if detected_emotion and detected_emotion != "No Face Detected":
            self.emotion_counts[detected_emotion] += 1
            self.total_emotion_samples += 1
        
        # Handle break countdown
        if self.in_break_countdown and self.state == "BREAK":
            self.break_remaining -= elapsed
            self.break_duration_seconds += elapsed
            if self.break_remaining <= 0:
                self.in_break_countdown = False
                self.break_remaining = 0
                self.state = "STOPPED"
                action_trigger = "BREAK_OVER"
            self.last_tick = now
            return self.state, self._format_break_time(), action_trigger
        
        # Accumulate study time if we are actively studying
        if self.state == "STUDYING":
            self.study_duration_seconds += elapsed
            
        self.last_tick = now
        
        # Handle no face detection - pause quickly as no face means not studying
        if detected_emotion in ["No Face Detected", "Unknown", None]:
            if self.no_face_start is None:
                self.no_face_start = now
            elif (now - self.no_face_start) >= config.no_face_pause_seconds and self.state == "STUDYING":
                self.state = "PAUSED"
                action_trigger = "NO_FACE"
                # Don't reset no_face_start so it stays paused while face is missing
        else:
            self.no_face_start = None
        
        # Check if the emotion changed
        if detected_emotion != self.current_emotion:
            self.current_emotion = detected_emotion
            self.emotion_start_time = now
            
        time_in_emotion = now - self.emotion_start_time
        
        # State transitions
        
        # 1. Start studying if focused for configured time
        if self.current_emotion == "Focused" and time_in_emotion >= config.focus_trigger_seconds and self.state not in ["STUDYING", "BREAK"]:
            self.state = "STUDYING"
            action_trigger = "START_STUDY"
            
        # 2. Pause and trigger break if Bored or Stressed for configured time
        elif self.current_emotion in ["Bored", "Stressed"] and time_in_emotion >= config.stress_trigger_seconds and self.state == "STUDYING":
            self.state = "PAUSED"
            action_trigger = "TAKE_BREAK"
            self.emotion_start_time = now  # Reset to avoid spamming
            
        # 3. Pomodoro limit reached
        if self.study_duration_seconds >= self.pomodoro_limit and self.state == "STUDYING":
            self.pomodoros_completed += 1
            self.study_duration_seconds = 0  # Reset for next pomodoro
            
            # Determine if long or short break
            if self.pomodoros_completed % config.pomodoros_before_long_break == 0:
                self.current_break_limit = self.long_break_limit
                action_trigger = "POMODORO_LONG"
            else:
                self.current_break_limit = self.short_break_limit
                action_trigger = "POMODORO"
            
            self.state = "BREAK"
            self.break_remaining = self.current_break_limit
            self.in_break_countdown = True
             
        # Format the time for UI display
        time_str = self._format_time()
        
        return self.state, time_str, action_trigger
    
    def _format_time(self):
        """Format study duration as HH:MM:SS."""
        m, s = divmod(int(self.study_duration_seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    def _format_break_time(self):
        """Format break remaining as MM:SS."""
        m, s = divmod(int(max(0, self.break_remaining)), 60)
        return f"Break: {m:02d}:{s:02d}"
    
    def get_session_stats(self) -> SessionStats:
        """Get current session statistics."""
        return SessionStats(
            start_time=self.session_start,
            end_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_study_seconds=self.study_duration_seconds,
            total_break_seconds=self.break_duration_seconds,
            pomodoros_completed=self.pomodoros_completed,
            emotion_breakdown=self.get_emotion_stats(),
            focus_percentage=self.get_focus_percentage()
        )
    
    def save_session(self):
        """Save current session to history."""
        stats = self.get_session_stats()
        self.history.add_session(stats)
        return stats
