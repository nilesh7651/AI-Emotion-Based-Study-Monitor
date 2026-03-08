import threading
import pyttsx3
import platform
import subprocess
import os
from config import config

# Try to import pygame for sound effects
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except:
    PYGAME_AVAILABLE = False


class AIActionTrigger:
    def __init__(self):
        self.system = platform.system()
        self.sounds_dir = os.path.join(os.path.dirname(__file__), "sounds")
        
        # Create sounds directory if it doesn't exist
        if not os.path.exists(self.sounds_dir):
            os.makedirs(self.sounds_dir)
        
        # Action messages
        self.messages = {
            "START_STUDY": "Focus detected. Starting the stopwatch.",
            "TAKE_BREAK": "You look fatigued. Pausing the stopwatch, take a breather.",
            "POMODORO": "25 minutes completed! Time for a 5-minute break.",
            "POMODORO_LONG": "Great job! 4 pomodoros done. Take a 15-minute break.",
            "BREAK_OVER": "Break is over. Ready to focus again?",
            "BREAK_START": "Break time! Relax and recharge.",
            "NO_FACE": "I can't see you. Pausing the timer.",
            "PAUSE": "Timer paused.",
            "RESET": "Timer reset.",
            "BREAK_SKIP": "Break skipped. Let's continue!"
        }
        
        # Sound file mapping (users can add their own .wav files)
        self.sound_files = {
            "START_STUDY": "start.wav",
            "POMODORO": "complete.wav",
            "POMODORO_LONG": "complete.wav",
            "BREAK_OVER": "alert.wav",
            "TAKE_BREAK": "break.wav"
        }

    def _play_sound(self, sound_name):
        """Play a sound effect if available."""
        if not config.sound_enabled or not PYGAME_AVAILABLE:
            return
            
        sound_file = self.sound_files.get(sound_name)
        if sound_file:
            sound_path = os.path.join(self.sounds_dir, sound_file)
            if os.path.exists(sound_path):
                try:
                    pygame.mixer.music.load(sound_path)
                    pygame.mixer.music.set_volume(config.volume)
                    pygame.mixer.music.play()
                except:
                    pass
            else:
                # Generate a simple beep using pygame
                self._play_beep()
    
    def _play_beep(self):
        """Play a simple beep sound."""
        if not PYGAME_AVAILABLE:
            return
        try:
            # Generate a simple tone
            import numpy as np
            sample_rate = 22050
            duration = 0.3
            frequency = 440
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = np.sin(frequency * t * 2 * np.pi)
            tone = (tone * 32767 * config.volume).astype(np.int16)
            
            # Create stereo sound
            stereo_tone = np.column_stack((tone, tone))
            sound = pygame.sndarray.make_sound(stereo_tone)
            sound.play()
        except:
            pass

    def _speak_windows_fallback(self, text):
        """Bulletproof fallback for Windows to avoid COM thread issues."""
        ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"
        subprocess.run(["powershell", "-Command", ps_cmd], creationflags=subprocess.CREATE_NO_WINDOW)

    def _speak_pyttsx3(self, text):
        """Use pyttsx3 for text-to-speech."""
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.setProperty('volume', config.volume)
            engine.say(text)
            engine.runAndWait()
        except:
            if self.system == "Windows":
                self._speak_windows_fallback(text)
            else:
                print(f"[VOICE FAILED]: {text}")

    def _execute_voice(self, text):
        """Execute voice notification."""
        if not config.voice_enabled:
            return
            
        if self.system == "Windows":
            self._speak_windows_fallback(text)
        else:
            self._speak_pyttsx3(text)

    def trigger(self, action_type):
        """
        Trigger an action with sound and/or voice notification.
        """
        text = self.messages.get(action_type)
        if not text:
            return
            
        print(f"Triggering Action: {action_type} - '{text}'")
        
        # Play sound effect in background
        if config.sound_enabled:
            t_sound = threading.Thread(target=self._play_sound, args=(action_type,))
            t_sound.daemon = True
            t_sound.start()
        
        # Play voice notification in background
        if config.voice_enabled:
            t_voice = threading.Thread(target=self._execute_voice, args=(text,))
            t_voice.daemon = True
            t_voice.start()
    
    def set_message(self, action_type, message):
        """Allow customizing action messages."""
        self.messages[action_type] = message
