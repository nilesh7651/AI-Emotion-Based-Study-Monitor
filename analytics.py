"""
Analytics and Visualization Module for AI Study Monitor

Provides:
- Study pattern analysis
- Productivity scoring
- Visualizations (charts and graphs)
- PDF/Excel report generation
- Goal tracking
"""

import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple

# Try importing visualization libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for saving
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not installed. Charts disabled.")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class ProductivityAnalyzer:
    """Analyzes study patterns and calculates productivity metrics."""
    
    def __init__(self, history_file="session_history.json"):
        self.history_file = history_file
        self.sessions = self._load_sessions()
    
    def _load_sessions(self) -> List[Dict]:
        """Load session history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def calculate_productivity_score(self, session: Dict = None) -> float:
        """
        Calculate a productivity score (0-100) based on:
        - Focus percentage (40%)
        - Study duration vs goal (30%)
        - Pomodoros completed (20%)
        - Consistency (10%)
        """
        if session is None:
            # Use latest session
            if not self.sessions:
                return 0.0
            session = self.sessions[-1]
        
        score = 0.0
        
        # Focus percentage (max 40 points)
        focus_pct = session.get('focus_percentage', 0)
        score += (focus_pct / 100) * 40
        
        # Study duration (max 30 points) - assume 2 hours is excellent
        study_seconds = session.get('total_study_seconds', 0)
        target_seconds = 2 * 60 * 60  # 2 hours
        duration_ratio = min(study_seconds / target_seconds, 1.0)
        score += duration_ratio * 30
        
        # Pomodoros (max 20 points) - 4 pomodoros is excellent
        pomodoros = session.get('pomodoros_completed', 0)
        pomodoro_ratio = min(pomodoros / 4, 1.0)
        score += pomodoro_ratio * 20
        
        # Stress penalty (reduce score if highly stressed)
        emotions = session.get('emotion_breakdown', {})
        stress_pct = emotions.get('Stressed', 0)
        if stress_pct > 30:
            score *= (1 - (stress_pct - 30) / 100)
        
        # Consistency bonus (10 points if studied yesterday too)
        if self._studied_yesterday():
            score += 10
        
        return min(max(score, 0), 100)
    
    def _studied_yesterday(self) -> bool:
        """Check if there was a study session yesterday."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        for session in self.sessions:
            if session.get('start_time', '').startswith(yesterday):
                if session.get('total_study_seconds', 0) > 300:  # At least 5 min
                    return True
        return False
    
    def get_streak(self) -> int:
        """Calculate current study streak (consecutive days)."""
        if not self.sessions:
            return 0
        
        streak = 0
        check_date = datetime.now().date()
        
        while True:
            date_str = check_date.strftime("%Y-%m-%d")
            found = False
            
            for session in self.sessions:
                if session.get('start_time', '').startswith(date_str):
                    if session.get('total_study_seconds', 0) > 300:
                        found = True
                        break
            
            if found:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """Get daily aggregated statistics for the last N days."""
        stats = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            day_study = 0.0
            day_pomodoros = 0
            day_focus = []
            
            for session in self.sessions:
                if session.get('start_time', '').startswith(date_str):
                    day_study += session.get('total_study_seconds', 0)
                    day_pomodoros += session.get('pomodoros_completed', 0)
                    if session.get('focus_percentage'):
                        day_focus.append(session['focus_percentage'])
            
            stats.append({
                'date': date_str,
                'day_name': date.strftime("%a"),
                'study_hours': day_study / 3600,
                'pomodoros': day_pomodoros,
                'focus_avg': sum(day_focus) / len(day_focus) if day_focus else 0
            })
        
        return stats[::-1]  # Oldest first
    
    def get_weekly_summary(self) -> Dict:
        """Get summary statistics for the current week."""
        daily_stats = self.get_daily_stats(7)
        
        total_hours = sum(d['study_hours'] for d in daily_stats)
        total_pomodoros = sum(d['pomodoros'] for d in daily_stats)
        avg_focus = sum(d['focus_avg'] for d in daily_stats) / 7 if daily_stats else 0
        
        return {
            'total_hours': round(total_hours, 1),
            'total_pomodoros': total_pomodoros,
            'average_focus': round(avg_focus, 1),
            'streak': self.get_streak(),
            'best_day': max(daily_stats, key=lambda x: x['study_hours'])['day_name'] if daily_stats else 'N/A'
        }
    
    def get_emotion_trends(self, days: int = 7) -> Dict[str, List[float]]:
        """Get emotion trends over time."""
        trends = defaultdict(list)
        daily = self.get_daily_stats(days)
        
        for day in daily:
            date_str = day['date']
            day_emotions = defaultdict(list)
            
            for session in self.sessions:
                if session.get('start_time', '').startswith(date_str):
                    for emotion, pct in session.get('emotion_breakdown', {}).items():
                        day_emotions[emotion].append(pct)
            
            for emotion in ['Focused', 'Stressed', 'Bored', 'Distracted']:
                if day_emotions[emotion]:
                    trends[emotion].append(sum(day_emotions[emotion]) / len(day_emotions[emotion]))
                else:
                    trends[emotion].append(0)
        
        return dict(trends)
    
    def get_hourly_breakdown(self, days: int = 7) -> Dict[int, float]:
        """Get study hours breakdown by hour of day (0-23)."""
        hourly = defaultdict(float)
        
        for session in self.sessions:
            start_time = session.get('start_time', '')
            if not start_time:
                continue
            try:
                dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                if (datetime.now() - dt).days <= days:
                    hour = dt.hour
                    hourly[hour] += session.get('total_study_seconds', 0) / 3600
            except:
                pass
        
        return dict(hourly)
    
    def get_best_study_time(self) -> str:
        """Determine when user studies most productively."""
        hourly = self.get_hourly_breakdown(30)  # Last 30 days
        
        if not hourly:
            return "Not enough data"
        
        # Group into time periods
        morning = sum(hourly.get(h, 0) for h in range(6, 12))    # 6am-12pm
        afternoon = sum(hourly.get(h, 0) for h in range(12, 17)) # 12pm-5pm
        evening = sum(hourly.get(h, 0) for h in range(17, 21))   # 5pm-9pm
        night = sum(hourly.get(h, 0) for h in range(21, 24)) + sum(hourly.get(h, 0) for h in range(0, 6))
        
        periods = {'🌅 Morning (6am-12pm)': morning, '☀️ Afternoon (12pm-5pm)': afternoon, 
                   '🌆 Evening (5pm-9pm)': evening, '🌙 Night (9pm-6am)': night}
        
        return max(periods, key=periods.get) if max(periods.values()) > 0 else "No pattern yet"
    
    def get_week_comparison(self) -> Dict:
        """Compare this week vs last week."""
        this_week = self.get_daily_stats(7)
        
        # Shift dates to get last week
        old_sessions = self.sessions
        last_week_sessions = []
        for session in self.sessions:
            start_time = session.get('start_time', '')
            if start_time:
                try:
                    dt = datetime.strptime(start_time.split()[0], "%Y-%m-%d")
                    days_ago = (datetime.now() - dt).days
                    if 7 <= days_ago <= 14:
                        last_week_sessions.append(session)
                except:
                    pass
        
        this_week_hours = sum(d['study_hours'] for d in this_week)
        this_week_pomos = sum(d['pomodoros'] for d in this_week)
        this_week_focus = sum(d['focus_avg'] for d in this_week) / 7 if this_week else 0
        
        last_week_hours = sum(s.get('total_study_seconds', 0) for s in last_week_sessions) / 3600
        last_week_pomos = sum(s.get('pomodoros_completed', 0) for s in last_week_sessions)
        last_week_focus_list = [s.get('focus_percentage', 0) for s in last_week_sessions if s.get('focus_percentage')]
        last_week_focus = sum(last_week_focus_list) / len(last_week_focus_list) if last_week_focus_list else 0
        
        def calc_change(current, previous):
            if previous == 0:
                return 100 if current > 0 else 0
            return ((current - previous) / previous) * 100
        
        return {
            'this_week': {'hours': round(this_week_hours, 1), 'pomodoros': this_week_pomos, 'focus': round(this_week_focus, 1)},
            'last_week': {'hours': round(last_week_hours, 1), 'pomodoros': last_week_pomos, 'focus': round(last_week_focus, 1)},
            'change': {
                'hours': round(calc_change(this_week_hours, last_week_hours), 1),
                'pomodoros': round(calc_change(this_week_pomos, last_week_pomos), 1),
                'focus': round(calc_change(this_week_focus, last_week_focus), 1)
            }
        }
    
    def get_insights(self) -> List[str]:
        """Generate smart insights based on study patterns."""
        insights = []
        weekly = self.get_weekly_summary()
        comparison = self.get_week_comparison()
        hourly = self.get_hourly_breakdown(14)
        
        # Trend insights
        if comparison['change']['hours'] > 20:
            insights.append(f"📈 Great progress! You studied {comparison['change']['hours']:.0f}% more than last week.")
        elif comparison['change']['hours'] < -20:
            insights.append(f"📉 Your study time dropped {abs(comparison['change']['hours']):.0f}% from last week.")
        
        # Focus insights
        if weekly['average_focus'] >= 80:
            insights.append("🎯 Outstanding focus! You're in the zone.")
        elif weekly['average_focus'] < 50:
            insights.append("💭 Your focus is low. Try shorter sessions or reduce distractions.")
        
        # Streak insights
        streak = weekly['streak']
        if streak >= 7:
            insights.append(f"🔥 Amazing {streak}-day streak! Keep it up!")
        elif streak == 0:
            insights.append("⏰ Start a new streak today! Consistency builds habits.")
        
        # Time pattern insights
        best_time = self.get_best_study_time()
        if "Night" in best_time:
            insights.append("🦉 You're a night owl! Your best study time is in the evening.")
        elif "Morning" in best_time:
            insights.append("🐦 Early bird! You're most productive in the morning.")
        
        # Study amount insights
        if weekly['total_hours'] < 5:
            insights.append(f"📚 Only {weekly['total_hours']}h this week. Try adding 30 min daily.")
        elif weekly['total_hours'] >= 20:
            insights.append(f"💪 {weekly['total_hours']}h this week - excellent dedication!")
        
        return insights[:5]  # Return top 5 insights


class ChartGenerator:
    """Generates visualization charts for study data."""
    
    def __init__(self, output_dir="charts"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def generate_weekly_chart(self, analyzer: ProductivityAnalyzer) -> str:
        """Generate weekly study hours bar chart."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        daily_stats = analyzer.get_daily_stats(7)
        
        days = [d['day_name'] for d in daily_stats]
        hours = [d['study_hours'] for d in daily_stats]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        bars = ax.bar(days, hours, color='#2ECC71', edgecolor='white', linewidth=1.2)
        
        # Add value labels on bars
        for bar, hour in zip(bars, hours):
            if hour > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                       f'{hour:.1f}h', ha='center', va='bottom', fontsize=10)
        
        ax.set_xlabel('Day', fontsize=12)
        ax.set_ylabel('Study Hours', fontsize=12)
        ax.set_title('📚 Weekly Study Time', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(hours) * 1.2 if hours else 5)
        
        # Style
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('white')
        
        filepath = os.path.join(self.output_dir, 'weekly_hours.png')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_emotion_pie(self, session: Dict) -> str:
        """Generate emotion breakdown pie chart."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        emotions = session.get('emotion_breakdown', {})
        if not emotions:
            return None
        
        labels = list(emotions.keys())
        sizes = list(emotions.values())
        colors = {
            'Focused': '#2ECC71',
            'Stressed': '#E74C3C',
            'Bored': '#F39C12',
            'Distracted': '#9B59B6',
            'Uncertain': '#95A5A6'
        }
        
        pie_colors = [colors.get(l, '#3498DB') for l in labels]
        
        fig, ax = plt.subplots(figsize=(8, 8))
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct='%1.1f%%',
            colors=pie_colors, pctdistance=0.7,
            wedgeprops=dict(width=0.5, edgecolor='white')
        )
        
        ax.set_title('🎭 Emotion Breakdown', fontsize=14, fontweight='bold')
        
        filepath = os.path.join(self.output_dir, 'emotion_pie.png')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_focus_trend(self, analyzer: ProductivityAnalyzer, days: int = 7) -> str:
        """Generate focus percentage trend line chart."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        daily_stats = analyzer.get_daily_stats(days)
        
        dates = [d['day_name'] for d in daily_stats]
        focus = [d['focus_avg'] for d in daily_stats]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(dates, focus, marker='o', color='#3498DB', linewidth=2, markersize=8)
        ax.fill_between(dates, focus, alpha=0.3, color='#3498DB')
        
        ax.set_xlabel('Day', fontsize=12)
        ax.set_ylabel('Focus %', fontsize=12)
        ax.set_title('🎯 Focus Trend', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 100)
        
        # Add threshold line
        ax.axhline(y=70, color='#2ECC71', linestyle='--', alpha=0.7, label='Good Focus (70%)')
        ax.legend()
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_facecolor('#f8f9fa')
        
        filepath = os.path.join(self.output_dir, 'focus_trend.png')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def generate_emotion_trends(self, analyzer: ProductivityAnalyzer, days: int = 7) -> str:
        """Generate stacked area chart of emotion trends."""
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        trends = analyzer.get_emotion_trends(days)
        daily_stats = analyzer.get_daily_stats(days)
        dates = [d['day_name'] for d in daily_stats]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        colors = {
            'Focused': '#2ECC71',
            'Stressed': '#E74C3C',
            'Bored': '#F39C12',
            'Distracted': '#9B59B6'
        }
        
        for emotion in ['Focused', 'Stressed', 'Bored', 'Distracted']:
            if emotion in trends:
                ax.plot(dates, trends[emotion], marker='o', label=emotion, 
                       color=colors[emotion], linewidth=2)
        
        ax.set_xlabel('Day', fontsize=12)
        ax.set_ylabel('Percentage %', fontsize=12)
        ax.set_title('📊 Emotion Trends Over Time', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.set_ylim(0, 100)
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        filepath = os.path.join(self.output_dir, 'emotion_trends.png')
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath


class ReportGenerator:
    """Generates PDF/text reports of study sessions."""
    
    def __init__(self, analyzer: ProductivityAnalyzer):
        self.analyzer = analyzer
    
    def generate_text_report(self) -> str:
        """Generate a comprehensive text report."""
        weekly = self.analyzer.get_weekly_summary()
        daily = self.analyzer.get_daily_stats(7)
        streak = self.analyzer.get_streak()
        
        report = []
        report.append("=" * 60)
        report.append("AI STUDY MONITOR - WEEKLY REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        report.append("📊 WEEKLY SUMMARY")
        report.append("-" * 40)
        report.append(f"  Total Study Time: {weekly['total_hours']} hours")
        report.append(f"  Pomodoros Completed: {weekly['total_pomodoros']}")
        report.append(f"  Average Focus: {weekly['average_focus']}%")
        report.append(f"  Current Streak: {streak} days 🔥")
        report.append(f"  Best Day: {weekly['best_day']}")
        report.append("")
        
        # Productivity Score
        score = self.analyzer.calculate_productivity_score()
        report.append("🏆 PRODUCTIVITY SCORE")
        report.append("-" * 40)
        report.append(f"  Score: {score:.0f}/100")
        
        if score >= 80:
            report.append("  Rating: ⭐⭐⭐⭐⭐ Excellent!")
        elif score >= 60:
            report.append("  Rating: ⭐⭐⭐⭐ Good")
        elif score >= 40:
            report.append("  Rating: ⭐⭐⭐ Average")
        else:
            report.append("  Rating: ⭐⭐ Needs improvement")
        report.append("")
        
        # Daily breakdown
        report.append("📅 DAILY BREAKDOWN")
        report.append("-" * 40)
        for day in daily:
            pomo_str = "🍅" * min(day['pomodoros'], 5)
            report.append(f"  {day['day_name']}: {day['study_hours']:.1f}h | "
                         f"Focus: {day['focus_avg']:.0f}% | {pomo_str}")
        report.append("")
        
        # Tips
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        
        if weekly['average_focus'] < 60:
            report.append("  • Your focus is below optimal. Try reducing distractions.")
        if weekly['total_hours'] < 10:
            report.append("  • Aim for more study time. Small daily sessions add up!")
        if streak < 3:
            report.append("  • Build a streak! Consistency is key to learning.")
        if weekly['average_focus'] >= 70 and weekly['total_hours'] >= 15:
            report.append("  • Great job! Keep up the excellent work!")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None) -> str:
        """Save report to file."""
        if filename is None:
            filename = f"study_report_{datetime.now().strftime('%Y%m%d')}.txt"
        
        report = self.generate_text_report()
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        return filename


class GoalTracker:
    """Tracks study goals and achievements."""
    
    GOALS_FILE = "study_goals.json"
    
    def __init__(self):
        self.goals = self._load_goals()
        self.achievements = self._load_achievements()
    
    def _load_goals(self) -> Dict:
        """Load goals from file."""
        if os.path.exists(self.GOALS_FILE):
            try:
                with open(self.GOALS_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default goals
        return {
            'daily_hours': 2.0,
            'daily_pomodoros': 4,
            'weekly_hours': 14.0,
            'focus_target': 70.0
        }
    
    def _load_achievements(self) -> List[Dict]:
        """Load achievements from file."""
        achievements_file = "achievements.json"
        if os.path.exists(achievements_file):
            try:
                with open(achievements_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def save_goals(self):
        """Save goals to file."""
        with open(self.GOALS_FILE, 'w') as f:
            json.dump(self.goals, f, indent=2)
    
    def save_achievements(self):
        """Save achievements to file."""
        with open("achievements.json", 'w') as f:
            json.dump(self.achievements, f, indent=2)
    
    def set_goal(self, goal_type: str, value: float):
        """Set a study goal."""
        self.goals[goal_type] = value
        self.save_goals()
    
    def check_achievements(self, analyzer: ProductivityAnalyzer) -> List[str]:
        """Check and award new achievements."""
        new_achievements = []
        earned_ids = [a['id'] for a in self.achievements]
        
        # Define achievement criteria
        all_achievements = [
            {
                'id': 'first_session',
                'name': '🌟 First Steps',
                'description': 'Complete your first study session',
                'check': lambda a: len(a.sessions) >= 1
            },
            {
                'id': 'pomodoro_master',
                'name': '🍅 Pomodoro Master',
                'description': 'Complete 10 pomodoros in one day',
                'check': lambda a: any(d['pomodoros'] >= 10 for d in a.get_daily_stats(7))
            },
            {
                'id': 'focus_champion',
                'name': '🎯 Focus Champion',
                'description': 'Achieve 90% focus in a session',
                'check': lambda a: any(s.get('focus_percentage', 0) >= 90 for s in a.sessions)
            },
            {
                'id': 'week_warrior',
                'name': '⚔️ Week Warrior',
                'description': 'Study for 7 consecutive days',
                'check': lambda a: a.get_streak() >= 7
            },
            {
                'id': 'marathon_studier',
                'name': '🏃 Marathon Studier',
                'description': 'Study for 4+ hours in one day',
                'check': lambda a: any(d['study_hours'] >= 4 for d in a.get_daily_stats(7))
            },
            {
                'id': 'consistency_king',
                'name': '👑 Consistency King',
                'description': 'Maintain a 14-day streak',
                'check': lambda a: a.get_streak() >= 14
            },
            {
                'id': 'hundred_hours',
                'name': '💯 Century Club',
                'description': 'Accumulate 100 total study hours',
                'check': lambda a: sum(s.get('total_study_seconds', 0) for s in a.sessions) >= 360000
            },
        ]
        
        for achievement in all_achievements:
            if achievement['id'] not in earned_ids:
                try:
                    if achievement['check'](analyzer):
                        self.achievements.append({
                            'id': achievement['id'],
                            'name': achievement['name'],
                            'description': achievement['description'],
                            'earned_date': datetime.now().isoformat()
                        })
                        new_achievements.append(achievement['name'])
                except:
                    pass
        
        if new_achievements:
            self.save_achievements()
        
        return new_achievements
    
    def get_progress(self, analyzer: ProductivityAnalyzer) -> Dict:
        """Get progress towards goals."""
        today_stats = analyzer.get_daily_stats(1)[0] if analyzer.get_daily_stats(1) else {}
        weekly_stats = analyzer.get_weekly_summary()
        
        return {
            'daily_hours': {
                'current': today_stats.get('study_hours', 0),
                'goal': self.goals['daily_hours'],
                'progress': min(today_stats.get('study_hours', 0) / self.goals['daily_hours'] * 100, 100)
            },
            'daily_pomodoros': {
                'current': today_stats.get('pomodoros', 0),
                'goal': self.goals['daily_pomodoros'],
                'progress': min(today_stats.get('pomodoros', 0) / self.goals['daily_pomodoros'] * 100, 100)
            },
            'weekly_hours': {
                'current': weekly_stats.get('total_hours', 0),
                'goal': self.goals['weekly_hours'],
                'progress': min(weekly_stats.get('total_hours', 0) / self.goals['weekly_hours'] * 100, 100)
            },
            'focus': {
                'current': today_stats.get('focus_avg', 0),
                'goal': self.goals['focus_target'],
                'progress': min(today_stats.get('focus_avg', 0) / self.goals['focus_target'] * 100, 100) if today_stats.get('focus_avg') else 0
            }
        }


def print_dashboard():
    """Print a text-based dashboard to console."""
    analyzer = ProductivityAnalyzer()
    goals = GoalTracker()
    
    print("\n" + "=" * 60)
    print("📊 STUDY DASHBOARD")
    print("=" * 60)
    
    # Weekly Summary
    weekly = analyzer.get_weekly_summary()
    print(f"\n🗓️  This Week:")
    print(f"   Study Time: {weekly['total_hours']} hours")
    print(f"   Pomodoros: {weekly['total_pomodoros']} 🍅")
    print(f"   Avg Focus: {weekly['average_focus']}%")
    print(f"   Streak: {weekly['streak']} days 🔥")
    
    # Today's Progress
    progress = goals.get_progress(analyzer)
    print(f"\n📅 Today's Progress:")
    for key, data in progress.items():
        bar = "█" * int(data['progress'] / 10) + "░" * (10 - int(data['progress'] / 10))
        print(f"   {key}: [{bar}] {data['progress']:.0f}%")
    
    # Productivity Score
    score = analyzer.calculate_productivity_score()
    print(f"\n🏆 Productivity Score: {score:.0f}/100")
    
    # Achievements
    achievements = goals.achievements
    if achievements:
        print(f"\n🎖️  Achievements ({len(achievements)}):")
        for a in achievements[-3:]:
            print(f"   {a['name']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_dashboard()
    
    # Generate charts
    analyzer = ProductivityAnalyzer()
    chart_gen = ChartGenerator()
    
    if MATPLOTLIB_AVAILABLE:
        print("\nGenerating charts...")
        chart_gen.generate_weekly_chart(analyzer)
        chart_gen.generate_focus_trend(analyzer)
        chart_gen.generate_emotion_trends(analyzer)
        print("Charts saved to 'charts/' folder")
    
    # Generate report
    reporter = ReportGenerator(analyzer)
    report_file = reporter.save_report()
    print(f"Report saved to '{report_file}'")
