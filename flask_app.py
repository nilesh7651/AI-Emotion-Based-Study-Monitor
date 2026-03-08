"""
Flask Web Application for AI Study Monitor

This provides a web interface using Flask + WebSocket for real-time
emotion detection using the browser's camera.

Run with: python flask_app.py
Then open: http://localhost:5000
"""

from flask import Flask, render_template, Response, jsonify, request
from flask_socketio import SocketIO
import cv2
import base64
import numpy as np
import json
import time
import threading
from datetime import datetime
from collections import defaultdict

# Import emotion detection
try:
    from classifier import create_classifier
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False
    print("Warning: Classifier not available")

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

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'emotion_detector_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
session_state = {
    'studying': False,
    'start_time': None,
    'total_seconds': 0,
    'emotion_counts': defaultdict(int),
    'pomodoros': 0,
    'on_break': False,
    'current_emotion': 'Unknown',
    'no_face_start': None  # Track when face was lost
}

# Initialize classifier
classifier = None
if CLASSIFIER_AVAILABLE:
    try:
        classifier = create_classifier(backend='fer', use_mtcnn=False)
        print("Classifier initialized successfully")
    except Exception as e:
        print(f"Failed to initialize classifier: {e}")


# =============================================================================
# Routes
# =============================================================================

@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get current session status."""
    if session_state['studying'] and session_state['start_time']:
        elapsed = time.time() - session_state['start_time'] + session_state['total_seconds']
    else:
        elapsed = session_state['total_seconds']
    
    return jsonify({
        'studying': session_state['studying'],
        'on_break': session_state['on_break'],
        'elapsed_seconds': elapsed,
        'pomodoros': session_state['pomodoros'],
        'current_emotion': session_state['current_emotion'],
        'emotion_counts': dict(session_state['emotion_counts']),
        'focus_percentage': calculate_focus()
    })


@app.route('/api/start', methods=['POST'])
def start_session():
    """Start studying."""
    session_state['studying'] = True
    session_state['start_time'] = time.time()
    session_state['on_break'] = False
    return jsonify({'status': 'started'})


@app.route('/api/pause', methods=['POST'])
def pause_session():
    """Pause studying."""
    if session_state['studying'] and session_state['start_time']:
        session_state['total_seconds'] += time.time() - session_state['start_time']
    session_state['studying'] = False
    return jsonify({'status': 'paused'})


@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset session."""
    session_state['studying'] = False
    session_state['start_time'] = None
    session_state['total_seconds'] = 0
    session_state['emotion_counts'] = defaultdict(int)
    session_state['current_emotion'] = 'Unknown'
    return jsonify({'status': 'reset'})


@app.route('/api/exercise/<category>')
def get_exercise(category):
    """Get an exercise suggestion."""
    if not EXERCISES_AVAILABLE:
        return jsonify({'error': 'Exercises not available'}), 400
    
    manager = BreakExerciseManager()
    exercise = manager.get_suggestion(category=category)
    
    return jsonify({
        'name': exercise.name,
        'description': exercise.description,
        'duration': exercise.duration_seconds,
        'category': exercise.category,
        'steps': exercise.steps,
        'benefits': exercise.benefits
    })


@app.route('/api/analytics')
def get_analytics():
    """Get analytics data."""
    if not ANALYTICS_AVAILABLE:
        return jsonify({'error': 'Analytics not available'}), 400
    
    analyzer = ProductivityAnalyzer()
    weekly = analyzer.get_weekly_summary()
    
    return jsonify({
        'total_hours': weekly['total_hours'],
        'total_pomodoros': weekly['total_pomodoros'],
        'average_focus': weekly['average_focus'],
        'streak': weekly['streak'],
        'productivity_score': analyzer.calculate_productivity_score()
    })


def calculate_focus():
    """Calculate focus percentage."""
    counts = session_state['emotion_counts']
    total = sum(counts.values())
    if total == 0:
        return 0
    return (counts.get('Focused', 0) / total) * 100


# =============================================================================
# WebSocket Handlers
# =============================================================================

@socketio.on('connect')
def handle_connect():
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


@socketio.on('frame')
def handle_frame(data):
    """Process a video frame from browser."""
    if not classifier:
        return
    
    try:
        # Decode base64 image
        img_data = data.split(',')[1]
        img_bytes = base64.b64decode(img_data)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return
        
        # Analyze emotion
        box, emotions, state = classifier.analyze_frame(frame)
        
        # Update session state
        session_state['current_emotion'] = state
        
        # Handle no face detection - pause if no face for 5 seconds
        current_time = time.time()
        if state in ['No Face Detected', 'Unknown']:
            if session_state['no_face_start'] is None:
                session_state['no_face_start'] = current_time
            elif current_time - session_state['no_face_start'] > 5:  # 5 seconds
                if session_state['studying'] and session_state['start_time']:
                    session_state['total_seconds'] += current_time - session_state['start_time']
                    session_state['start_time'] = None
                session_state['studying'] = False
                socketio.emit('auto_paused', {'reason': 'No face detected'})
        else:
            session_state['no_face_start'] = None
            # Only track emotions when face is detected and studying
            if session_state['studying']:
                session_state['emotion_counts'][state] += 1
        
        # Send result back to client
        result = {
            'emotion': state,
            'box': box,
            'focus_percentage': calculate_focus()
        }
        
        socketio.emit('emotion_result', result)
    
    except Exception as e:
        print(f"Error processing frame: {e}")


# =============================================================================
# HTML Template
# =============================================================================

# Create templates folder and index.html if they don't exist
import os

templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
os.makedirs(templates_dir, exist_ok=True)

index_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Study Monitor</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .camera-container {
            position: relative;
        }
        
        #video, #canvas {
            width: 100%;
            border-radius: 10px;
            display: block;
        }
        
        #canvas {
            display: none;
        }
        
        .emotion-overlay {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 1.2rem;
        }
        
        .timer {
            font-size: 4rem;
            text-align: center;
            font-weight: bold;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
        }
        
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 25px;
            margin-bottom: 20px;
        }
        
        .status.studying { background: #27ae60; }
        .status.paused { background: #e74c3c; }
        .status.break { background: #9b59b6; }
        
        .controls {
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }
        
        .btn-start { background: linear-gradient(135deg, #27ae60, #2ecc71); color: white; }
        .btn-pause { background: linear-gradient(135deg, #f39c12, #e67e22); color: white; }
        .btn-reset { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; }
        .btn-skip { background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9rem;
            opacity: 0.9;
        }
        
        .progress-bar {
            height: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            margin: 5px 0;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #27ae60, #2ecc71);
            transition: width 0.5s ease;
        }
        
        .emotion-item {
            margin: 10px 0;
        }
        
        .emotion-label {
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
        }
        
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎓 AI Study Monitor</h1>
            <p>Track your focus and study effectively</p>
        </header>
        
        <div class="main-grid">
            <div class="card camera-container">
                <h2>📷 Live Camera</h2>
                <video id="video" autoplay playsinline></video>
                <canvas id="canvas"></canvas>
                <div class="emotion-overlay" id="emotion-display">😐 Initializing...</div>
            </div>
            
            <div class="card">
                <h2>⏱️ Timer</h2>
                
                <div class="timer" id="timer">00:00:00</div>
                
                <div class="status" id="status">⏸️ Ready to Start</div>
                
                <div class="controls">
                    <button class="btn btn-start" onclick="startSession()">▶️ Start</button>
                    <button class="btn btn-pause" onclick="pauseSession()">⏸️ Pause</button>
                    <button class="btn btn-reset" onclick="resetSession()">🔄 Reset</button>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="pomodoros">0</div>
                        <div class="stat-label">🍅 Pomodoros</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="focus">0%</div>
                        <div class="stat-label">🎯 Focus</div>
                    </div>
                </div>
                
                <h3 style="margin-top: 20px;">🎭 Emotion Breakdown</h3>
                <div id="emotions">
                    <div class="emotion-item">
                        <div class="emotion-label">
                            <span>🎯 Focused</span>
                            <span id="focused-pct">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="focused-bar" style="width: 0%; background: #27ae60;"></div>
                        </div>
                    </div>
                    <div class="emotion-item">
                        <div class="emotion-label">
                            <span>😰 Stressed</span>
                            <span id="stressed-pct">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="stressed-bar" style="width: 0%; background: #e74c3c;"></div>
                        </div>
                    </div>
                    <div class="emotion-item">
                        <div class="emotion-label">
                            <span>😴 Bored</span>
                            <span id="bored-pct">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="bored-bar" style="width: 0%; background: #f39c12;"></div>
                        </div>
                    </div>
                    <div class="emotion-item">
                        <div class="emotion-label">
                            <span>🤔 Distracted</span>
                            <span id="distracted-pct">0%</span>
                        </div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="distracted-bar" style="width: 0%; background: #9b59b6;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // WebSocket connection
        const socket = io();
        
        // Video elements
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        
        // Session state
        let studying = false;
        let startTime = null;
        let totalSeconds = 0;
        let timerInterval = null;
        
        // Emotion emojis
        const emojis = {
            'Focused': '🎯',
            'Stressed': '😰',
            'Bored': '😴',
            'Distracted': '🤔',
            'No Face Detected': '👻',
            'Unknown': '😐'
        };
        
        // Initialize camera
        async function initCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480 }
                });
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    // Start sending frames
                    setInterval(sendFrame, 200);  // 5 FPS
                };
            } catch (err) {
                console.error('Camera error:', err);
                document.getElementById('emotion-display').textContent = '📷 Camera not available';
            }
        }
        
        // Send video frame to server
        function sendFrame() {
            if (video.readyState === video.HAVE_ENOUGH_DATA) {
                ctx.drawImage(video, 0, 0);
                const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
                socket.emit('frame', dataUrl);
            }
        }
        
        // Handle emotion result from server
        socket.on('emotion_result', (data) => {
            const emoji = emojis[data.emotion] || '😐';
            document.getElementById('emotion-display').textContent = `${emoji} ${data.emotion}`;
            document.getElementById('focus').textContent = `${data.focus_percentage.toFixed(0)}%`;
        });
        
        // Timer functions
        function updateTimer() {
            let seconds = totalSeconds;
            if (studying && startTime) {
                seconds += (Date.now() - startTime) / 1000;
            }
            
            const h = Math.floor(seconds / 3600);
            const m = Math.floor((seconds % 3600) / 60);
            const s = Math.floor(seconds % 60);
            
            document.getElementById('timer').textContent = 
                `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }
        
        function startSession() {
            fetch('/api/start', { method: 'POST' })
                .then(() => {
                    studying = true;
                    startTime = Date.now();
                    document.getElementById('status').textContent = '📚 Studying';
                    document.getElementById('status').className = 'status studying';
                    if (!timerInterval) {
                        timerInterval = setInterval(updateTimer, 100);
                    }
                });
        }
        
        function pauseSession() {
            fetch('/api/pause', { method: 'POST' })
                .then(() => {
                    if (studying && startTime) {
                        totalSeconds += (Date.now() - startTime) / 1000;
                    }
                    studying = false;
                    document.getElementById('status').textContent = '⏸️ Paused';
                    document.getElementById('status').className = 'status paused';
                });
        }
        
        function resetSession() {
            fetch('/api/reset', { method: 'POST' })
                .then(() => {
                    studying = false;
                    startTime = null;
                    totalSeconds = 0;
                    document.getElementById('status').textContent = '⏸️ Ready';
                    document.getElementById('status').className = 'status';
                    updateTimer();
                    
                    // Reset emotion bars
                    ['focused', 'stressed', 'bored', 'distracted'].forEach(e => {
                        document.getElementById(`${e}-bar`).style.width = '0%';
                        document.getElementById(`${e}-pct`).textContent = '0%';
                    });
                });
        }
        
        // Poll for status updates
        function pollStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('pomodoros').textContent = data.pomodoros;
                    document.getElementById('focus').textContent = `${data.focus_percentage.toFixed(0)}%`;
                    
                    // Update emotion bars
                    const total = Object.values(data.emotion_counts).reduce((a, b) => a + b, 0) || 1;
                    ['Focused', 'Stressed', 'Bored', 'Distracted'].forEach(emotion => {
                        const lc = emotion.toLowerCase();
                        const pct = ((data.emotion_counts[emotion] || 0) / total * 100).toFixed(0);
                        document.getElementById(`${lc}-bar`).style.width = `${pct}%`;
                        document.getElementById(`${lc}-pct`).textContent = `${pct}%`;
                    });
                });
        }
        
        // Initialize
        initCamera();
        setInterval(pollStatus, 1000);
        setInterval(updateTimer, 100);
    </script>
</body>
</html>
'''

with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(index_html)

print("Created templates/index.html")


if __name__ == '__main__':
    print("=" * 50)
    print("AI Study Monitor - Web Version")
    print("=" * 50)
    print("Starting server at http://localhost:5000")
    print("Open this URL in your browser")
    print("=" * 50)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
