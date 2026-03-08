"""
Desktop Notifications Module for AI Study Monitor

Provides:
- Windows toast notifications
- System tray integration
- Notification scheduling
- Custom notification sounds
- Voice notifications (text-to-speech)
"""

import os
import sys
import threading
import time
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Try importing sound libraries
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except (ImportError, Exception):
    PYGAME_AVAILABLE = False


class NotificationType(Enum):
    """Types of notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    BREAK = "break"
    ACHIEVEMENT = "achievement"
    EYE_STRAIN = "eye_strain"


@dataclass
class Notification:
    """Represents a notification."""
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    duration_seconds: int = 5
    sound: bool = True
    voice: bool = False
    priority: str = "normal"  # low, normal, high, urgent


# Sound frequencies for different notification types
SOUND_CONFIGS = {
    NotificationType.INFO: {'frequency': 600, 'duration': 0.2, 'beeps': 1},
    NotificationType.SUCCESS: {'frequency': 800, 'duration': 0.15, 'beeps': 2},
    NotificationType.WARNING: {'frequency': 500, 'duration': 0.3, 'beeps': 2},
    NotificationType.BREAK: {'frequency': 700, 'duration': 0.25, 'beeps': 3},
    NotificationType.ACHIEVEMENT: {'frequency': 1000, 'duration': 0.1, 'beeps': 4},
    NotificationType.EYE_STRAIN: {'frequency': 400, 'duration': 0.4, 'beeps': 2},
}


# Try importing Windows notification library
_notification_backend = None

try:
    from win10toast import ToastNotifier
    _notification_backend = "win10toast"
except ImportError:
    pass

if _notification_backend is None:
    try:
        from plyer import notification as plyer_notification
        _notification_backend = "plyer"
    except ImportError:
        pass


class SoundManager:
    """Manages sound effects and voice notifications."""
    
    def __init__(self):
        self.enabled_sound = PYGAME_AVAILABLE
        self.enabled_voice = PYTTSX3_AVAILABLE
        self._tts_engine = None
        self._tts_lock = threading.Lock()
        
        if self.enabled_voice:
            try:
                self._tts_engine = pyttsx3.init()
                self._tts_engine.setProperty('rate', 150)
                self._tts_engine.setProperty('volume', 0.9)
            except:
                self.enabled_voice = False
    
    def play_beep(self, frequency: int = 600, duration: float = 0.2):
        """Play a beep sound."""
        if not self.enabled_sound:
            return
        
        def _play():
            try:
                sample_rate = 44100
                samples = int(sample_rate * duration)
                t = np.linspace(0, duration, samples, False)
                wave = np.sin(2 * np.pi * frequency * t) * 0.3
                
                # Fade in/out to avoid clicks
                fade_samples = min(int(samples * 0.1), 1000)
                fade_in = np.linspace(0, 1, fade_samples)
                fade_out = np.linspace(1, 0, fade_samples)
                wave[:fade_samples] *= fade_in
                wave[-fade_samples:] *= fade_out
                
                wave = (wave * 32767).astype(np.int16)
                stereo = np.column_stack((wave, wave))
                sound = pygame.sndarray.make_sound(stereo)
                sound.play()
                time.sleep(duration + 0.05)
            except Exception as e:
                pass
        
        thread = threading.Thread(target=_play, daemon=True)
        thread.start()
    
    def play_notification_sound(self, notification_type: NotificationType):
        """Play sound for notification type."""
        if not self.enabled_sound:
            return
        
        config = SOUND_CONFIGS.get(notification_type, SOUND_CONFIGS[NotificationType.INFO])
        
        def _play_sequence():
            for i in range(config['beeps']):
                self.play_beep(config['frequency'], config['duration'])
                if i < config['beeps'] - 1:
                    time.sleep(0.1)
        
        thread = threading.Thread(target=_play_sequence, daemon=True)
        thread.start()
    
    def speak(self, text: str):
        """Speak text using TTS."""
        if not self.enabled_voice or not self._tts_engine:
            return
        
        def _speak():
            with self._tts_lock:
                try:
                    self._tts_engine.say(text)
                    self._tts_engine.runAndWait()
                except:
                    pass
        
        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()
    
    def play_success_melody(self):
        """Play a success melody."""
        if not self.enabled_sound:
            return
        
        def _play():
            notes = [523, 659, 784, 1047]  # C5, E5, G5, C6
            for note in notes:
                self.play_beep(note, 0.1)
                time.sleep(0.12)
        
        thread = threading.Thread(target=_play, daemon=True)
        thread.start()
    
    def play_warning_sound(self):
        """Play warning sound."""
        if not self.enabled_sound:
            return
        
        def _play():
            for _ in range(2):
                self.play_beep(400, 0.3)
                time.sleep(0.4)
        
        thread = threading.Thread(target=_play, daemon=True)
        thread.start()


class DesktopNotifier:
    """Handles desktop notifications with sound and voice support."""
    
    # Icons for different notification types (Windows toast supports .ico)
    ICONS = {
        NotificationType.INFO: None,
        NotificationType.SUCCESS: None,
        NotificationType.WARNING: None,
        NotificationType.BREAK: None,
        NotificationType.ACHIEVEMENT: None,
        NotificationType.EYE_STRAIN: None
    }
    
    def __init__(self, app_name: str = "AI Study Monitor", 
                 enable_sound: bool = True,
                 enable_voice: bool = True):
        self.app_name = app_name
        self.enabled = True
        self.enable_sound = enable_sound
        self.enable_voice = enable_voice
        self._notifier = None
        self._sound_manager = SoundManager()
        self._init_backend()
    
    def _init_backend(self):
        """Initialize the notification backend."""
        global _notification_backend
        
        if _notification_backend == "win10toast":
            try:
                self._notifier = ToastNotifier()
            except:
                _notification_backend = None
    
    def show(self, notification: Notification):
        """Show a desktop notification with optional sound/voice."""
        if not self.enabled:
            return
        
        # Play sound if enabled
        if notification.sound and self.enable_sound:
            self._sound_manager.play_notification_sound(notification.notification_type)
        
        # Speak message if voice enabled
        if notification.voice and self.enable_voice:
            speak_text = f"{notification.title}. {notification.message}"
            self._sound_manager.speak(speak_text)
        
        # Run toast notification in thread to avoid blocking
        thread = threading.Thread(
            target=self._show_notification,
            args=(notification,),
            daemon=True
        )
        thread.start()
    
    def _show_notification(self, notification: Notification):
        """Internal method to show notification."""
        global _notification_backend
        
        try:
            if _notification_backend == "win10toast" and self._notifier:
                self._notifier.show_toast(
                    notification.title,
                    notification.message,
                    duration=notification.duration_seconds,
                    threaded=False
                )
            
            elif _notification_backend == "plyer":
                plyer_notification.notify(
                    title=notification.title,
                    message=notification.message,
                    app_name=self.app_name,
                    timeout=notification.duration_seconds
                )
            
            else:
                # Fallback: Use Windows PowerShell for toast notification
                self._show_powershell_toast(notification)
        
        except Exception as e:
            print(f"Notification error: {e}")
    
    def _show_powershell_toast(self, notification: Notification):
        """Show toast notification using PowerShell (Windows fallback)."""
        if sys.platform != "win32":
            return
        
        try:
            import subprocess
            
            # PowerShell script for toast notification
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

            $template = @"
            <toast>
                <visual>
                    <binding template="ToastText02">
                        <text id="1">{notification.title}</text>
                        <text id="2">{notification.message}</text>
                    </binding>
                </visual>
            </toast>
"@
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{self.app_name}").Show($toast)
            '''
            
            # Simpler fallback using BurntToast module or basic notification
            simple_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            $notification = New-Object System.Windows.Forms.NotifyIcon
            $notification.Icon = [System.Drawing.SystemIcons]::Information
            $notification.BalloonTipTitle = "{notification.title}"
            $notification.BalloonTipText = "{notification.message}"
            $notification.Visible = $true
            $notification.ShowBalloonTip({notification.duration_seconds * 1000})
            Start-Sleep -Seconds {notification.duration_seconds + 1}
            $notification.Dispose()
            '''
            
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden", "-Command", simple_script],
                capture_output=True,
                timeout=10
            )
        
        except Exception as e:
            # Silent fail for notification
            pass
    
    # Convenience methods
    def notify_break_time(self):
        """Notify user it's break time."""
        self.show(Notification(
            title="⏰ Break Time!",
            message="You've been studying hard. Time for a short break!",
            notification_type=NotificationType.BREAK,
            duration_seconds=10,
            voice=True,
            priority="high"
        ))
    
    def notify_break_over(self):
        """Notify user break is over."""
        self.show(Notification(
            title="📚 Break Over",
            message="Ready to get back to studying?",
            notification_type=NotificationType.INFO,
            duration_seconds=5
        ))
    
    def notify_high_focus(self):
        """Celebrate high focus."""
        self.show(Notification(
            title="🎯 Great Focus!",
            message="You're in the zone! Keep it up!",
            notification_type=NotificationType.SUCCESS,
            duration_seconds=3
        ))
    
    def notify_stress_detected(self):
        """Notify about stress detection."""
        self.show(Notification(
            title="😓 Stress Detected",
            message="Consider taking a deep breath or short break.",
            notification_type=NotificationType.WARNING,
            duration_seconds=5
        ))
    
    def notify_eye_strain(self):
        """Warn about eye strain."""
        self.show(Notification(
            title="👁️ Eye Strain Warning",
            message="Your blink rate is low. Look away from screen for 20 seconds.",
            notification_type=NotificationType.EYE_STRAIN,
            duration_seconds=8
        ))
    
    def notify_achievement(self, achievement_name: str):
        """Celebrate achievement unlock."""
        self.show(Notification(
            title="🏆 Achievement Unlocked!",
            message=achievement_name,
            notification_type=NotificationType.ACHIEVEMENT,
            duration_seconds=8
        ))
    
    def notify_pomodoro_complete(self, count: int):
        """Notify pomodoro completion."""
        self.show(Notification(
            title="🍅 Pomodoro Complete!",
            message=f"Great job! You've completed {count} pomodoro(s).",
            notification_type=NotificationType.SUCCESS,
            duration_seconds=5
        ))
    
    def notify_goal_reached(self, goal_name: str):
        """Notify when a goal is reached."""
        self.show(Notification(
            title="🎯 Goal Reached!",
            message=f"You achieved: {goal_name}",
            notification_type=NotificationType.ACHIEVEMENT,
            duration_seconds=8
        ))
    
    def notify_custom(self, title: str, message: str):
        """Show custom notification."""
        self.show(Notification(
            title=title,
            message=message,
            notification_type=NotificationType.INFO
        ))


class NotificationScheduler:
    """Schedules periodic notifications."""
    
    def __init__(self, notifier: DesktopNotifier):
        self.notifier = notifier
        self._timers = []
        self._running = False
    
    def schedule_reminders(self, interval_minutes: int = 30):
        """Schedule periodic reminders."""
        import time
        
        def reminder_loop():
            while self._running:
                time.sleep(interval_minutes * 60)
                if self._running:
                    self.notifier.show(Notification(
                        title="⏰ Study Check-in",
                        message="How's your focus? Remember to take breaks!",
                        notification_type=NotificationType.INFO
                    ))
        
        self._running = True
        timer_thread = threading.Thread(target=reminder_loop, daemon=True)
        timer_thread.start()
        self._timers.append(timer_thread)
    
    def schedule_hydration_reminder(self, interval_minutes: int = 45):
        """Remind to drink water."""
        import time
        
        def hydration_loop():
            while self._running:
                time.sleep(interval_minutes * 60)
                if self._running:
                    self.notifier.show(Notification(
                        title="💧 Stay Hydrated",
                        message="Time for a drink of water!",
                        notification_type=NotificationType.INFO
                    ))
        
        self._running = True
        timer_thread = threading.Thread(target=hydration_loop, daemon=True)
        timer_thread.start()
        self._timers.append(timer_thread)
    
    def stop_all(self):
        """Stop all scheduled reminders."""
        self._running = False


def check_notification_support() -> dict:
    """Check which notification backends are available."""
    results = {
        'win10toast': False,
        'plyer': False,
        'powershell': sys.platform == 'win32'
    }
    
    try:
        from win10toast import ToastNotifier
        results['win10toast'] = True
    except ImportError:
        pass
    
    try:
        from plyer import notification
        results['plyer'] = True
    except ImportError:
        pass
    
    return results


def test_notification():
    """Test notification system."""
    print("Testing notification system...")
    print(f"Backend: {_notification_backend}")
    print(f"Available backends: {check_notification_support()}")
    
    notifier = DesktopNotifier()
    notifier.notify_custom(
        "🧪 Test Notification",
        "AI Study Monitor notifications are working!"
    )
    print("Notification sent! Check your system tray.")


if __name__ == "__main__":
    test_notification()
