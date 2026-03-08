# AI Emotion-Based Study Monitor

An intelligent study application that uses your webcam to detect facial emotions and automatically tracks your study time using the Pomodoro technique. The app monitors your emotional state and helps you maintain focus with smart breaks.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.15-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### Core Features
- **🎯 Real-time Emotion Detection**: Uses FER (Facial Expression Recognition) with TensorFlow to analyze your facial expressions
- **📷 Live Camera Feed**: Mirrored camera display with face detection overlay
- **⏱️ Automatic Study Tracking**: Timer starts when you appear focused and pauses when you look stressed or bored
- **🍅 Pomodoro Timer**: Built-in 25-minute work sessions with automatic 5/15-minute breaks
- **🔊 Voice Notifications**: AI voice prompts for state changes and break reminders
- **📊 Emotion Statistics**: Real-time visualization of your emotional state breakdown

### New Enhancements
- **🎛️ Control Buttons**: Manual Start, Pause, Reset, and Skip Break controls
- **📈 Session Statistics**: Track pomodoros completed, focus percentage, and daily totals
- **💾 Session History**: Automatic saving of all study sessions with detailed analytics
- **⚙️ Settings Panel**: Customize all timers, thresholds, and preferences
- **🌙 Theme Toggle**: Switch between dark and light modes
- **🔔 Sound Effects**: Optional audio alerts (add your own .wav files)
- **👻 No-Face Detection**: Auto-pause when you step away from the screen

### Advanced Features
- **📊 Analytics Dashboard**: View weekly study trends, emotion charts, and productivity scores
- **🏆 Achievements & Goals**: Set daily/weekly goals and unlock achievements
- **🧘 Break Exercises**: Eye exercises, stretches, breathing techniques during breaks
- **👁️ Eye Strain Detection**: Monitors blink rate and suggests breaks
- **🔔 Desktop Notifications**: Windows toast notifications for important events
- **📝 Report Generation**: Generate text reports of your study statistics
- **👥 Multi-User Mode**: Face recognition to identify users and track study time separately for each person
- **🏆 User Leaderboard**: See who studies the most with the built-in leaderboard

## 📊 Emotion States

| Detected Emotion | Study State | Icon | Timer Action |
|------------------|-------------|------|--------------|
| Neutral, Happy | Focused | 🎯 | Timer runs |
| Angry, Disgust, Fear | Stressed | 😰 | Suggest break |
| Sad | Bored | 😴 | Suggest break |
| Surprise | Distracted | 🤔 | Timer runs |
| No face | Not Studying | 👻 | **Auto-pause after 5 sec** |

> **Note**: When no face is detected for 5 seconds, the timer automatically pauses. This means stepping away from the camera = not studying.

## 🛠️ Requirements

- **Python**: 3.10 or higher
- **Webcam**: Any USB or built-in camera
- **OS**: Windows 10/11 (voice features optimized for Windows)
- **RAM**: 4GB minimum, 8GB recommended

## 📦 Installation

### 1. Clone or Download the Project
```powershell
git clone https://github.com/yourusername/emotion_detector.git
cd emotion_detector
```

### 2. Create Virtual Environment
```powershell
python -m venv venv
```

### 3. Activate Virtual Environment
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
.\venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

### 4. Install Dependencies
```powershell
pip install -r requirements.txt
```

> **⚠️ Important**: TensorFlow 2.15.0 is required. Newer versions may have DLL compatibility issues on Windows.

## 🚀 How to Run

### Quick Start
```powershell
cd "c:\Users\NILESH KUMAR\Desktop\college\machine learning\emotion_detector"
.\venv\Scripts\Activate.ps1
python main.py
```

### Step-by-Step
1. **Activate the virtual environment**
2. **Run**: `python main.py`
3. **Position** your face in front of the camera
4. **Stay focused** - the stopwatch will start automatically
5. **Use controls** to manually start/pause/reset as needed
6. **Take breaks** when prompted
7. **Close** the window to save your session

## 🎛️ Controls

| Button | Action |
|--------|--------|
| ▶ Start | Manually start the study timer |
| ⏸ Pause | Pause the current session |
| 🔄 Reset | Reset the timer to 00:00:00 |
| ⏭ Skip | End break early and continue |
| � Users | Open multi-user management panel |
| 📊 Stats | Open analytics & exercises dashboard |
| 🌙 Theme | Toggle dark/light mode |
| ⚙ Settings | Open configuration panel |
## 👥 Multi-User Mode

The app supports multiple users with face recognition. Each user's study time is tracked separately.

### How to Use
1. Click the **👥 Users** button to open the User Management panel
2. Enter your name and click **📷 Capture & Register** to register your face
3. The app will automatically recognize you when you sit in front of the camera
4. Your study time will be tracked separately from other users
5. View the **🏆 Leaderboard** to see who studies the most!

### Requirements for Multi-User Mode
- Install `face_recognition` library: `pip install face_recognition`
- On Windows, you may need to install `dlib` first:
  - Option 1: Use conda: `conda install -c conda-forge dlib`
  - Option 2: Download pre-built wheel from [here](https://github.com/jloh02/dlib/releases)

### Multi-User Settings
```json
{
    "multi_user_enabled": true,
    "face_recognition_tolerance": 0.6,
    "recognition_interval": 1.0,
    "show_user_leaderboard": true
}
```

| Setting | Description |
|---------|-------------|
| `multi_user_enabled` | Enable/disable multi-user face recognition |
| `face_recognition_tolerance` | Lower = stricter matching (0.4-0.7 recommended) |
| `recognition_interval` | Seconds between recognition attempts (saves CPU) |
| `show_user_leaderboard` | Show the leaderboard in user panel |
## ⚙️ Configuration

Click the **Settings** button or edit `config.json`:

```json
{
    "pomodoro_duration_minutes": 25,
    "short_break_minutes": 5,
    "long_break_minutes": 15,
    "pomodoros_before_long_break": 4,
    "focus_trigger_seconds": 5.0,
    "stress_trigger_seconds": 20.0,
    "no_face_pause_seconds": 5.0,
    "model_backend": "fer",
    "use_mtcnn": true,
    "smoothing_window": 5,
    "confidence_threshold": 0.3,
    "always_on_top": true,
    "theme": "dark",
    "show_emotion_bars": true,
    "mirror_camera": true,
    "voice_enabled": true,
    "sound_enabled": true,
    "volume": 0.7,
    "multi_user_enabled": true,
    "face_recognition_tolerance": 0.6
}
```

## 🧠 Emotion Detection Models

The app supports two emotion detection backends:

### FER (Default)
Fast and lightweight, good for most use cases.
```json
"model_backend": "fer",
"use_mtcnn": true
```
- **Haarcascade** (`use_mtcnn: false`): Fastest, but less accurate
- **MTCNN** (`use_mtcnn: true`): Slower but much better face detection

### DeepFace (Better Accuracy)
More accurate but slower, uses state-of-the-art models.
```json
"model_backend": "deepface"
```

### Model Improvement Features

| Feature | Description |
|---------|-------------|
| **MTCNN Face Detection** | Better face detection than Haarcascade |
| **Temporal Smoothing** | Averages emotions over multiple frames to reduce jitter |
| **Confidence Thresholds** | Ignores low-confidence predictions |
| **Weighted Scoring** | Different emotions have different weights for study states |
| **Face Quality Check** | Rejects blurry or too-small faces |
| **CLAHE Enhancement** | Improves detection in poor lighting conditions |

### Tuning Tips

- **Jittery results?** → Increase `smoothing_window` (5-10)
- **Too sensitive?** → Increase `confidence_threshold` (0.3-0.5)
- **Missing faces?** → Set `use_mtcnn: true`
- **Too slow?** → Use `"model_backend": "fer"` with `"use_mtcnn": false`
- **Inaccurate emotions?** → Try `"model_backend": "deepface"`

## 📁 Project Structure

```
emotion_detector/
├── main.py              # Application entry point
├── app_ui.py            # CustomTkinter UI with controls
├── camera.py            # Webcam capture module
├── classifier.py        # FER emotion classification
├── logic.py             # Study state machine & Pomodoro logic
├── actions.py           # Voice & sound notifications
├── config.py            # Configuration management
├── user_manager.py      # Multi-user face recognition & tracking
├── requirements.txt     # Python dependencies
├── README.md            # Documentation
│
├── analytics.py         # Productivity analysis & chart generation
├── dashboard.py         # Dashboard UI with tabs
├── exercises.py         # Break exercise suggestions
├── notifications.py     # Desktop toast notifications
├── eye_strain.py        # Eye strain/blink detection
├── test_accuracy.py     # Model accuracy testing utility
│
├── config.json          # User settings (auto-generated)
├── session_history.json # Historical session data
├── study_report.json    # Last session report
├── study_goals.json     # Goal tracking data
├── achievements.json    # Unlocked achievements
├── users.json           # Registered user profiles (multi-user)
├── face_encodings.pkl   # User face data (multi-user)
│
├── charts/              # Generated visualization charts
│   ├── weekly_hours.png
│   ├── focus_trend.png
│   └── emotion_trends.png
│
└── sounds/              # Custom sound files (optional)
    ├── start.wav
    ├── complete.wav
    ├── break.wav
    └── alert.wav
```

## 📈 Output Files

### study_report.json
Generated after each session:
```json
{
    "total_study_seconds": 1500.25,
    "total_break_seconds": 300.0,
    "pomodoros_completed": 1,
    "focus_percentage": 78.5,
    "emotion_breakdown": {
        "Focused": 78.5,
        "Distracted": 15.2,
        "Bored": 6.3
    },
    "session_end": "Sat Feb 22 14:30:00 2026"
}
```

### session_history.json
Long-term session tracking for analytics.

## 🔧 Troubleshooting

### TensorFlow DLL Error
```powershell
pip uninstall tensorflow tensorflow-estimator tensorflow-io-gcs-filesystem -y
pip install tensorflow==2.15.0
```

### Camera Not Working
- Ensure webcam is connected and not used by another app
- Try changing `camera_index` in settings (0, 1, or 2)
- Check camera permissions in Windows Privacy settings

### FER Import Error
The import should be `from fer.fer import FER` (already fixed in code)

### Voice Not Working
- Check `voice_enabled` in settings
- Ensure speakers are connected and volume is up
- Windows Speech services must be available

## 🎨 Customization

### Adding Custom Sounds
1. Create a `sounds/` folder in the project directory
2. Add `.wav` files named:
   - `start.wav` - When study begins
   - `complete.wav` - Pomodoro completed
   - `break.wav` - Break suggestion
   - `alert.wav` - Break over

### Adjusting Sensitivity
- Lower `focus_trigger_seconds` (default: 5) to start faster
- Increase `stress_trigger_seconds` (default: 20) for fewer break prompts
- Adjust `no_face_pause_seconds` (default: 5) for away-from-desk detection

## 📜 License

MIT License - Feel free to modify and distribute!

## 🙏 Credits

- [FER](https://github.com/justinshenk/fer) - Facial Expression Recognition library
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - Modern UI framework
- [TensorFlow](https://www.tensorflow.org/) - Machine Learning framework
- [OpenCV](https://opencv.org/) - Computer Vision library
#
