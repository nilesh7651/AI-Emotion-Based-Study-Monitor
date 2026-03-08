"""
Break Exercises Module for AI Study Monitor

Provides suggestions for:
- Eye exercises
- Stretching exercises
- Breathing exercises
- Quick energy boosters
"""

import random
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Exercise:
    """Represents a break exercise."""
    name: str
    description: str
    duration_seconds: int
    category: str  # 'eye', 'stretch', 'breathing', 'energy'
    difficulty: str  # 'easy', 'medium', 'hard'
    benefits: List[str]
    steps: List[str]


# Eye Exercises
EYE_EXERCISES = [
    Exercise(
        name="20-20-20 Rule",
        description="Look at something 20 feet away for 20 seconds",
        duration_seconds=20,
        category="eye",
        difficulty="easy",
        benefits=["Reduces eye strain", "Relaxes eye muscles", "Prevents dry eyes"],
        steps=[
            "Look away from your screen",
            "Focus on something 20 feet (6 meters) away",
            "Keep focusing for 20 seconds",
            "Blink naturally"
        ]
    ),
    Exercise(
        name="Eye Rolling",
        description="Circular eye movements to relax muscles",
        duration_seconds=30,
        category="eye",
        difficulty="easy",
        benefits=["Relaxes eye muscles", "Improves flexibility", "Reduces tension"],
        steps=[
            "Close your eyes",
            "Slowly roll your eyes clockwise 5 times",
            "Roll your eyes counter-clockwise 5 times",
            "Keep movements slow and smooth"
        ]
    ),
    Exercise(
        name="Palming",
        description="Warm your eyes with your palms",
        duration_seconds=60,
        category="eye",
        difficulty="easy",
        benefits=["Deep relaxation", "Reduces strain", "Rest for retina"],
        steps=[
            "Rub your palms together to generate warmth",
            "Cup your palms over closed eyes",
            "Don't press on eyeballs",
            "Relax and enjoy the darkness",
            "Breathe deeply"
        ]
    ),
    Exercise(
        name="Focus Shifting",
        description="Alternate focus between near and far objects",
        duration_seconds=45,
        category="eye",
        difficulty="easy",
        benefits=["Exercises ciliary muscles", "Improves focus flexibility"],
        steps=[
            "Hold your thumb 10 inches from your face",
            "Focus on your thumb for 5 seconds",
            "Focus on something far away for 5 seconds",
            "Repeat 5-6 times"
        ]
    ),
    Exercise(
        name="Blink Break",
        description="Conscious blinking to refresh eyes",
        duration_seconds=20,
        category="eye",
        difficulty="easy",
        benefits=["Moisturizes eyes", "Clears vision", "Resets focus"],
        steps=[
            "Blink slowly 10 times",
            "Close your eyes for 5 seconds",
            "Open and look around gently"
        ]
    ),
]

# Stretching Exercises
STRETCH_EXERCISES = [
    Exercise(
        name="Neck Rolls",
        description="Gentle circular neck movements",
        duration_seconds=45,
        category="stretch",
        difficulty="easy",
        benefits=["Releases neck tension", "Improves circulation", "Reduces stiffness"],
        steps=[
            "Drop chin to chest",
            "Slowly roll head to right shoulder",
            "Roll head back",
            "Roll to left shoulder",
            "Complete 3 circles each direction"
        ]
    ),
    Exercise(
        name="Shoulder Shrugs",
        description="Raise and lower shoulders to release tension",
        duration_seconds=30,
        category="stretch",
        difficulty="easy",
        benefits=["Releases shoulder tension", "Improves posture", "Boosts energy"],
        steps=[
            "Raise shoulders towards ears",
            "Hold for 3 seconds",
            "Drop shoulders down",
            "Repeat 5-8 times"
        ]
    ),
    Exercise(
        name="Seated Spinal Twist",
        description="Gentle twist for spine flexibility",
        duration_seconds=60,
        category="stretch",
        difficulty="easy",
        benefits=["Spinal mobility", "Releases back tension", "Aids digestion"],
        steps=[
            "Sit up straight in chair",
            "Place right hand on left knee",
            "Twist torso to the left gently",
            "Hold for 15 seconds",
            "Repeat on other side"
        ]
    ),
    Exercise(
        name="Wrist Circles",
        description="Rotate wrists to prevent carpal tunnel",
        duration_seconds=30,
        category="stretch",
        difficulty="easy",
        benefits=["Prevents RSI", "Improves wrist flexibility", "Reduces typing strain"],
        steps=[
            "Extend arms in front",
            "Make fists",
            "Rotate wrists clockwise 10 times",
            "Rotate counter-clockwise 10 times"
        ]
    ),
    Exercise(
        name="Upper Back Stretch",
        description="Stretch between shoulder blades",
        duration_seconds=30,
        category="stretch",
        difficulty="easy",
        benefits=["Opens chest", "Reduces hunching", "Improves breathing"],
        steps=[
            "Interlace fingers in front",
            "Push palms away from body",
            "Round upper back",
            "Drop chin to chest",
            "Hold for 15-20 seconds"
        ]
    ),
    Exercise(
        name="Standing Side Stretch",
        description="Full body lateral stretch",
        duration_seconds=45,
        category="stretch",
        difficulty="medium",
        benefits=["Stretches obliques", "Improves posture", "Energizes body"],
        steps=[
            "Stand with feet hip-width apart",
            "Raise right arm overhead",
            "Lean to the left",
            "Hold for 15 seconds",
            "Repeat on other side"
        ]
    ),
    Exercise(
        name="Hip Flexor Stretch",
        description="Counter sitting posture",
        duration_seconds=60,
        category="stretch",
        difficulty="medium",
        benefits=["Relieves tight hips", "Improves posture", "Reduces lower back pain"],
        steps=[
            "Stand and take a step back with right foot",
            "Lower into a lunge position",
            "Push hips forward slightly",
            "Hold 20 seconds",
            "Switch legs"
        ]
    ),
]

# Breathing Exercises
BREATHING_EXERCISES = [
    Exercise(
        name="Deep Breathing",
        description="Simple deep breaths for relaxation",
        duration_seconds=60,
        category="breathing",
        difficulty="easy",
        benefits=["Reduces stress", "Increases oxygen", "Calms mind"],
        steps=[
            "Sit comfortably",
            "Breathe in deeply through nose (4 seconds)",
            "Hold breath (2 seconds)",
            "Exhale slowly through mouth (6 seconds)",
            "Repeat 5 times"
        ]
    ),
    Exercise(
        name="Box Breathing",
        description="4-4-4-4 breathing pattern for focus",
        duration_seconds=90,
        category="breathing",
        difficulty="medium",
        benefits=["Enhances focus", "Reduces anxiety", "Regulates nervous system"],
        steps=[
            "Inhale for 4 counts",
            "Hold for 4 counts",
            "Exhale for 4 counts",
            "Hold empty for 4 counts",
            "Repeat 4-5 cycles"
        ]
    ),
    Exercise(
        name="4-7-8 Breathing",
        description="Relaxing breath for stress relief",
        duration_seconds=60,
        category="breathing",
        difficulty="medium",
        benefits=["Deep relaxation", "Reduces tension", "Helps with anxiety"],
        steps=[
            "Exhale completely",
            "Inhale quietly through nose (4 counts)",
            "Hold breath (7 counts)",
            "Exhale through mouth (8 counts)",
            "Repeat 3-4 times"
        ]
    ),
    Exercise(
        name="Energizing Breath",
        description="Quick breaths to boost energy",
        duration_seconds=30,
        category="breathing",
        difficulty="easy",
        benefits=["Increases alertness", "Boosts energy", "Clears mind"],
        steps=[
            "Take 3 quick, deep breaths",
            "On the last breath, exhale forcefully",
            "Repeat 3 times",
            "Return to normal breathing"
        ]
    ),
]

# Quick Energy Boosters
ENERGY_EXERCISES = [
    Exercise(
        name="Desk Push-ups",
        description="Modified push-ups using desk",
        duration_seconds=45,
        category="energy",
        difficulty="medium",
        benefits=["Boosts circulation", "Builds strength", "Increases alertness"],
        steps=[
            "Stand arm's length from desk",
            "Place hands on desk edge",
            "Lower chest towards desk",
            "Push back up",
            "Do 10-15 reps"
        ]
    ),
    Exercise(
        name="Jumping Jacks",
        description="Classic cardio exercise",
        duration_seconds=30,
        category="energy",
        difficulty="medium",
        benefits=["Gets blood flowing", "Wakes up body", "Burns energy"],
        steps=[
            "Stand with feet together",
            "Jump while spreading arms and legs",
            "Return to starting position",
            "Do 15-20 reps"
        ]
    ),
    Exercise(
        name="March in Place",
        description="Simple movement to boost energy",
        duration_seconds=60,
        category="energy",
        difficulty="easy",
        benefits=["Gentle cardio", "Improves circulation", "Low impact"],
        steps=[
            "Stand tall",
            "Lift knees alternately",
            "Swing arms naturally",
            "Continue for 1 minute"
        ]
    ),
    Exercise(
        name="Chair Squats",
        description="Stand up and sit down repeatedly",
        duration_seconds=45,
        category="energy",
        difficulty="easy",
        benefits=["Strengthens legs", "Boosts energy", "Improves circulation"],
        steps=[
            "Stand in front of chair",
            "Lower down as if to sit",
            "Touch chair lightly",
            "Stand back up",
            "Repeat 10-12 times"
        ]
    ),
    Exercise(
        name="Shake It Out",
        description="Shake your whole body",
        duration_seconds=30,
        category="energy",
        difficulty="easy",
        benefits=["Releases tension", "Boosts mood", "Quick energy burst"],
        steps=[
            "Stand with feet shoulder-width",
            "Shake your hands vigorously",
            "Shake your arms",
            "Shake your whole body",
            "Have fun with it!"
        ]
    ),
]


class BreakExerciseManager:
    """Manages break exercise suggestions."""
    
    def __init__(self):
        self.all_exercises = (
            EYE_EXERCISES + 
            STRETCH_EXERCISES + 
            BREATHING_EXERCISES + 
            ENERGY_EXERCISES
        )
        self.completed_today = []
        self.last_suggestion = None
    
    def get_suggestion(self, 
                       category: Optional[str] = None,
                       duration_max: int = 120,
                       difficulty: str = None) -> Exercise:
        """Get a random exercise suggestion."""
        exercises = self.all_exercises.copy()
        
        # Filter by category
        if category:
            exercises = [e for e in exercises if e.category == category]
        
        # Filter by duration
        exercises = [e for e in exercises if e.duration_seconds <= duration_max]
        
        # Filter by difficulty
        if difficulty:
            exercises = [e for e in exercises if e.difficulty == difficulty]
        
        # Avoid repeating last suggestion
        if self.last_suggestion and self.last_suggestion in exercises and len(exercises) > 1:
            exercises.remove(self.last_suggestion)
        
        if not exercises:
            exercises = EYE_EXERCISES  # Default fallback
        
        suggestion = random.choice(exercises)
        self.last_suggestion = suggestion
        return suggestion
    
    def get_eye_exercise(self) -> Exercise:
        """Get an eye exercise specifically."""
        return self.get_suggestion(category="eye")
    
    def get_stretch(self) -> Exercise:
        """Get a stretching exercise."""
        return self.get_suggestion(category="stretch")
    
    def get_breathing_exercise(self) -> Exercise:
        """Get a breathing exercise."""
        return self.get_suggestion(category="breathing")
    
    def get_energy_booster(self) -> Exercise:
        """Get an energy boosting exercise."""
        return self.get_suggestion(category="energy")
    
    def get_quick_routine(self, duration_minutes: int = 5) -> List[Exercise]:
        """Get a quick break routine."""
        routine = []
        total_seconds = duration_minutes * 60
        current_duration = 0
        
        # Always include eye exercise
        eye_ex = self.get_eye_exercise()
        routine.append(eye_ex)
        current_duration += eye_ex.duration_seconds
        
        # Add a stretch
        if current_duration < total_seconds:
            stretch = self.get_stretch()
            routine.append(stretch)
            current_duration += stretch.duration_seconds
        
        # Add breathing or energy based on time left
        if current_duration < total_seconds:
            if random.random() > 0.5:
                routine.append(self.get_breathing_exercise())
            else:
                routine.append(self.get_energy_booster())
        
        return routine
    
    def format_exercise_text(self, exercise: Exercise) -> str:
        """Format exercise as readable text."""
        lines = []
        lines.append(f"🏃 {exercise.name}")
        lines.append(f"   {exercise.description}")
        lines.append(f"   ⏱️ Duration: {exercise.duration_seconds}s")
        lines.append("")
        lines.append("   Steps:")
        for i, step in enumerate(exercise.steps, 1):
            lines.append(f"   {i}. {step}")
        
        return "\n".join(lines)
    
    def format_routine_text(self, routine: List[Exercise]) -> str:
        """Format a routine as readable text."""
        total_time = sum(e.duration_seconds for e in routine)
        
        lines = []
        lines.append("=" * 40)
        lines.append(f"🧘 BREAK ROUTINE ({total_time}s total)")
        lines.append("=" * 40)
        
        for i, exercise in enumerate(routine, 1):
            lines.append(f"\n{i}. {exercise.name} ({exercise.duration_seconds}s)")
            lines.append(f"   {exercise.description}")
            for step in exercise.steps:
                lines.append(f"   • {step}")
        
        lines.append("\n" + "=" * 40)
        return "\n".join(lines)
    
    def mark_completed(self, exercise: Exercise):
        """Mark an exercise as completed today."""
        self.completed_today.append({
            'name': exercise.name,
            'category': exercise.category,
            'duration': exercise.duration_seconds
        })
    
    def get_stats(self) -> Dict:
        """Get today's exercise statistics."""
        total_time = sum(e['duration'] for e in self.completed_today)
        
        by_category = {}
        for e in self.completed_today:
            cat = e['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        return {
            'total_exercises': len(self.completed_today),
            'total_time_seconds': total_time,
            'by_category': by_category
        }


# Category icons for UI
CATEGORY_ICONS = {
    'eye': '👁️',
    'stretch': '🤸',
    'breathing': '🌬️',
    'energy': '⚡'
}

CATEGORY_COLORS = {
    'eye': '#3498DB',
    'stretch': '#27AE60',
    'breathing': '#9B59B6',
    'energy': '#F39C12'
}


def demo():
    """Demo the exercise module."""
    manager = BreakExerciseManager()
    
    print("=" * 50)
    print("🧘 BREAK EXERCISE SUGGESTIONS")
    print("=" * 50)
    
    print("\n👁️ Eye Exercise:")
    print(manager.format_exercise_text(manager.get_eye_exercise()))
    
    print("\n🤸 Stretch:")
    print(manager.format_exercise_text(manager.get_stretch()))
    
    print("\n🌬️ Breathing:")
    print(manager.format_exercise_text(manager.get_breathing_exercise()))
    
    print("\n⚡ Energy Booster:")
    print(manager.format_exercise_text(manager.get_energy_booster()))
    
    print("\n" + "=" * 50)
    print("QUICK 5-MINUTE ROUTINE:")
    routine = manager.get_quick_routine(5)
    print(manager.format_routine_text(routine))


if __name__ == "__main__":
    demo()
