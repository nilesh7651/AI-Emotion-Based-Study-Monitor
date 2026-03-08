import threading
import time
import json
import os
from camera import Camera
from classifier import EmotionClassifier, DeepFaceClassifier, create_classifier
from logic import StudyLogic
from actions import AIActionTrigger
from app_ui import AppUI
from config import config, SessionHistory
from user_manager import get_user_manager, FACE_RECOGNITION_AVAILABLE

class EmotionStopwatchApp:
    def __init__(self):
        self.running = True
        
        # Initialize modules
        print("Initializing Camera...")
        self.camera = Camera(src=config.camera_index)
        
        print(f"Initializing Emotion Classifier ({config.model_backend})...")
        print("This may take a moment to load model weights...")
        
        if config.model_backend.lower() == 'deepface':
            self.classifier = create_classifier(
                backend='deepface',
                smoothing_window=config.smoothing_window,
                confidence_threshold=config.confidence_threshold
            )
        else:
            self.classifier = create_classifier(
                backend='fer',
                use_mtcnn=config.use_mtcnn,
                smoothing_window=config.smoothing_window,
                confidence_threshold=config.confidence_threshold
            )
        
        self.logic = StudyLogic()
        self.actions = AIActionTrigger()
        self.history = SessionHistory()
        
        # Initialize multi-user face recognition
        print("Initializing User Manager...")
        self.user_manager = get_user_manager()
        if self.user_manager.is_available() and config.multi_user_enabled:
            print(f"Multi-user mode enabled. {len(self.user_manager.get_all_users())} users registered.")
        else:
            print("Multi-user mode disabled (face_recognition not available or disabled in config).")
        
        print("Initializing UI...")
        self.ui = AppUI(
            on_close_callback=self.stop,
            on_start=self.on_start,
            on_pause=self.on_pause,
            on_reset=self.on_reset,
            on_skip_break=self.on_skip_break
        )
        
        # Start background processing thread
        self.process_thread = threading.Thread(target=self.process_loop)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def on_start(self):
        """Handle manual start button click."""
        trigger = self.logic.start_manual()
        if trigger:
            self.actions.trigger(trigger)
    
    def on_pause(self):
        """Handle manual pause button click."""
        trigger = self.logic.pause_manual()
        if trigger:
            self.actions.trigger(trigger)
    
    def on_reset(self):
        """Handle reset button click."""
        trigger = self.logic.reset_timer()
        if trigger:
            self.actions.trigger(trigger)
    
    def on_skip_break(self):
        """Handle skip break button click."""
        trigger = self.logic.skip_break()
        if trigger:
            self.actions.trigger(trigger)
        
    def process_loop(self):
        # Allow UI to initialize before processing
        time.sleep(1) 
        
        frame_skip = config.frame_skip
        frame_count = 0
        last_user_time_update = time.time()
        
        while self.running:
            frame = self.camera.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
                
            frame_count += 1
            if frame_count % frame_skip != 0:
                time.sleep(0.01)
                continue
                
            # 1. Analyze Emotion
            box, raw_emotions, study_state = self.classifier.analyze_frame(frame)
            
            # 1.5. Multi-user face recognition
            current_user = None
            if self.user_manager.is_available() and config.multi_user_enabled:
                user_id = self.user_manager.recognize_user(frame)
                if user_id:
                    current_user = self.user_manager.get_user(user_id)
            
            # 2. Update Logic Engine
            stopwatch_state, time_str, action_trigger = self.logic.update(study_state)
            
            # 3. Fire Actions (if any)
            if action_trigger:
                self.actions.trigger(action_trigger)
            
            # 4. Get statistics
            emotion_stats = self.logic.get_emotion_stats()
            focus_pct = self.logic.get_focus_percentage()
            pomodoros = self.logic.pomodoros_completed
            today_stats = self.history.get_today_stats()
            today_seconds = today_stats.get("total_study_seconds", 0) + self.logic.study_duration_seconds
            
            # Get Pomodoro progress
            pomodoro_duration = self.logic.pomodoro_limit
            pomodoro_remaining = pomodoro_duration - self.logic.study_duration_seconds
            if pomodoro_remaining < 0:
                pomodoro_remaining = 0
                
            # 5. Track time for current user (use real elapsed time)
            current_time = time.time()
            elapsed_since_update = current_time - last_user_time_update
            last_user_time_update = current_time
            
            if current_user and stopwatch_state == "STUDYING":
                self.user_manager.update_session_time(
                    current_user.user_id, 
                    study_seconds=elapsed_since_update
                )
            elif current_user and stopwatch_state == "BREAK":
                self.user_manager.update_session_time(
                    current_user.user_id,
                    break_seconds=elapsed_since_update
                )
            
            # 6. Safely update UI from processing thread
            try:
                self.ui.after(10, self.ui.update_display, 
                    study_state, 
                    time_str, 
                    stopwatch_state, 
                    frame.copy(), 
                    box,
                    emotion_stats,
                    focus_pct,
                    pomodoros,
                    today_seconds,
                    current_user,
                    pomodoro_remaining,
                    pomodoro_duration
                )
            except Exception as e:
                # UI closed
                pass
            
            time.sleep(0.05)

    def stop(self):
        print("Saving study session and exiting...")
        self.running = False
        
        # Save multi-user sessions
        if self.user_manager.is_available() and config.multi_user_enabled:
            self.user_manager.save_all_sessions()
            print("Multi-user sessions saved.")
        
        # Save session to history
        if config.auto_save_sessions:
            stats = self.logic.save_session()
            print(f"Session saved: {stats.total_study_seconds:.0f}s studied, {stats.pomodoros_completed} pomodoros")
        
        # Save legacy report for backward compatibility
        report = {
            "total_study_seconds": round(self.logic.study_duration_seconds, 2),
            "total_break_seconds": round(self.logic.break_duration_seconds, 2),
            "pomodoros_completed": self.logic.pomodoros_completed,
            "focus_percentage": round(self.logic.get_focus_percentage(), 2),
            "emotion_breakdown": self.logic.get_emotion_stats(),
            "session_end": time.ctime()
        }
        
        with open("study_report.json", "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"Report saved. Total study time: {report['total_study_seconds']}s")
        self.camera.release()

    def run(self):
        # Starts the blocking Tkinter main loop
        self.ui.mainloop()

if __name__ == "__main__":
    app = EmotionStopwatchApp()
    app.run()
