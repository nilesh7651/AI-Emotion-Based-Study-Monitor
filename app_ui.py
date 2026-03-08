import customtkinter as ctk
from PIL import Image
import cv2
from config import config

# Try importing user manager
try:
    from user_manager import get_user_manager, FACE_RECOGNITION_AVAILABLE
    USER_MANAGER_AVAILABLE = True
except ImportError:
    USER_MANAGER_AVAILABLE = False
    FACE_RECOGNITION_AVAILABLE = False

# Try importing dashboard
try:
    from dashboard import DashboardWindow, ExercisePopup, EyeStrainStatusWidget
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False

# Try importing exercises
try:
    from exercises import BreakExerciseManager
    EXERCISES_AVAILABLE = True
except ImportError:
    EXERCISES_AVAILABLE = False

# Motivational tips for the app
MOTIVATIONAL_TIPS = [
    "💡 Tip: Stay hydrated! Drink water every 30 minutes.",
    "💡 Tip: Look at something 20ft away for 20 sec every 20 min.",
    "💡 Tip: Good posture = Better focus. Sit up straight!",
    "💡 Tip: Break complex tasks into smaller chunks.",
    "💡 Tip: Eliminate distractions before starting.",
    "💡 Tip: Reward yourself after completing a Pomodoro!",
    "💡 Tip: Regular breaks boost productivity by 30%.",
    "💡 Tip: Morning study is most effective for memory.",
    "🎯 Focus: One task at a time beats multitasking.",
    "🎯 Focus: Turn off phone notifications while studying.",
    "💪 Keep going! Consistency beats intensity.",
    "💪 You're doing great! Every minute counts.",
    "🧠 Learning is a journey, not a destination.",
    "🏆 Champions are made in the moments they choose to try again.",
]

class AppUI(ctk.CTk):
    def __init__(self, on_close_callback, on_start=None, on_pause=None, on_reset=None, on_skip_break=None, on_settings=None):
        super().__init__()
        
        self.on_close_callback = on_close_callback
        self.on_start = on_start
        self.on_pause = on_pause
        self.on_reset = on_reset
        self.on_skip_break = on_skip_break
        self.on_settings = on_settings
        
        self.title("🎓 AI Study Monitor - Focus & Productivity")
        self.geometry("950x650")
        self.minsize(850, 550)
        
        if config.always_on_top:
            self.attributes('-topmost', True)
        
        ctk.set_appearance_mode(config.theme)
        ctk.set_default_color_theme("blue")
        
        # Configure grid - Header, Main, Controls, Status
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Main content
        self.grid_rowconfigure(2, weight=0)  # Controls
        self.grid_rowconfigure(3, weight=0)  # Status bar
        
        self._create_header()
        self._create_camera_panel()
        self._create_info_panel()
        self._create_control_bar()
        self._create_status_bar()
        
        # Store photo reference
        self._photo = None
        
        # Current frame for user registration
        self._current_frame = None
        
        # Tip rotation
        self._current_tip_index = 0
        self._rotate_tip()
        
        # Bind keyboard shortcuts
        self._setup_keyboard_shortcuts()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _create_header(self):
        """Create app header with branding and quick info."""
        self.header_frame = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        # App title with icon
        title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        self.lbl_app_title = ctk.CTkLabel(
            title_frame,
            text="🎓 AI Study Monitor",
            font=("Helvetica", 18, "bold")
        )
        self.lbl_app_title.pack(side="left")
        
        self.lbl_app_subtitle = ctk.CTkLabel(
            title_frame,
            text="  |  Emotion-Based Focus Tracking",
            font=("Helvetica", 11),
            text_color="gray"
        )
        self.lbl_app_subtitle.pack(side="left", padx=(5, 0))
        
        # Keyboard shortcuts hint
        shortcuts_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        shortcuts_frame.grid(row=0, column=1, padx=15, pady=8, sticky="e")
        
        shortcuts_text = "⌨️ Space: Start/Pause  |  R: Reset  |  S: Skip  |  D: Dashboard"
        self.lbl_shortcuts = ctk.CTkLabel(
            shortcuts_frame,
            text=shortcuts_text,
            font=("Helvetica", 9),
            text_color="gray"
        )
        self.lbl_shortcuts.pack()
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for quick actions."""
        self.bind("<space>", lambda e: self._toggle_start_pause())
        self.bind("<r>", lambda e: self._on_reset_click())
        self.bind("<R>", lambda e: self._on_reset_click())
        self.bind("<s>", lambda e: self._on_skip_click())
        self.bind("<S>", lambda e: self._on_skip_click())
        self.bind("<d>", lambda e: self._open_dashboard())
        self.bind("<D>", lambda e: self._open_dashboard())
        self.bind("<Escape>", lambda e: self.on_close())
    
    def _toggle_start_pause(self):
        """Toggle between start and pause."""
        current_state = self.lbl_state.cget("text")
        if "STUDYING" in current_state:
            if self.on_pause:
                self.on_pause()
        else:
            if self.on_start:
                self.on_start()
    
    def _create_status_bar(self):
        """Create status bar at the bottom."""
        self.status_frame = ctk.CTkFrame(self, height=30, corner_radius=0, fg_color=("#E8E8E8", "#1A1A1A"))
        self.status_frame.grid(row=3, column=0, columnspan=2, sticky="ew")
        self.status_frame.grid_columnconfigure(1, weight=1)
        
        # Connection status
        self.lbl_camera_status = ctk.CTkLabel(
            self.status_frame,
            text="📷 Camera: Active",
            font=("Helvetica", 9),
            text_color="gray"
        )
        self.lbl_camera_status.grid(row=0, column=0, padx=15, pady=5, sticky="w")
        
        # Tip display in center
        self.lbl_tip = ctk.CTkLabel(
            self.status_frame,
            text="💡 Tip: Stay focused!",
            font=("Helvetica", 9),
            text_color="gray"
        )
        self.lbl_tip.grid(row=0, column=1, pady=5)
        
        # Version/time
        import datetime
        self.lbl_time_now = ctk.CTkLabel(
            self.status_frame,
            text=datetime.datetime.now().strftime("%H:%M"),
            font=("Helvetica", 9),
            text_color="gray"
        )
        self.lbl_time_now.grid(row=0, column=2, padx=15, pady=5, sticky="e")
        
        # Update time every minute
        self._update_status_time()
    
    def _update_status_time(self):
        """Update the time in status bar."""
        import datetime
        self.lbl_time_now.configure(text=datetime.datetime.now().strftime("%H:%M"))
        self.after(60000, self._update_status_time)
    
    def _rotate_tip(self):
        """Rotate motivational tips every 30 seconds."""
        import random
        tip = random.choice(MOTIVATIONAL_TIPS)
        if hasattr(self, 'lbl_tip'):
            self.lbl_tip.configure(text=tip)
        self.after(30000, self._rotate_tip)
    
    def _create_camera_panel(self):
        """Create the left panel with camera display and emotion bars."""
        self.camera_frame = ctk.CTkFrame(self, corner_radius=10)
        self.camera_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.camera_frame.grid_columnconfigure(0, weight=1)
        
        # Camera title with face quality indicator
        title_row = ctk.CTkFrame(self.camera_frame, fg_color="transparent")
        title_row.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        title_row.grid_columnconfigure(0, weight=1)
        
        self.lbl_camera_title = ctk.CTkLabel(
            title_row, 
            text="📷 Live Camera", 
            font=("Helvetica", 14, "bold")
        )
        self.lbl_camera_title.pack(side="left", padx=10)
        
        # Face quality indicator
        self.lbl_face_quality = ctk.CTkLabel(
            title_row,
            text="◉ Face OK",
            font=("Helvetica", 10),
            text_color="#2ECC71"
        )
        self.lbl_face_quality.pack(side="right", padx=10)
        
        # Camera display with border
        camera_container = ctk.CTkFrame(self.camera_frame, fg_color="#1A1A1A", corner_radius=8)
        camera_container.grid(row=1, column=0, padx=10, pady=5)
        
        self.lbl_camera = ctk.CTkLabel(
            camera_container, 
            text="📷 Camera Loading...", 
            width=360, 
            height=270,
            font=("Helvetica", 12)
        )
        self.lbl_camera.pack(padx=3, pady=3)
        
        # Emotion bars section with better design
        if config.show_emotion_bars:
            self.emotion_title = ctk.CTkLabel(
                self.camera_frame,
                text="📊 Emotion Analysis",
                font=("Helvetica", 12, "bold")
            )
            self.emotion_title.grid(row=2, column=0, pady=(10, 5))
            
            self.emotion_bars_frame = ctk.CTkFrame(self.camera_frame)
            self.emotion_bars_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
            
            self.emotion_bars = {}
            emotions = ["Focused", "Stressed", "Bored", "Distracted"]
            colors = {"Focused": "#2ECC71", "Stressed": "#E74C3C", "Bored": "#F39C12", "Distracted": "#9B59B6"}
            icons = {"Focused": "🎯", "Stressed": "😰", "Bored": "😴", "Distracted": "🤔"}
            
            for i, emotion in enumerate(emotions):
                row = ctk.CTkFrame(self.emotion_bars_frame, fg_color="transparent")
                row.pack(fill="x", pady=2, padx=5)
                
                icon_lbl = ctk.CTkLabel(row, text=icons.get(emotion, ""), width=25)
                icon_lbl.pack(side="left")
                
                lbl = ctk.CTkLabel(row, text=emotion, width=70, anchor="w", font=("Helvetica", 11))
                lbl.pack(side="left")
                
                bar = ctk.CTkProgressBar(row, width=180, height=14)
                bar.pack(side="left", padx=5)
                bar.set(0)
                bar.configure(progress_color=colors.get(emotion, "#3498DB"))
                
                pct = ctk.CTkLabel(row, text="0%", width=40, font=("Helvetica", 11, "bold"))
                pct.pack(side="left")
                
                self.emotion_bars[emotion] = {"bar": bar, "label": pct}
    
    def _create_info_panel(self):
        """Create the right panel with timer and stats."""
        self.info_frame = ctk.CTkFrame(self, corner_radius=10)
        self.info_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.info_frame.grid_columnconfigure(0, weight=1)
        
        # Current emotion with styled badge
        emotion_container = ctk.CTkFrame(self.info_frame)
        emotion_container.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="ew")
        
        self.lbl_emotion = ctk.CTkLabel(
            emotion_container, 
            text="😐 Status: Initializing...", 
            font=("Helvetica", 18)
        )
        self.lbl_emotion.pack(pady=8)
        
        # Timer section with Pomodoro progress
        timer_section = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        timer_section.grid(row=1, column=0, pady=(5, 5))
        
        # Large timer display
        self.lbl_time = ctk.CTkLabel(
            timer_section, 
            text="00:00:00", 
            font=("Helvetica", 52, "bold")
        )
        self.lbl_time.pack()
        
        # Pomodoro progress bar (under timer)
        self.pomodoro_progress_frame = ctk.CTkFrame(timer_section, fg_color="transparent")
        self.pomodoro_progress_frame.pack(fill="x", pady=(5, 0))
        
        ctk.CTkLabel(
            self.pomodoro_progress_frame,
            text="🍅 Pomodoro:",
            font=("Helvetica", 10)
        ).pack(side="left", padx=(20, 5))
        
        self.pomodoro_progress_bar = ctk.CTkProgressBar(self.pomodoro_progress_frame, width=200, height=12)
        self.pomodoro_progress_bar.pack(side="left", padx=5)
        self.pomodoro_progress_bar.set(0)
        self.pomodoro_progress_bar.configure(progress_color="#E74C3C")
        
        self.lbl_pomodoro_time = ctk.CTkLabel(
            self.pomodoro_progress_frame,
            text="25:00",
            font=("Helvetica", 10, "bold")
        )
        self.lbl_pomodoro_time.pack(side="left", padx=5)
        
        # State label with badge styling
        self.state_badge = ctk.CTkFrame(self.info_frame, corner_radius=15)
        self.state_badge.grid(row=2, column=0, pady=(5, 10))
        
        self.lbl_state = ctk.CTkLabel(
            self.state_badge, 
            text="  ⏹ STOPPED  ", 
            font=("Helvetica", 14, "bold"), 
            text_color="white"
        )
        self.lbl_state.pack(padx=15, pady=5)
        self.state_badge.configure(fg_color="gray")
        
        # Stats cards with improved design
        self.stats_frame = ctk.CTkFrame(self.info_frame, fg_color="transparent")
        self.stats_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Pomodoro counter card
        self.pomodoro_frame = self._create_stat_card_ui(
            self.stats_frame, "🍅", "Pomodoros", "0", 0, "#E74C3C"
        )
        self.lbl_pomodoros = self.pomodoro_frame["value_label"]
        
        # Focus percentage card
        self.focus_frame = self._create_stat_card_ui(
            self.stats_frame, "🎯", "Focus Rate", "0%", 1, "#2ECC71"
        )
        self.lbl_focus = self.focus_frame["value_label"]
        
        # Today's total card
        self.today_frame = self._create_stat_card_ui(
            self.stats_frame, "📅", "Today", "0h 0m", 2, "#3498DB"
        )
        self.lbl_today = self.today_frame["value_label"]
        
        # Current user frame (for multi-user mode)
        self.user_frame = ctk.CTkFrame(self.info_frame)
        self.user_frame.grid(row=4, column=0, padx=15, pady=(5, 5), sticky="ew")
        self.user_frame.grid_columnconfigure((0, 1), weight=1)
        
        user_info_left = ctk.CTkFrame(self.user_frame, fg_color="transparent")
        user_info_left.grid(row=0, column=0, padx=10, pady=8, sticky="w")
        
        self.lbl_user_title = ctk.CTkLabel(
            user_info_left, 
            text="👤 Current User", 
            font=("Helvetica", 11, "bold")
        )
        self.lbl_user_title.pack(anchor="w")
        
        self.lbl_user_name = ctk.CTkLabel(
            user_info_left, 
            text="Not Recognized", 
            font=("Helvetica", 14),
            text_color="gray"
        )
        self.lbl_user_name.pack(anchor="w")
        
        user_info_right = ctk.CTkFrame(self.user_frame, fg_color="transparent")
        user_info_right.grid(row=0, column=1, padx=10, pady=8, sticky="e")
        
        self.lbl_user_time = ctk.CTkLabel(
            user_info_right, 
            text="Total: 0h 0m", 
            font=("Helvetica", 12, "bold"),
            text_color="#3498DB"
        )
        self.lbl_user_time.pack(anchor="e")
        
        # Quick session history
        self._create_session_history_section()
    
    def _create_stat_card_ui(self, parent, icon, title, value, column, accent_color):
        """Create a stylized stat card."""
        card = ctk.CTkFrame(parent, corner_radius=10)
        card.grid(row=0, column=column, padx=5, pady=5, sticky="nsew")
        
        # Icon with accent color
        icon_label = ctk.CTkLabel(
            card,
            text=icon,
            font=("Helvetica", 24)
        )
        icon_label.pack(pady=(10, 0))
        
        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Helvetica", 10),
            text_color="gray"
        )
        title_label.pack()
        
        # Value with accent color
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Helvetica", 22, "bold"),
            text_color=accent_color
        )
        value_label.pack(pady=(0, 10))
        
        return {"frame": card, "value_label": value_label}
    
    def _create_session_history_section(self):
        """Create a mini session history view."""
        history_frame = ctk.CTkFrame(self.info_frame)
        history_frame.grid(row=5, column=0, padx=15, pady=(5, 10), sticky="ew")
        
        header = ctk.CTkFrame(history_frame, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 5))
        
        ctk.CTkLabel(
            header,
            text="📊 Recent Sessions",
            font=("Helvetica", 11, "bold")
        ).pack(side="left")
        
        # Load last 3 sessions
        self.session_list_frame = ctk.CTkFrame(history_frame, fg_color="transparent")
        self.session_list_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        # Will be populated when data is available
        self._update_session_history()
    
    def _create_control_bar(self):
        """Create the bottom control bar with grouped buttons."""
        self.control_frame = ctk.CTkFrame(self, corner_radius=10)
        self.control_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 5), sticky="ew")
        
        # Use pack for better organization
        controls_inner = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        controls_inner.pack(pady=8, padx=10)
        
        # === Timer Controls Group ===
        timer_group = ctk.CTkFrame(controls_inner, fg_color="transparent")
        timer_group.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(timer_group, text="Timer", font=("Helvetica", 9), text_color="gray").pack(side="top")
        
        timer_btns = ctk.CTkFrame(timer_group, fg_color="transparent")
        timer_btns.pack(side="top")
        
        self.btn_start = ctk.CTkButton(
            timer_btns, 
            text="▶ Start", 
            command=self._on_start_click,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            width=75,
            height=32
        )
        self.btn_start.pack(side="left", padx=2)
        
        self.btn_pause = ctk.CTkButton(
            timer_btns, 
            text="⏸ Pause", 
            command=self._on_pause_click,
            fg_color="#F39C12",
            hover_color="#D68910",
            width=75,
            height=32
        )
        self.btn_pause.pack(side="left", padx=2)
        
        self.btn_reset = ctk.CTkButton(
            timer_btns, 
            text="🔄 Reset", 
            command=self._on_reset_click,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=75,
            height=32
        )
        self.btn_reset.pack(side="left", padx=2)
        
        # Separator
        sep1 = ctk.CTkFrame(controls_inner, width=2, height=40, fg_color="gray")
        sep1.pack(side="left", padx=10)
        
        # === Pomodoro Group ===
        pomo_group = ctk.CTkFrame(controls_inner, fg_color="transparent")
        pomo_group.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(pomo_group, text="Pomodoro", font=("Helvetica", 9), text_color="gray").pack(side="top")
        
        self.btn_skip = ctk.CTkButton(
            pomo_group, 
            text="⏭ Skip Break", 
            command=self._on_skip_click,
            fg_color="#9B59B6",
            hover_color="#8E44AD",
            width=90,
            height=32
        )
        self.btn_skip.pack(side="top", pady=(2, 0))
        
        # Separator
        sep2 = ctk.CTkFrame(controls_inner, width=2, height=40, fg_color="gray")
        sep2.pack(side="left", padx=10)
        
        # === Features Group ===
        features_group = ctk.CTkFrame(controls_inner, fg_color="transparent")
        features_group.pack(side="left", padx=(0, 15))
        
        ctk.CTkLabel(features_group, text="Features", font=("Helvetica", 9), text_color="gray").pack(side="top")
        
        features_btns = ctk.CTkFrame(features_group, fg_color="transparent")
        features_btns.pack(side="top")
        
        self.btn_users = ctk.CTkButton(
            features_btns,
            text="👥 Users",
            command=self._open_user_manager,
            fg_color="#3498DB",
            hover_color="#2980B9",
            width=70,
            height=32
        )
        self.btn_users.pack(side="left", padx=2)
        
        self.btn_dashboard = ctk.CTkButton(
            features_btns,
            text="📊 Stats",
            command=self._open_dashboard,
            fg_color="#1ABC9C",
            hover_color="#16A085",
            width=70,
            height=32
        )
        self.btn_dashboard.pack(side="left", padx=2)
        
        # Separator
        sep3 = ctk.CTkFrame(controls_inner, width=2, height=40, fg_color="gray")
        sep3.pack(side="left", padx=10)
        
        # === Preferences Group ===
        prefs_group = ctk.CTkFrame(controls_inner, fg_color="transparent")
        prefs_group.pack(side="left")
        
        ctk.CTkLabel(prefs_group, text="Settings", font=("Helvetica", 9), text_color="gray").pack(side="top")
        
        prefs_btns = ctk.CTkFrame(prefs_group, fg_color="transparent")
        prefs_btns.pack(side="top")
        
        self.btn_theme = ctk.CTkButton(
            prefs_btns,
            text="🌙",
            command=self._toggle_theme,
            fg_color="#34495E",
            hover_color="#2C3E50",
            width=35,
            height=32
        )
        self.btn_theme.pack(side="left", padx=2)
        
        self.btn_settings = ctk.CTkButton(
            prefs_btns, 
            text="⚙",
            command=self._on_settings_click,
            fg_color="#7F8C8D",
            hover_color="#626D71",
            width=35,
            height=32
        )
        self.btn_settings.pack(side="left", padx=2)
    
    def _update_session_history(self):
        """Update the session history display."""
        # Clear existing
        for widget in self.session_list_frame.winfo_children():
            widget.destroy()
        
        # Try to load session history
        try:
            import json
            import os
            history_path = os.path.join(os.path.dirname(__file__), "session_history.json")
            
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    sessions = json.load(f)
                
                # Get last 3 sessions
                recent = sessions[-3:] if len(sessions) >= 3 else sessions
                recent.reverse()  # Most recent first
                
                for session in recent:
                    row = ctk.CTkFrame(self.session_list_frame, fg_color="transparent")
                    row.pack(fill="x", pady=1)
                    
                    # Date
                    date_str = session.get('date', 'Unknown')
                    if 'T' in date_str:
                        date_str = date_str.split('T')[0]
                    
                    ctk.CTkLabel(
                        row,
                        text=f"📅 {date_str}",
                        font=("Helvetica", 9),
                        text_color="gray"
                    ).pack(side="left")
                    
                    # Duration and pomodoros
                    duration = session.get('total_study_seconds', 0)
                    h, r = divmod(int(duration), 3600)
                    m = r // 60
                    pomos = session.get('pomodoros_completed', 0)
                    
                    ctk.CTkLabel(
                        row,
                        text=f"{h}h {m}m | 🍅{pomos}",
                        font=("Helvetica", 9, "bold")
                    ).pack(side="right")
            else:
                ctk.CTkLabel(
                    self.session_list_frame,
                    text="No sessions yet. Start studying!",
                    font=("Helvetica", 9),
                    text_color="gray"
                ).pack()
        except Exception:
            ctk.CTkLabel(
                self.session_list_frame,
                text="Start studying to see history",
                font=("Helvetica", 9),
                text_color="gray"
            ).pack()
    
    def _on_start_click(self):
        if self.on_start:
            self.on_start()
    
    def _on_pause_click(self):
        if self.on_pause:
            self.on_pause()
    
    def _on_reset_click(self):
        if self.on_reset:
            self.on_reset()
    
    def _on_skip_click(self):
        if self.on_skip_break:
            self.on_skip_break()
    
    def _on_settings_click(self):
        if self.on_settings:
            self.on_settings()
        else:
            self._open_settings_dialog()
    
    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        current = ctk.get_appearance_mode()
        new_theme = "light" if current == "Dark" else "dark"
        ctk.set_appearance_mode(new_theme)
        config.theme = new_theme
        config.save()
    
    def _open_dashboard(self):
        """Open the analytics dashboard."""
        if DASHBOARD_AVAILABLE:
            dashboard = DashboardWindow(self)
            dashboard.grab_set()
        else:
            print("Dashboard not available - missing dependencies")
    
    def show_exercise_popup(self, exercise=None):
        """Show a break exercise popup during breaks."""
        if not EXERCISES_AVAILABLE:
            return
        
        if exercise is None:
            manager = BreakExerciseManager()
            exercise = manager.get_suggestion()
        
        if DASHBOARD_AVAILABLE:
            popup = ExercisePopup(self, exercise)
            popup.grab_set()
    
    def _open_settings_dialog(self):
        """Open a settings dialog."""
        dialog = SettingsDialog(self)
        dialog.grab_set()
    
    def update_camera(self, frame, box=None):
        """Update the camera display with a new frame."""
        if frame is None or not config.show_camera:
            return
        
        # Mirror camera if enabled
        if config.mirror_camera:
            frame = cv2.flip(frame, 1)
            
        # Draw face bounding box if detected
        if box is not None:
            x, y, w, h = box
            # Adjust x for mirrored frame
            if config.mirror_camera:
                x = frame.shape[1] - x - w
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Update face quality indicator
            self.lbl_face_quality.configure(text="◉ Face OK", text_color="#2ECC71")
            self.lbl_camera_status.configure(text="📷 Camera: Active | Face: ✅")
        else:
            # No face detected
            self.lbl_face_quality.configure(text="○ No Face", text_color="#E74C3C")
            self.lbl_camera_status.configure(text="📷 Camera: Active | Face: ❌")
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Resize to fit display (larger for new UI)
        frame_resized = cv2.resize(frame_rgb, (360, 270))
        
        # Convert to PIL Image then to CTkImage
        img = Image.fromarray(frame_resized)
        self._photo = ctk.CTkImage(light_image=img, dark_image=img, size=(360, 270))
        
        # Update the label
        self.lbl_camera.configure(image=self._photo, text="")
        
    def update_display(self, emotion_text, time_str, state, frame=None, box=None, 
                       emotion_stats=None, focus_pct=0, pomodoros=0, today_seconds=0, current_user=None,
                       pomodoro_remaining=None, pomodoro_duration=None):
        """Update all UI elements."""
        # Emotion with emoji
        emoji = self._get_emotion_emoji(emotion_text)
        self.lbl_emotion.configure(text=f"{emoji} {emotion_text}")
        self.lbl_time.configure(text=time_str)
        
        # State with color and badge
        state_config = {
            "STUDYING": {"color": "#2ECC71", "icon": "▶", "text": "STUDYING"},
            "PAUSED": {"color": "#E74C3C", "icon": "⏸", "text": "PAUSED"},
            "BREAK": {"color": "#9B59B6", "icon": "☕", "text": "BREAK TIME"},
            "STOPPED": {"color": "gray", "icon": "⏹", "text": "STOPPED"}
        }
        cfg = state_config.get(state, state_config["STOPPED"])
        self.state_badge.configure(fg_color=cfg["color"])
        self.lbl_state.configure(text=f"  {cfg['icon']} {cfg['text']}  ")
        
        # Update Pomodoro progress bar
        if pomodoro_remaining is not None and pomodoro_duration is not None and pomodoro_duration > 0:
            progress = 1.0 - (pomodoro_remaining / pomodoro_duration)
            self.pomodoro_progress_bar.set(max(0, min(1, progress)))
            
            # Format remaining time
            mins, secs = divmod(int(pomodoro_remaining), 60)
            self.lbl_pomodoro_time.configure(text=f"{mins:02d}:{secs:02d}")
            
            # Change color based on progress
            if progress > 0.8:
                self.pomodoro_progress_bar.configure(progress_color="#2ECC71")  # Almost done - green
            elif progress > 0.5:
                self.pomodoro_progress_bar.configure(progress_color="#F39C12")  # Halfway - orange
            else:
                self.pomodoro_progress_bar.configure(progress_color="#E74C3C")  # Just started - red
        else:
            self.pomodoro_progress_bar.set(0)
            pomo_mins = getattr(config, 'pomodoro_duration_minutes', 25)
            self.lbl_pomodoro_time.configure(text=f"{pomo_mins}:00")
        
        # Update stats
        self.lbl_pomodoros.configure(text=str(pomodoros))
        self.lbl_focus.configure(text=f"{focus_pct:.0f}%")
        
        # Update focus color based on percentage
        if focus_pct >= 75:
            self.lbl_focus.configure(text_color="#2ECC71")
        elif focus_pct >= 50:
            self.lbl_focus.configure(text_color="#F39C12")
        else:
            self.lbl_focus.configure(text_color="#E74C3C")
        
        # Format today's time
        h, remainder = divmod(int(today_seconds), 3600)
        m = remainder // 60
        self.lbl_today.configure(text=f"{h}h {m}m")
        
        # Update current user display
        if current_user:
            self.lbl_user_name.configure(text=current_user.name, text_color="#2ECC71")
            user_total = current_user.total_study_seconds
            uh, ur = divmod(int(user_total), 3600)
            um = ur // 60
            self.lbl_user_time.configure(text=f"Total: {uh}h {um}m")
        else:
            self.lbl_user_name.configure(text="Not Recognized", text_color="gray")
            self.lbl_user_time.configure(text="Click 'Users' to register")
        
        # Update emotion bars
        if emotion_stats and config.show_emotion_bars:
            for emotion, data in self.emotion_bars.items():
                pct = emotion_stats.get(emotion, 0)
                data["bar"].set(pct / 100)
                data["label"].configure(text=f"{pct:.0f}%")
        
        # Update camera feed and store current frame
        if frame is not None:
            self._current_frame = frame.copy()
            self.update_camera(frame, box)
    
    def _get_emotion_emoji(self, emotion):
        """Get emoji for emotion state."""
        emojis = {
            "Focused": "🎯",
            "Stressed": "😰",
            "Bored": "😴",
            "Distracted": "🤔",
            "No Face Detected": "👻"
        }
        return emojis.get(emotion, "😐")
    
    def _open_user_manager(self):
        """Open the user management dialog."""
        if USER_MANAGER_AVAILABLE and FACE_RECOGNITION_AVAILABLE:
            dialog = UserManagerDialog(self, self._current_frame)
            dialog.grab_set()
        else:
            # Show error message
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Multi-User Mode")
            error_dialog.geometry("400x150")
            error_dialog.transient(self)
            
            ctk.CTkLabel(
                error_dialog, 
                text="⚠️ Face Recognition Not Available",
                font=("Helvetica", 14, "bold")
            ).pack(pady=20)
            
            ctk.CTkLabel(
                error_dialog,
                text="Install with: pip install face_recognition\n\nNote: On Windows, you may need to install\ndlib first using conda or pre-built wheels.",
                justify="center"
            ).pack(pady=10)
            
            ctk.CTkButton(
                error_dialog,
                text="OK",
                command=error_dialog.destroy,
                width=100
            ).pack(pady=10)

    def on_close(self):
        self.on_close_callback()
        self.destroy()


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog window."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Settings")
        self.geometry("400x500")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Scrollable frame
        self.scroll = ctk.CTkScrollableFrame(self, width=380, height=440)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Pomodoro Settings
        ctk.CTkLabel(self.scroll, text="🍅 Pomodoro Settings", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(10, 5))
        
        self._add_slider("Work Duration (min)", config.pomodoro_duration_minutes, 5, 60, "pomodoro_duration_minutes")
        self._add_slider("Short Break (min)", config.short_break_minutes, 1, 15, "short_break_minutes")
        self._add_slider("Long Break (min)", config.long_break_minutes, 5, 30, "long_break_minutes")
        
        # Detection Settings
        ctk.CTkLabel(self.scroll, text="🎯 Detection Settings", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(20, 5))
        
        self._add_slider("Focus Trigger (sec)", config.focus_trigger_seconds, 1, 30, "focus_trigger_seconds")
        self._add_slider("Stress Trigger (sec)", config.stress_trigger_seconds, 5, 60, "stress_trigger_seconds")
        
        # UI Settings
        ctk.CTkLabel(self.scroll, text="🖥 UI Settings", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(20, 5))
        
        self._add_toggle("Always on Top", config.always_on_top, "always_on_top")
        self._add_toggle("Show Emotion Bars", config.show_emotion_bars, "show_emotion_bars")
        self._add_toggle("Mirror Camera", config.mirror_camera, "mirror_camera")
        
        # Audio Settings
        ctk.CTkLabel(self.scroll, text="🔊 Audio Settings", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(20, 5))
        
        self._add_toggle("Voice Enabled", config.voice_enabled, "voice_enabled")
        self._add_toggle("Sound Effects", config.sound_enabled, "sound_enabled")
        self._add_slider("Volume", config.volume * 100, 0, 100, "volume", is_float=True)
        
        # Save button
        ctk.CTkButton(self.scroll, text="💾 Save Settings", command=self._save).pack(pady=20)
    
    def _add_slider(self, label, value, min_val, max_val, config_key, is_float=False):
        """Add a labeled slider."""
        frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(frame, text=label, width=150, anchor="w").pack(side="left")
        
        var = ctk.StringVar(value=str(int(value)))
        
        def on_change(val):
            var.set(f"{int(float(val))}")
        
        slider = ctk.CTkSlider(frame, from_=min_val, to=max_val, command=on_change, width=150)
        slider.set(value)
        slider.pack(side="left", padx=5)
        
        lbl = ctk.CTkLabel(frame, textvariable=var, width=40)
        lbl.pack(side="left")
        
        # Store reference for saving
        slider._config_key = config_key
        slider._is_float = is_float
        if not hasattr(self, '_sliders'):
            self._sliders = []
        self._sliders.append(slider)
    
    def _add_toggle(self, label, value, config_key):
        """Add a labeled toggle switch."""
        frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        ctk.CTkLabel(frame, text=label, width=150, anchor="w").pack(side="left")
        
        switch = ctk.CTkSwitch(frame, text="")
        if value:
            switch.select()
        switch.pack(side="left", padx=5)
        
        switch._config_key = config_key
        if not hasattr(self, '_switches'):
            self._switches = []
        self._switches.append(switch)
    
    def _save(self):
        """Save all settings to config."""
        # Save sliders
        for slider in getattr(self, '_sliders', []):
            val = slider.get()
            if slider._is_float:
                val = val / 100  # Convert percentage to 0-1
            else:
                val = int(val)
            setattr(config, slider._config_key, val)
        
        # Save toggles
        for switch in getattr(self, '_switches', []):
            setattr(config, switch._config_key, switch.get() == 1)
        
        config.save()
        self.destroy()


class UserManagerDialog(ctk.CTkToplevel):
    """User management dialog for multi-user mode."""
    
    def __init__(self, parent, current_frame=None):
        super().__init__(parent)
        
        self.title("👥 User Management")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        
        # Store parent reference to get latest frames
        self.parent_ui = parent
        self.user_manager = get_user_manager() if USER_MANAGER_AVAILABLE else None
        
        self._create_widgets()
        self._refresh_user_list()
    
    def _create_widgets(self):
        # Title
        ctk.CTkLabel(
            self, 
            text="👥 Multi-User Face Recognition",
            font=("Helvetica", 18, "bold")
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            self,
            text="Register users to track study time separately",
            font=("Helvetica", 11),
            text_color="gray"
        ).pack(pady=(0, 15))
        
        # Registration section
        reg_frame = ctk.CTkFrame(self)
        reg_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            reg_frame,
            text="📝 Register New User",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.name_entry = ctk.CTkEntry(
            reg_frame,
            placeholder_text="Enter your name...",
            width=300
        )
        self.name_entry.pack(padx=10, pady=5)
        
        self.register_btn = ctk.CTkButton(
            reg_frame,
            text="📷 Capture & Register",
            command=self._register_user,
            fg_color="#2ECC71",
            hover_color="#27AE60",
            width=200
        )
        self.register_btn.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(
            reg_frame,
            text="Position your face clearly in the camera",
            font=("Helvetica", 10),
            text_color="gray"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Users list section
        list_frame = ctk.CTkFrame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(
            list_frame,
            text="📋 Registered Users",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Scrollable user list
        self.users_scroll = ctk.CTkScrollableFrame(list_frame, height=250)
        self.users_scroll.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Leaderboard section
        lb_frame = ctk.CTkFrame(self)
        lb_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            lb_frame,
            text="🏆 Study Leaderboard",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.leaderboard_frame = ctk.CTkFrame(lb_frame, fg_color="transparent")
        self.leaderboard_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Close button
        ctk.CTkButton(
            self,
            text="Close",
            command=self.destroy,
            width=100
        ).pack(pady=10)
    
    def _refresh_user_list(self):
        """Refresh the list of registered users."""
        # Clear existing widgets
        for widget in self.users_scroll.winfo_children():
            widget.destroy()
        
        if not self.user_manager:
            ctk.CTkLabel(
                self.users_scroll,
                text="User manager not available",
                text_color="gray"
            ).pack(pady=20)
            return
        
        users = self.user_manager.get_all_users()
        
        if not users:
            ctk.CTkLabel(
                self.users_scroll,
                text="No users registered yet.\nRegister yourself above!",
                text_color="gray"
            ).pack(pady=20)
        else:
            for user in users:
                self._create_user_row(user)
        
        # Refresh leaderboard
        self._refresh_leaderboard()
    
    def _create_user_row(self, user):
        """Create a row for a user in the list."""
        row = ctk.CTkFrame(self.users_scroll)
        row.pack(fill="x", pady=2)
        row.grid_columnconfigure(1, weight=1)
        
        # User icon
        ctk.CTkLabel(row, text="👤", font=("Helvetica", 16)).grid(row=0, column=0, padx=(10, 5), pady=5)
        
        # User info
        info_frame = ctk.CTkFrame(row, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        ctk.CTkLabel(
            info_frame,
            text=user.name,
            font=("Helvetica", 12, "bold"),
            anchor="w"
        ).pack(anchor="w")
        
        # Format study time
        h, r = divmod(int(user.total_study_seconds), 3600)
        m = r // 60
        ctk.CTkLabel(
            info_frame,
            text=f"📚 {h}h {m}m | 🍅 {user.total_pomodoros} pomodoros",
            font=("Helvetica", 10),
            text_color="gray",
            anchor="w"
        ).pack(anchor="w")
        
        # Delete button
        ctk.CTkButton(
            row,
            text="🗑️",
            command=lambda uid=user.user_id: self._delete_user(uid),
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=40,
            height=30
        ).grid(row=0, column=2, padx=10, pady=5)
    
    def _refresh_leaderboard(self):
        """Refresh the leaderboard display."""
        for widget in self.leaderboard_frame.winfo_children():
            widget.destroy()
        
        if not self.user_manager:
            return
        
        leaderboard = self.user_manager.get_leaderboard()[:5]  # Top 5
        
        if not leaderboard:
            return
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        
        for i, entry in enumerate(leaderboard):
            row = ctk.CTkFrame(self.leaderboard_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            
            medal = medals[i] if i < len(medals) else f"{i+1}."
            h, r = divmod(int(entry["total_seconds"]), 3600)
            m = r // 60
            
            ctk.CTkLabel(
                row,
                text=f"{medal} {entry['name']}",
                font=("Helvetica", 11),
                anchor="w",
                width=200
            ).pack(side="left", padx=5)
            
            ctk.CTkLabel(
                row,
                text=f"{h}h {m}m",
                font=("Helvetica", 11, "bold"),
                anchor="e"
            ).pack(side="right", padx=5)
    
    def _register_user(self):
        """Register a new user with face capture."""
        name = self.name_entry.get().strip()
        
        if not name:
            self.status_label.configure(text="⚠️ Please enter a name", text_color="#E74C3C")
            return
        
        # Get the LATEST frame from parent UI
        current_frame = getattr(self.parent_ui, '_current_frame', None)
        
        if current_frame is None:
            self.status_label.configure(text="⚠️ No camera frame available. Make sure camera is working.", text_color="#E74C3C")
            return
        
        if not self.user_manager:
            self.status_label.configure(text="⚠️ User manager not available", text_color="#E74C3C")
            return
        
        self.status_label.configure(text="📷 Capturing face...", text_color="gray")
        self.update()
        
        # Get fresh frame right before registration
        current_frame = getattr(self.parent_ui, '_current_frame', None)
        if current_frame is None:
            self.status_label.configure(text="⚠️ Camera frame lost. Try again.", text_color="#E74C3C")
            return
        
        success, message = self.user_manager.register_user(name, current_frame)
        
        if success:
            self.status_label.configure(text=f"✅ {message}", text_color="#2ECC71")
            self.name_entry.delete(0, "end")
            self._refresh_user_list()
        else:
            self.status_label.configure(text=f"❌ {message}", text_color="#E74C3C")
    
    def _delete_user(self, user_id):
        """Delete a user after confirmation."""
        if not self.user_manager:
            return
        
        user = self.user_manager.get_user(user_id)
        if not user:
            return
        
        # Create confirmation dialog
        confirm = ctk.CTkToplevel(self)
        confirm.title("Confirm Delete")
        confirm.geometry("300x150")
        confirm.transient(self)
        confirm.grab_set()
        
        ctk.CTkLabel(
            confirm,
            text=f"Delete user '{user.name}'?",
            font=("Helvetica", 14, "bold")
        ).pack(pady=20)
        
        ctk.CTkLabel(
            confirm,
            text="This will remove all their study data.",
            text_color="gray"
        ).pack()
        
        btn_frame = ctk.CTkFrame(confirm, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def do_delete():
            self.user_manager.delete_user(user_id)
            self._refresh_user_list()
            confirm.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=confirm.destroy,
            width=80
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=do_delete,
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=80
        ).pack(side="left", padx=10)
