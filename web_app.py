"""
Web-based AI Study Monitor using Streamlit
Enhanced UI with WebRTC Camera Support

Run with: streamlit run web_app.py
"""

import streamlit as st
import cv2
import numpy as np
import time
from datetime import datetime
from collections import defaultdict
import av
import json

# Auto-refresh for timer
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# WebRTC for camera
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode

# Try importing emotion detection
try:
    from classifier import create_classifier
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False

try:
    from exercises import BreakExerciseManager, CATEGORY_ICONS
    EXERCISES_AVAILABLE = True
except ImportError:
    EXERCISES_AVAILABLE = False

try:
    from analytics import ProductivityAnalyzer, GoalTracker
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False


# =============================================================================
# Page Configuration
# =============================================================================

st.set_page_config(
    page_title="AI Study Monitor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# Custom CSS for Better UI
# =============================================================================

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #ffffff;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        text-align: center;
        margin-bottom: 1rem !important;
    }
    
    /* Cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #ffffff;
        text-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: rgba(255,255,255,0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }
    
    /* Timer display */
    .timer-display {
        font-size: 5rem;
        font-weight: 800;
        text-align: center;
        color: #ffffff;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 30px rgba(102, 126, 234, 0.8);
        margin: 20px 0;
        letter-spacing: 5px;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 10px 30px;
        border-radius: 50px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.9rem;
        text-align: center;
        margin: 10px auto;
    }
    
    .status-studying {
        background: linear-gradient(90deg, #11998e, #38ef7d);
        color: white;
        box-shadow: 0 5px 20px rgba(17, 153, 142, 0.4);
    }
    
    .status-paused {
        background: linear-gradient(90deg, #eb3349, #f45c43);
        color: white;
        box-shadow: 0 5px 20px rgba(235, 51, 73, 0.4);
    }
    
    .status-break {
        background: linear-gradient(90deg, #8e2de2, #4a00e0);
        color: white;
        box-shadow: 0 5px 20px rgba(142, 45, 226, 0.4);
    }
    
    /* Buttons */
    .stButton > button {
        border-radius: 25px !important;
        padding: 10px 25px !important;
        font-weight: 600 !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(0,0,0,0.3) !important;
    }
    
    /* Progress bars */
    .stProgress > div > div {
        border-radius: 10px;
        height: 15px !important;
    }
    
    /* Emotion cards */
    .emotion-card {
        background: rgba(255,255,255,0.05);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, rgba(52, 152, 219, 0.2) 0%, rgba(41, 128, 185, 0.2) 100%);
        border: 1px solid rgba(52, 152, 219, 0.3);
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
    }
    
    /* Exercise cards */
    .exercise-card {
        background: linear-gradient(135deg, rgba(39, 174, 96, 0.2) 0%, rgba(46, 204, 113, 0.2) 100%);
        border: 1px solid rgba(39, 174, 96, 0.3);
        border-radius: 20px;
        padding: 25px;
        margin: 15px 0;
    }
    
    /* Video container */
    .video-container {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        border: 3px solid rgba(102, 126, 234, 0.5);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        color: #ffffff !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255,255,255,0.7) !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 10px 20px;
        color: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Session State Initialization
# =============================================================================

def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'studying': False,
        'start_time': None,
        'total_seconds': 0,
        'emotion_counts': defaultdict(int),
        'pomodoros': 0,
        'on_break': False,
        'current_emotion': 'Unknown',
        'classifier': None,
        'session_history': [],
        'today_total_seconds': 0,
        'streak': 1,
        'last_emotion_update': 0,
        'focus_time': 0,
        'distracted_time': 0,
        'no_face_start': None  # Track when face was lost
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# Video Processor for WebRTC
# =============================================================================

class EmotionVideoProcessor(VideoProcessorBase):
    """Process video frames for emotion detection."""
    
    def __init__(self):
        self.emotion = "Unknown"
        self.emotions_dict = {}
        self.classifier = None
        self.frame_count = 0
        self.last_box = None
        
        if CLASSIFIER_AVAILABLE:
            try:
                self.classifier = create_classifier(backend='fer', use_mtcnn=False)
            except:
                pass
    
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame_count += 1
        
        # Process every 3rd frame for performance
        if self.classifier and self.frame_count % 3 == 0:
            try:
                box, emotions, state = self.classifier.analyze_frame(img)
                self.emotion = state
                self.emotions_dict = emotions if emotions else {}
                self.last_box = box
                
            except Exception as e:
                pass
        
        # Draw bounding box
        if self.last_box:
            x, y, w, h = self.last_box
            
            # Color based on emotion
            colors = {
                'Focused': (46, 204, 113),
                'Stressed': (231, 76, 60),
                'Bored': (241, 196, 15),
                'Distracted': (155, 89, 182),
            }
            color = colors.get(self.emotion, (102, 126, 234))
            color_bgr = (color[2], color[1], color[0])
            
            cv2.rectangle(img, (x, y), (x+w, y+h), color_bgr, 3)
            
            # Emotion label with background
            label = f"{self.emotion}"
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            cv2.rectangle(img, (x, y-35), (x+label_w+10, y-5), color_bgr, -1)
            cv2.putText(img, label, (x+5, y-12), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            # Draw emotion bars on video
            bar_y = y + h + 10
            bar_height = 8
            for i, (emo, val) in enumerate(self.emotions_dict.items()):
                if val > 0.05:  # Only show significant emotions
                    bar_width = int(val * 100)
                    cv2.rectangle(img, (x, bar_y + i*15), (x + bar_width, bar_y + i*15 + bar_height), color_bgr, -1)
                    cv2.putText(img, f"{emo[:3]}", (x + bar_width + 5, bar_y + i*15 + 8), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")


# =============================================================================
# Helper Functions
# =============================================================================

def calculate_focus_percentage():
    """Calculate focus percentage from emotion counts."""
    counts = st.session_state.emotion_counts
    total = sum(counts.values())
    if total == 0:
        return 0
    focused = counts.get('Focused', 0)
    return (focused / total) * 100


def format_time(seconds):
    """Format seconds to HH:MM:SS."""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_elapsed_time():
    """Get total elapsed study time."""
    elapsed = st.session_state.total_seconds
    if st.session_state.studying and st.session_state.start_time:
        elapsed += time.time() - st.session_state.start_time
    return elapsed


# =============================================================================
# Main Application
# =============================================================================

def main():
    init_session_state()
    
    # Auto-refresh for timer - MUST be at the top of main(), always called
    if AUTOREFRESH_AVAILABLE and st.session_state.studying:
        count = st_autorefresh(interval=1000, limit=None, key="timer_auto_refresh")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## 🎓 AI Study Monitor")
        st.markdown("---")
        
        # Navigation
        page = st.radio(
            "Navigation",
            ["📷 Study Session", "📊 Dashboard", "🧘 Exercises", "⚙️ Settings"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Quick stats with custom styling
        st.markdown("### 📈 Today's Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🍅 Pomodoros", st.session_state.pomodoros)
        with col2:
            focus_pct = calculate_focus_percentage()
            st.metric("🎯 Focus", f"{focus_pct:.0f}%")
        
        # Current emotion indicator
        st.markdown("---")
        emoji_map = {
            'Focused': '🎯', 'Stressed': '😰', 'Bored': '😴',
            'Distracted': '🤔', 'Unknown': '😐', 'No Face Detected': '👻'
        }
        current = st.session_state.current_emotion
        emoji = emoji_map.get(current, '😐')
        st.markdown(f"### {emoji} Current: {current}")
    
    # Main content
    if page == "📷 Study Session":
        study_session_page()
    elif page == "📊 Dashboard":
        dashboard_page()
    elif page == "🧘 Exercises":
        exercises_page()
    elif page == "⚙️ Settings":
        settings_page()


def study_session_page():
    """Main study session page with camera."""
    st.markdown("# 📷 Study Session")
    
    # Show manual refresh if autorefresh not available
    if st.session_state.studying and not AUTOREFRESH_AVAILABLE:
        st.info("🔄 Timer updates when you interact with the page. Click anywhere to refresh.")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.markdown("### 🎥 Live Camera Feed")
        
        # WebRTC Camera with emotion detection
        ctx = webrtc_streamer(
            key="emotion-detection",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=EmotionVideoProcessor,
            media_stream_constraints={"video": True, "audio": False},
            async_processing=True,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        )
        
        # Update emotion state from processor
        if ctx.video_processor:
            current_emotion = ctx.video_processor.emotion
            st.session_state.current_emotion = current_emotion
            
            # Auto-pause if no face detected while studying
            if current_emotion in ['No Face Detected', 'Unknown'] and st.session_state.studying:
                # Track no-face time
                if 'no_face_start' not in st.session_state:
                    st.session_state.no_face_start = time.time()
                elif time.time() - st.session_state.no_face_start > 5:  # 5 seconds without face
                    # Auto-pause the timer
                    if st.session_state.start_time:
                        st.session_state.total_seconds += time.time() - st.session_state.start_time
                        st.session_state.start_time = None
                    st.session_state.studying = False
                    st.warning("⏸️ Timer paused - No face detected!")
            else:
                # Reset no-face timer when face is detected
                st.session_state.no_face_start = None
            
            # Track emotion counts while studying (only if face detected)
            if st.session_state.studying and current_emotion not in ['Unknown', 'No Face Detected']:
                st.session_state.emotion_counts[current_emotion] += 1
            
            # Display current emotion with color
            emoji_map = {
                'Focused': ('🎯', '#27ae60'),
                'Stressed': ('😰', '#e74c3c'),
                'Bored': ('😴', '#f39c12'),
                'Distracted': ('🤔', '#9b59b6'),
                'Unknown': ('😐', '#95a5a6'),
                'No Face Detected': ('👻', '#7f8c8d')
            }
            emoji, color = emoji_map.get(current_emotion, ('😐', '#95a5a6'))
            
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {color}40, {color}20); 
                        padding: 15px; border-radius: 15px; text-align: center;
                        border: 2px solid {color};">
                <span style="font-size: 2rem;">{emoji}</span>
                <span style="font-size: 1.5rem; font-weight: bold; color: white; margin-left: 10px;">{current_emotion}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("👆 Click 'Start' above to begin camera detection")
    
    with col2:
        # Timer Section
        st.markdown("### ⏱️ Study Timer")
        
        elapsed = get_elapsed_time()
        time_str = format_time(elapsed)
        
        st.markdown(f'<div class="timer-display">{time_str}</div>', unsafe_allow_html=True)
        
        # Status indicator
        if st.session_state.on_break:
            st.markdown('<p style="text-align:center;"><span class="status-badge status-break">☕ On Break</span></p>', unsafe_allow_html=True)
        elif st.session_state.studying:
            st.markdown('<p style="text-align:center;"><span class="status-badge status-studying">📚 Studying</span></p>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="text-align:center;"><span class="status-badge status-paused">⏸️ Ready</span></p>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Control buttons - using unique keys to prevent conflicts
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            start_disabled = st.session_state.studying
            if st.button("▶️ Start", use_container_width=True, type="primary", 
                        disabled=start_disabled, key="btn_start"):
                st.session_state.studying = True
                st.session_state.start_time = time.time()
                st.session_state.on_break = False
                st.rerun()
        
        with col_b:
            pause_disabled = not st.session_state.studying
            if st.button("⏸️ Pause", use_container_width=True, 
                        disabled=pause_disabled, key="btn_pause"):
                if st.session_state.studying and st.session_state.start_time:
                    st.session_state.total_seconds += time.time() - st.session_state.start_time
                    st.session_state.start_time = None
                st.session_state.studying = False
                st.rerun()
        
        with col_c:
            if st.button("🔄 Reset", use_container_width=True, key="btn_reset"):
                st.session_state.studying = False
                st.session_state.start_time = None
                st.session_state.total_seconds = 0
                st.session_state.emotion_counts = defaultdict(int)
                st.session_state.on_break = False
                st.rerun()
        
        # Pomodoro controls
        st.markdown("---")
        col_pom1, col_pom2 = st.columns(2)
        with col_pom1:
            if st.button("☕ Start Break", use_container_width=True):
                st.session_state.on_break = True
                st.session_state.studying = False
                if st.session_state.start_time:
                    st.session_state.total_seconds += time.time() - st.session_state.start_time
                st.session_state.pomodoros += 1
                st.rerun()
        with col_pom2:
            if st.button("📚 End Break", use_container_width=True):
                st.session_state.on_break = False
                st.rerun()
        
        st.markdown("---")
        
        # Emotion breakdown
        st.markdown("### 🎭 Emotion Breakdown")
        
        emotions_config = [
            ('Focused', '#27ae60', '🎯'),
            ('Stressed', '#e74c3c', '😰'),
            ('Bored', '#f39c12', '😴'),
            ('Distracted', '#9b59b6', '🤔')
        ]
        
        counts = st.session_state.emotion_counts
        total = max(sum(counts.values()), 1)
        
        for emotion, color, emoji in emotions_config:
            pct = (counts.get(emotion, 0) / total) * 100
            st.markdown(f"**{emoji} {emotion}** - {pct:.0f}%")
            st.progress(pct / 100)


def dashboard_page():
    """Analytics dashboard page."""
    st.markdown("# 📊 Analytics Dashboard")
    
    # Summary cards row
    col1, col2, col3, col4 = st.columns(4)
    
    cards_data = [
        ("📚", "2.5h", "Today"),
        ("🍅", str(st.session_state.pomodoros), "Pomodoros"),
        ("🎯", f"{calculate_focus_percentage():.0f}%", "Focus"),
        ("🔥", "3", "Day Streak")
    ]
    
    for col, (icon, value, label) in zip([col1, col2, col3, col4], cards_data):
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 2rem;">{icon}</div>
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Weekly Study Hours")
        import random
        chart_data = {
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Hours': [random.uniform(1, 4) for _ in range(7)]
        }
        st.bar_chart(chart_data, x='Day', y='Hours', color='#667eea')
    
    with col2:
        st.markdown("### 🎭 Emotion Distribution")
        emotion_data = {
            'Emotion': ['Focused', 'Distracted', 'Bored', 'Stressed'],
            'Percentage': [65, 15, 12, 8]
        }
        st.bar_chart(emotion_data, x='Emotion', y='Percentage', color='#764ba2')
    
    st.markdown("---")
    
    # Productivity Score
    st.markdown("### 🏆 Productivity Score")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        score = 72
        st.markdown(f"""
        <div class="stat-card" style="padding: 40px;">
            <div class="stat-value" style="font-size: 4rem;">{score}</div>
            <div class="stat-label" style="font-size: 1.2rem;">out of 100</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="info-box">
            <h4>📊 Score Breakdown</h4>
            <p>✅ <b>Focus Time:</b> Great - 78% of session focused</p>
            <p>✅ <b>Study Duration:</b> Good - 2.5 hours today</p>
            <p>⚠️ <b>Break Compliance:</b> Fair - Took 2 of 4 suggested breaks</p>
            <p>✅ <b>Consistency:</b> Excellent - 3 day streak!</p>
        </div>
        """, unsafe_allow_html=True)


def exercises_page():
    """Break exercises page."""
    st.markdown("# 🧘 Break Exercises")
    
    if not EXERCISES_AVAILABLE:
        st.warning("⚠️ Exercises module not available")
        return
    
    manager = BreakExerciseManager()
    
    # Category selection with nice buttons
    st.markdown("### Choose a Category")
    
    col1, col2, col3, col4 = st.columns(4)
    
    categories = [
        ("👁️ Eye", "eye", col1),
        ("🤸 Stretch", "stretch", col2),
        ("🌬️ Breathing", "breathing", col3),
        ("⚡ Energy", "energy", col4)
    ]
    
    for label, cat, col in categories:
        with col:
            if st.button(label, use_container_width=True, key=f"btn_{cat}"):
                st.session_state.exercise_category = cat
    
    st.markdown("---")
    
    # Show exercise
    category = st.session_state.get('exercise_category', None)
    
    if category:
        exercise = manager.get_suggestion(category=category)
        
        st.markdown(f"""
        <div class="exercise-card">
            <h2>{CATEGORY_ICONS.get(category, '🏃')} {exercise.name}</h2>
            <p style="font-size: 1.2rem; color: rgba(255,255,255,0.8);">{exercise.description}</p>
            <p><b>⏱️ Duration:</b> {exercise.duration_seconds} seconds</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📋 Steps")
            for i, step in enumerate(exercise.steps, 1):
                st.markdown(f"**{i}.** {step}")
        
        with col2:
            st.markdown("### ✨ Benefits")
            for benefit in exercise.benefits:
                st.markdown(f"✅ {benefit}")
        
        if st.button("✅ Mark Complete", type="primary", use_container_width=True):
            st.balloons()
            st.success("🎉 Great job! Exercise completed!")
    else:
        st.markdown("""
        <div class="info-box">
            <h3>👆 Select a category above</h3>
            <p>Get personalized exercise suggestions for your break time!</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🧘 Get 5-Minute Break Routine", use_container_width=True):
        routine = manager.get_quick_routine(5)
        
        st.markdown("### Your 5-Minute Routine")
        
        for i, ex in enumerate(routine, 1):
            with st.expander(f"**{i}. {ex.name}** ({ex.duration_seconds}s)"):
                st.write(ex.description)
                for step in ex.steps:
                    st.write(f"• {step}")


def settings_page():
    """Settings page."""
    st.markdown("# ⚙️ Settings")
    
    tab1, tab2, tab3 = st.tabs(["🍅 Pomodoro", "🎯 Detection", "🔔 Notifications"])
    
    with tab1:
        st.markdown("### Pomodoro Timer Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            work_duration = st.slider("Work Duration (minutes)", 15, 60, 25)
            short_break = st.slider("Short Break (minutes)", 3, 15, 5)
        
        with col2:
            long_break = st.slider("Long Break (minutes)", 10, 30, 15)
            pomodoros_before_long = st.slider("Pomodoros before long break", 2, 6, 4)
    
    with tab2:
        st.markdown("### Detection Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            backend = st.selectbox("Model Backend", ["FER (Fast)", "DeepFace (Accurate)"])
            use_mtcnn = st.checkbox("Use MTCNN (better face detection)", value=False)
        
        with col2:
            confidence = st.slider("Confidence Threshold", 0.1, 0.9, 0.3)
            smoothing = st.slider("Smoothing Window", 1, 10, 5)
    
    with tab3:
        st.markdown("### Notification Settings")
        
        voice_enabled = st.checkbox("🔊 Voice Notifications", value=True)
        sound_enabled = st.checkbox("🔔 Sound Effects", value=True)
        desktop_notifications = st.checkbox("💻 Desktop Notifications", value=True)
        
        st.markdown("---")
        
        st.markdown("### Reminder Intervals")
        break_reminder = st.slider("Break Reminder (minutes)", 15, 45, 25)
        hydration_reminder = st.slider("Hydration Reminder (minutes)", 30, 90, 45)
    
    st.markdown("---")
    
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        st.success("✅ Settings saved successfully!")


# =============================================================================
# Run Application
# =============================================================================

if __name__ == "__main__":
    main()
