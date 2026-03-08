🎯 AI Emotion-Based Study Monitor

An intelligent AI-powered study assistant that uses your webcam to detect facial emotions and automatically tracks your study sessions using the Pomodoro technique.

The application analyzes your emotional state in real-time and helps maintain productivity by starting, pausing, or suggesting breaks automatically.






📑 Table of Contents

Features

Emotion States

Requirements

Installation

Usage

Controls

Multi-User Mode

Configuration

Emotion Detection Models

Project Structure

Output Files

Troubleshooting

Customization

License

Credits

✨ Features
🎯 Core Features

Real-time Emotion Detection
Uses FER (Facial Expression Recognition) with TensorFlow.

Live Camera Feed
Displays mirrored webcam feed with face detection overlay.

Automatic Study Tracking
Timer starts when you appear focused and pauses when stressed or bored.

Pomodoro Timer
Built-in 25-minute work sessions with automatic breaks.

Voice Notifications
AI voice prompts for state changes and reminders.

Emotion Statistics
Real-time visualization of emotional state distribution.

🚀 Enhanced Features

🎛 Manual Controls (Start / Pause / Reset / Skip Break)

📈 Session Statistics (focus %, pomodoros completed)

💾 Session History with analytics

⚙ Settings Panel for timer and detection parameters

🌙 Dark / Light Theme Toggle

🔔 Sound Alerts

👻 No-Face Auto Pause when user leaves the screen

🔬 Advanced Features

📊 Analytics Dashboard

🏆 Study Goals & Achievements

🧘 Break Exercises (eye relaxation, breathing)

👁 Eye Strain Detection

🔔 Desktop Notifications

📝 Study Report Generation

👥 Multi-User Mode with Face Recognition

🏆 Leaderboard

📊 Emotion States
Detected Emotion	Study State	Icon	Timer Action
Neutral, Happy	Focused	🎯	Timer runs
Angry, Disgust, Fear	Stressed	😰	Suggest break
Sad	Bored	😴	Suggest break
Surprise	Distracted	🤔	Timer runs
No Face	Not Studying	👻	Auto pause after 5 seconds

When no face is detected for 5 seconds, the timer automatically pauses.

🛠 Requirements

Python: 3.10+

Webcam: USB or built-in

OS: Windows 10 / 11

RAM: 4GB minimum (8GB recommended)

📦 Installation
1️⃣ Clone Repository
git clone https://github.com/yourusername/emotion_detector.git
cd emotion_detector
2️⃣ Create Virtual Environment
python -m venv venv
3️⃣ Activate Environment
Windows PowerShell
.\venv\Scripts\Activate.ps1
Windows CMD
.\venv\Scripts\activate.bat
Linux / Mac
source venv/bin/activate
4️⃣ Install Dependencies
pip install -r requirements.txt

⚠ Important: TensorFlow 2.15.0 is recommended for Windows compatibility.

🚀 Usage

Run the application:

python main.py
Steps

Activate virtual environment

Run python main.py

Position your face in front of the webcam

Stay focused — timer starts automatically

Take breaks when suggested

Close the app to save your session

🎛 Controls
Button	Action
▶ Start	Start study timer
⏸ Pause	Pause session
🔄 Reset	Reset timer
⏭ Skip	Skip break
👥 Users	Manage users
📊 Stats	Open analytics dashboard
🌙 Theme	Toggle theme
⚙ Settings	Open configuration
👥 Multi-User Mode

The system supports multiple users with face recognition.

Each user’s study time is tracked independently.

How to Use

Click Users

Enter name

Click Capture & Register

The system will automatically recognize users

Study time will be recorded per user

Required Libraries
pip install face_recognition

Windows users may need:

conda install -c conda-forge dlib
⚙ Configuration

Edit config.json

{
  "pomodoro_duration_minutes": 25,
  "short_break_minutes": 5,
  "long_break_minutes": 15,
  "pomodoros_before_long_break": 4,
  "focus_trigger_seconds": 5.0,
  "stress_trigger_seconds": 20.0,
  "no_face_pause_seconds": 5.0,
  "model_backend": "fer",
  "use_mtcnn": true
}
🧠 Emotion Detection Models
FER (Default)

Fast and lightweight.

"model_backend": "fer"

Face detection options:

Haarcascade → fastest

MTCNN → more accurate

DeepFace

More accurate but slower.

"model_backend": "deepface"
📁 Project Structure
emotion_detector/
│
├── main.py
├── app_ui.py
├── camera.py
├── classifier.py
├── logic.py
├── actions.py
├── config.py
├── user_manager.py
│
├── analytics.py
├── dashboard.py
├── exercises.py
├── notifications.py
├── eye_strain.py
│
├── config.json
├── session_history.json
├── study_report.json
├── users.json
│
├── charts/
│
└── sounds/
📈 Output Files
study_report.json
{
 "total_study_seconds": 1500,
 "pomodoros_completed": 1,
 "focus_percentage": 78.5
}
session_history.json

Stores long-term study analytics.

🔧 Troubleshooting
TensorFlow Error
pip uninstall tensorflow tensorflow-estimator -y
pip install tensorflow==2.15.0
Camera Not Working

Ensure webcam is connected

Close other apps using camera

Change camera index in settings

Voice Not Working

Check:

voice_enabled in config

Speaker connection

Windows speech services

🎨 Customization
Add Custom Sounds

Create:

sounds/

Add:

start.wav
complete.wav
break.wav
alert.wav
Adjust Sensitivity

Lower focus_trigger_seconds → faster start

Increase stress_trigger_seconds → fewer break prompts

Adjust no_face_pause_seconds → away detection

📜 License

MIT License

Free to modify and distribute.

🙏 Credits

FER – Facial Expression Recognition

TensorFlow – Machine Learning Framework

OpenCV – Computer Vision Library

CustomTkinter – Modern Python UI
