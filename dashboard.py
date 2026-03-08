"""
Enhanced Dashboard Module for AI Study Monitor

Provides:
- Tabbed interface with multiple views
- Analytics dashboard with charts
- Break exercise display
- Goals and achievements panel
- Eye strain monitor status
- Multi-user statistics
"""

import customtkinter as ctk
import threading
import os
from typing import Callable, Optional
from PIL import Image
import io

try:
    from analytics import ProductivityAnalyzer, ChartGenerator, GoalTracker, ReportGenerator
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False

try:
    from exercises import BreakExerciseManager, Exercise, CATEGORY_ICONS
    EXERCISES_AVAILABLE = True
except ImportError:
    EXERCISES_AVAILABLE = False

try:
    from notifications import DesktopNotifier
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

try:
    from user_manager import get_user_manager, FACE_RECOGNITION_AVAILABLE
    USER_MANAGER_AVAILABLE = True
except ImportError:
    USER_MANAGER_AVAILABLE = False
    FACE_RECOGNITION_AVAILABLE = False


class DashboardWindow(ctk.CTkToplevel):
    """
    Dashboard window with tabs for analytics, exercises, and achievements.
    """
    
    def __init__(self, parent, analyzer: 'ProductivityAnalyzer' = None):
        super().__init__(parent)
        
        self.title("📊 Study Dashboard")
        self.geometry("700x550")
        self.minsize(600, 450)
        
        self.analyzer = analyzer or (ProductivityAnalyzer() if ANALYTICS_AVAILABLE else None)
        self.goal_tracker = GoalTracker() if ANALYTICS_AVAILABLE else None
        
        self._create_tabs()
    
    def _create_tabs(self):
        """Create tabbed interface."""
        self.tabview = ctk.CTkTabview(self, width=680)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.tabview.add("📊 Analytics")
        self.tabview.add("👥 Users")
        self.tabview.add("🏃 Exercises")
        self.tabview.add("🏆 Achievements")
        self.tabview.add("📝 Report")
        
        self._create_analytics_tab()
        self._create_users_tab()
        self._create_exercises_tab()
        self._create_achievements_tab()
        self._create_report_tab()
    
    def _create_analytics_tab(self):
        """Create analytics dashboard tab with improved visualizations."""
        tab = self.tabview.tab("📊 Analytics")
        
        if not ANALYTICS_AVAILABLE or not self.analyzer:
            ctk.CTkLabel(tab, text="Analytics module not available").pack()
            return
        
        # Reload data
        self.analyzer = ProductivityAnalyzer()
        
        # Create scrollable container
        scroll = ctk.CTkScrollableFrame(tab, width=650, height=450)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # ============ Weekly Summary Cards ============
        summary_frame = ctk.CTkFrame(scroll)
        summary_frame.pack(fill="x", padx=10, pady=10)
        summary_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        weekly = self.analyzer.get_weekly_summary()
        
        self._create_stat_card(summary_frame, "📚 Hours", f"{weekly['total_hours']}", 0)
        self._create_stat_card(summary_frame, "🍅 Pomodoros", str(weekly['total_pomodoros']), 1)
        self._create_stat_card(summary_frame, "🎯 Focus", f"{weekly['average_focus']}%", 2)
        self._create_stat_card(summary_frame, "🔥 Streak", f"{weekly['streak']} days", 3)
        
        # ============ Week Comparison ============
        comparison_frame = ctk.CTkFrame(scroll)
        comparison_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(comparison_frame, text="📈 Week Comparison", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        comparison = self.analyzer.get_week_comparison()
        
        comp_inner = ctk.CTkFrame(comparison_frame, fg_color="transparent")
        comp_inner.pack(fill="x", padx=10, pady=5)
        comp_inner.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Headers
        ctk.CTkLabel(comp_inner, text="Metric").grid(row=0, column=0, pady=5)
        ctk.CTkLabel(comp_inner, text="This Week", font=("Helvetica", 11, "bold")).grid(row=0, column=1)
        ctk.CTkLabel(comp_inner, text="vs Last Week", font=("Helvetica", 11, "bold")).grid(row=0, column=2)
        
        metrics = [
            ("Study Hours", comparison['this_week']['hours'], comparison['change']['hours']),
            ("Pomodoros", comparison['this_week']['pomodoros'], comparison['change']['pomodoros']),
            ("Focus %", comparison['this_week']['focus'], comparison['change']['focus'])
        ]
        
        for i, (name, value, change) in enumerate(metrics, 1):
            ctk.CTkLabel(comp_inner, text=name).grid(row=i, column=0, pady=2)
            ctk.CTkLabel(comp_inner, text=str(value), font=("Helvetica", 12, "bold")).grid(row=i, column=1)
            
            # Change indicator with color
            change_text = f"+{change}%" if change >= 0 else f"{change}%"
            change_color = "#2ECC71" if change >= 0 else "#E74C3C"
            arrow = "↑" if change >= 0 else "↓"
            ctk.CTkLabel(comp_inner, text=f"{arrow} {change_text}", text_color=change_color).grid(row=i, column=2)
        
        # ============ Smart Insights ============
        insights_frame = ctk.CTkFrame(scroll)
        insights_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(insights_frame, text="💡 Smart Insights", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        insights = self.analyzer.get_insights()
        for insight in insights:
            ctk.CTkLabel(insights_frame, text=f"  {insight}", anchor="w", justify="left").pack(anchor="w", padx=15, pady=2)
        
        if not insights:
            ctk.CTkLabel(insights_frame, text="  📊 Study more to see personalized insights!", text_color="gray").pack(anchor="w", padx=15)
        
        # ============ Best Study Time ============
        time_frame = ctk.CTkFrame(scroll)
        time_frame.pack(fill="x", padx=10, pady=10)
        
        best_time = self.analyzer.get_best_study_time()
        ctk.CTkLabel(time_frame, text="⏰ Your Best Study Time", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(time_frame, text=f"  {best_time}", font=("Helvetica", 12)).pack(anchor="w", padx=15, pady=5)
        
        # ============ Goal Progress ============
        goals_frame = ctk.CTkFrame(scroll)
        goals_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(goals_frame, text="🎯 Today's Goals", font=("Helvetica", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        if self.goal_tracker:
            progress = self.goal_tracker.get_progress(self.analyzer)
            
            for goal_name, data in progress.items():
                frame = ctk.CTkFrame(goals_frame, fg_color="transparent")
                frame.pack(fill="x", padx=10, pady=3)
                
                # Goal name (formatted)
                display_name = goal_name.replace('_', ' ').title()
                ctk.CTkLabel(frame, text=display_name, width=120, anchor="w").pack(side="left")
                
                # Progress bar with color based on progress
                bar = ctk.CTkProgressBar(frame, width=250, height=15)
                progress_val = min(data['progress'] / 100, 1.0)
                bar.set(progress_val)
                
                # Color gradient based on progress
                if progress_val >= 1.0:
                    bar.configure(progress_color="#2ECC71")  # Green - completed
                elif progress_val >= 0.5:
                    bar.configure(progress_color="#3498DB")  # Blue - good progress
                else:
                    bar.configure(progress_color="#F39C12")  # Orange - keep going
                    
                bar.pack(side="left", padx=5)
                
                # Progress text
                pct_text = f"{data['progress']:.0f}%"
                if data['progress'] >= 100:
                    pct_text = "✅ Done!"
                ctk.CTkLabel(frame, text=pct_text, width=60).pack(side="left", padx=5)
        
        # ============ Productivity Score ============
        score_frame = ctk.CTkFrame(scroll)
        score_frame.pack(fill="x", padx=10, pady=10)
        score_frame.grid_columnconfigure((0, 1), weight=1)
        
        score = self.analyzer.calculate_productivity_score()
        
        # Left side: Score
        left = ctk.CTkFrame(score_frame, fg_color="transparent")
        left.grid(row=0, column=0, padx=10, pady=10)
        
        ctk.CTkLabel(left, text="🏆 Productivity Score", font=("Helvetica", 14, "bold")).pack()
        
        score_label = ctk.CTkLabel(left, text=f"{score:.0f}", font=("Helvetica", 48, "bold"))
        score_label.pack()
        
        if score >= 80:
            score_label.configure(text_color="#2ECC71")
            rating = "⭐⭐⭐⭐⭐ Excellent!"
        elif score >= 60:
            score_label.configure(text_color="#27AE60")
            rating = "⭐⭐⭐⭐ Good"
        elif score >= 40:
            score_label.configure(text_color="#F39C12")
            rating = "⭐⭐⭐ Average"
        else:
            score_label.configure(text_color="#E74C3C")
            rating = "⭐⭐ Keep going!"
        
        ctk.CTkLabel(left, text=rating).pack()
        
        # Right side: Daily breakdown mini-chart
        right = ctk.CTkFrame(score_frame, fg_color="transparent")
        right.grid(row=0, column=1, padx=10, pady=10)
        
        ctk.CTkLabel(right, text="📊 This Week", font=("Helvetica", 12, "bold")).pack()
        
        daily_stats = self.analyzer.get_daily_stats(7)
        max_hours = max(d['study_hours'] for d in daily_stats) if daily_stats else 1
        
        chart_frame = ctk.CTkFrame(right, fg_color="transparent")
        chart_frame.pack(pady=5)
        
        for i, day in enumerate(daily_stats):
            day_frame = ctk.CTkFrame(chart_frame, fg_color="transparent", width=35)
            day_frame.pack(side="left", padx=2)
            
            # Bar height proportional to hours
            bar_height = max(int((day['study_hours'] / max_hours) * 50), 5) if max_hours > 0 else 5
            
            bar = ctk.CTkFrame(day_frame, width=20, height=bar_height, fg_color="#3498DB")
            bar.pack()
            
            ctk.CTkLabel(day_frame, text=day['day_name'][:2], font=("Helvetica", 9)).pack()
        
        # ============ Generate Charts Button ============
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        def generate_charts():
            chart_gen = ChartGenerator()
            chart_gen.generate_weekly_chart(self.analyzer)
            chart_gen.generate_focus_trend(self.analyzer)
            chart_gen.generate_emotion_trends(self.analyzer)
            
            # Show success message
            success_popup = ctk.CTkToplevel(self)
            success_popup.title("Success")
            success_popup.geometry("300x100")
            success_popup.transient(self)
            ctk.CTkLabel(success_popup, text="📈 Charts saved to 'charts/' folder!", font=("Helvetica", 12)).pack(pady=20)
            ctk.CTkButton(success_popup, text="OK", command=success_popup.destroy, width=80).pack()
        
        ctk.CTkButton(btn_frame, text="📈 Generate Detailed Charts", command=generate_charts).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🔄 Refresh Data", command=lambda: self._refresh_analytics(scroll)).pack(side="left", padx=5)
    
    def _refresh_analytics(self, scroll):
        """Refresh analytics data."""
        self.analyzer = ProductivityAnalyzer()
        # Rebuild the tab
        for widget in scroll.winfo_children():
            widget.destroy()
        self._create_analytics_tab()
    
    def _create_users_tab(self):
        """Create multi-user statistics tab."""
        tab = self.tabview.tab("👥 Users")
        
        if not USER_MANAGER_AVAILABLE or not FACE_RECOGNITION_AVAILABLE:
            ctk.CTkLabel(tab, text="Multi-user mode not available.\nInstall face_recognition to enable.", 
                         font=("Helvetica", 12), text_color="gray").pack(pady=50)
            return
        
        user_manager = get_user_manager()
        users = user_manager.get_all_users()
        
        if not users:
            ctk.CTkLabel(tab, text="No users registered yet.\nClick 👥 Users button on main screen to register.", 
                         font=("Helvetica", 12), text_color="gray").pack(pady=50)
            return
        
        # Title
        ctk.CTkLabel(tab, text="🏆 User Leaderboard", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        # Leaderboard
        leaderboard = user_manager.get_leaderboard()
        
        lb_frame = ctk.CTkFrame(tab)
        lb_frame.pack(fill="x", padx=20, pady=10)
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, entry in enumerate(leaderboard):
            row = ctk.CTkFrame(lb_frame)
            row.pack(fill="x", pady=3)
            row.grid_columnconfigure(1, weight=1)
            
            # Rank
            rank = medals[i] if i < 3 else f" {i+1}."
            ctk.CTkLabel(row, text=rank, font=("Helvetica", 16), width=40).pack(side="left", padx=10)
            
            # Name
            ctk.CTkLabel(row, text=entry['name'], font=("Helvetica", 14, "bold")).pack(side="left", padx=10)
            
            # Stats
            h, r = divmod(int(entry['total_seconds']), 3600)
            m = r // 60
            stats_text = f"📚 {h}h {m}m  |  🍅 {entry['pomodoros']}"
            ctk.CTkLabel(row, text=stats_text, font=("Helvetica", 11)).pack(side="right", padx=10)
        
        # Individual stats section
        ctk.CTkLabel(tab, text="📊 User Details", font=("Helvetica", 14, "bold")).pack(pady=(20, 10))
        
        details_frame = ctk.CTkScrollableFrame(tab, height=200)
        details_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        for user in users:
            user_frame = ctk.CTkFrame(details_frame)
            user_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(user_frame, text=f"👤 {user.name}", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10, pady=5)
            
            h, r = divmod(int(user.total_study_seconds), 3600)
            m = r // 60
            
            info = f"  Total: {h}h {m}m  |  Sessions: {user.total_sessions}  |  Pomodoros: {user.total_pomodoros}"
            ctk.CTkLabel(user_frame, text=info, font=("Helvetica", 10), text_color="gray").pack(anchor="w", padx=10, pady=(0, 5))
    
    def _create_stat_card(self, parent, title: str, value: str, col: int):
        """Create a statistics card widget."""
        card = ctk.CTkFrame(parent)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(card, text=title, font=("Helvetica", 12)).pack(pady=(10, 5))
        ctk.CTkLabel(card, text=value, font=("Helvetica", 24, "bold")).pack(pady=(0, 10))
    
    def _create_exercises_tab(self):
        """Create exercises suggestion tab."""
        tab = self.tabview.tab("🏃 Exercises")
        
        if not EXERCISES_AVAILABLE:
            ctk.CTkLabel(tab, text="Exercises module not available").pack()
            return
        
        self.exercise_manager = BreakExerciseManager()
        
        # Category buttons
        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(btn_frame, text="Get Exercise Suggestion:", font=("Helvetica", 12, "bold")).pack(side="left", padx=10)
        
        ctk.CTkButton(btn_frame, text="👁️ Eye", width=80, command=lambda: self._show_exercise('eye')).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🤸 Stretch", width=80, command=lambda: self._show_exercise('stretch')).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="🌬️ Breathing", width=80, command=lambda: self._show_exercise('breathing')).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="⚡ Energy", width=80, command=lambda: self._show_exercise('energy')).pack(side="left", padx=5)
        
        # Exercise display area
        self.exercise_frame = ctk.CTkFrame(tab)
        self.exercise_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Default: Show a random exercise
        self._show_exercise(None)
        
        # Quick routine button
        ctk.CTkButton(tab, text="🧘 Get 5-min Break Routine", command=self._show_routine).pack(pady=10)
    
    def _show_exercise(self, category: Optional[str]):
        """Display an exercise suggestion."""
        # Clear previous
        for widget in self.exercise_frame.winfo_children():
            widget.destroy()
        
        exercise = self.exercise_manager.get_suggestion(category=category)
        
        # Exercise title
        icon = CATEGORY_ICONS.get(exercise.category, '🏃')
        ctk.CTkLabel(
            self.exercise_frame, 
            text=f"{icon} {exercise.name}",
            font=("Helvetica", 18, "bold")
        ).pack(pady=10)
        
        # Description
        ctk.CTkLabel(
            self.exercise_frame,
            text=exercise.description,
            font=("Helvetica", 12)
        ).pack()
        
        # Duration
        ctk.CTkLabel(
            self.exercise_frame,
            text=f"⏱️ Duration: {exercise.duration_seconds} seconds",
            font=("Helvetica", 12)
        ).pack(pady=5)
        
        # Steps
        steps_frame = ctk.CTkFrame(self.exercise_frame)
        steps_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(steps_frame, text="Steps:", font=("Helvetica", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        
        for i, step in enumerate(exercise.steps, 1):
            ctk.CTkLabel(steps_frame, text=f"  {i}. {step}", anchor="w").pack(anchor="w", padx=10)
        
        # Benefits
        benefits_text = "Benefits: " + ", ".join(exercise.benefits)
        ctk.CTkLabel(self.exercise_frame, text=benefits_text, wraplength=500).pack(pady=10)
    
    def _show_routine(self):
        """Show a 5-minute break routine."""
        for widget in self.exercise_frame.winfo_children():
            widget.destroy()
        
        routine = self.exercise_manager.get_quick_routine(5)
        total_time = sum(e.duration_seconds for e in routine)
        
        ctk.CTkLabel(
            self.exercise_frame,
            text=f"🧘 5-Minute Break Routine ({total_time}s total)",
            font=("Helvetica", 16, "bold")
        ).pack(pady=10)
        
        for i, exercise in enumerate(routine, 1):
            frame = ctk.CTkFrame(self.exercise_frame)
            frame.pack(fill="x", padx=10, pady=5)
            
            icon = CATEGORY_ICONS.get(exercise.category, '🏃')
            ctk.CTkLabel(
                frame,
                text=f"{i}. {icon} {exercise.name} ({exercise.duration_seconds}s)",
                font=("Helvetica", 12, "bold"),
                anchor="w"
            ).pack(anchor="w", padx=10, pady=5)
            
            ctk.CTkLabel(
                frame,
                text=exercise.description,
                anchor="w"
            ).pack(anchor="w", padx=20)
    
    def _create_achievements_tab(self):
        """Create achievements display tab."""
        tab = self.tabview.tab("🏆 Achievements")
        
        if not ANALYTICS_AVAILABLE or not self.goal_tracker:
            ctk.CTkLabel(tab, text="Achievements module not available").pack()
            return
        
        # Check for new achievements
        new_achievements = self.goal_tracker.check_achievements(self.analyzer)
        
        if new_achievements:
            for achievement_name in new_achievements:
                ctk.CTkLabel(
                    tab,
                    text=f"🎉 NEW: {achievement_name}",
                    font=("Helvetica", 14, "bold"),
                    text_color="#2ECC71"
                ).pack(pady=5)
        
        # Display all achievements
        scroll = ctk.CTkScrollableFrame(tab, width=600, height=350)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(scroll, text="Your Achievements", font=("Helvetica", 16, "bold")).pack(pady=10)
        
        for achievement in self.goal_tracker.achievements:
            frame = ctk.CTkFrame(scroll)
            frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(
                frame,
                text=achievement['name'],
                font=("Helvetica", 14, "bold")
            ).pack(anchor="w", padx=10, pady=(10, 0))
            
            ctk.CTkLabel(
                frame,
                text=achievement['description']
            ).pack(anchor="w", padx=10)
            
            earned_date = achievement.get('earned_date', 'Unknown')[:10]
            ctk.CTkLabel(
                frame,
                text=f"Earned: {earned_date}",
                text_color="gray"
            ).pack(anchor="w", padx=10, pady=(0, 10))
        
        if not self.goal_tracker.achievements:
            ctk.CTkLabel(scroll, text="No achievements yet. Keep studying!").pack()
    
    def _create_report_tab(self):
        """Create report generation tab."""
        tab = self.tabview.tab("📝 Report")
        
        if not ANALYTICS_AVAILABLE:
            ctk.CTkLabel(tab, text="Report module not available").pack()
            return
        
        # Report preview
        reporter = ReportGenerator(self.analyzer)
        report_text = reporter.generate_text_report()
        
        # Text display
        textbox = ctk.CTkTextbox(tab, width=650, height=400)
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("1.0", report_text)
        textbox.configure(state="disabled")
        
        # Save button
        def save_report():
            filename = reporter.save_report()
            print(f"Report saved to {filename}")
        
        ctk.CTkButton(tab, text="💾 Save Report", command=save_report).pack(pady=10)


class ExercisePopup(ctk.CTkToplevel):
    """Popup window for break exercise suggestion."""
    
    def __init__(self, parent, exercise: 'Exercise'):
        super().__init__(parent)
        
        self.title("🧘 Break Exercise")
        self.geometry("400x350")
        self.resizable(False, False)
        
        # Make it stay on top
        self.attributes('-topmost', True)
        
        icon = CATEGORY_ICONS.get(exercise.category, '🏃') if EXERCISES_AVAILABLE else '🏃'
        
        # Exercise name
        ctk.CTkLabel(
            self,
            text=f"{icon} {exercise.name}",
            font=("Helvetica", 18, "bold")
        ).pack(pady=15)
        
        # Duration
        ctk.CTkLabel(
            self,
            text=f"⏱️ {exercise.duration_seconds} seconds"
        ).pack()
        
        # Description
        ctk.CTkLabel(
            self,
            text=exercise.description,
            font=("Helvetica", 12)
        ).pack(pady=10)
        
        # Steps
        steps_frame = ctk.CTkFrame(self)
        steps_frame.pack(fill="x", padx=20, pady=10)
        
        for i, step in enumerate(exercise.steps, 1):
            ctk.CTkLabel(steps_frame, text=f"{i}. {step}", anchor="w").pack(anchor="w", padx=10)
        
        # Done button
        ctk.CTkButton(
            self,
            text="✅ Done",
            command=self.destroy,
            fg_color="#2ECC71"
        ).pack(pady=15)


class EyeStrainStatusWidget(ctk.CTkFrame):
    """Widget showing eye strain status."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self, text="👁️ Eye Health", font=("Helvetica", 12, "bold")).grid(row=0, column=0, pady=5)
        
        self.lbl_blink_rate = ctk.CTkLabel(self, text="Blinks: --/min")
        self.lbl_blink_rate.grid(row=1, column=0)
        
        self.lbl_fatigue = ctk.CTkLabel(self, text="Fatigue: Low")
        self.lbl_fatigue.grid(row=2, column=0)
        
        self.health_bar = ctk.CTkProgressBar(self, width=150)
        self.health_bar.grid(row=3, column=0, pady=5)
        self.health_bar.set(1.0)
    
    def update_metrics(self, blink_rate: float, fatigue_level: str, health_score: int):
        """Update displayed metrics."""
        self.lbl_blink_rate.configure(text=f"Blinks: {blink_rate:.0f}/min")
        
        fatigue_colors = {'low': '#2ECC71', 'medium': '#F39C12', 'high': '#E74C3C'}
        self.lbl_fatigue.configure(
            text=f"Fatigue: {fatigue_level.title()}",
            text_color=fatigue_colors.get(fatigue_level, 'gray')
        )
        
        self.health_bar.set(health_score / 100)


def show_dashboard(parent=None):
    """Show the dashboard window."""
    if parent:
        dashboard = DashboardWindow(parent)
        dashboard.grab_set()
    else:
        # Standalone mode
        root = ctk.CTk()
        root.withdraw()
        dashboard = DashboardWindow(root)
        dashboard.mainloop()


if __name__ == "__main__":
    show_dashboard()
