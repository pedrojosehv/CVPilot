"""
User Feedback System - Interactive Template Rating and Learning
CVPilot - Collects explicit user feedback on template selections
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, FloatPrompt, IntPrompt, Confirm

console = Console()

@dataclass
class FeedbackSession:
    """Represents a user feedback session"""
    session_id: str
    job_id: str
    job_title: str
    original_template: str
    selected_template: str
    timestamp: str = ""
    feedback_collected: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class TemplateRating:
    """User rating for a template"""
    template_path: str
    job_id: str
    rating: float  # 1-5 stars
    feedback_text: Optional[str] = None
    categories_rated: Dict[str, float] = None  # role_fit, skills_match, content_quality, etc.
    timestamp: str = ""
    user_id: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if self.categories_rated is None:
            self.categories_rated = {}

class UserFeedbackSystem:
    """Interactive system for collecting user feedback on template selections"""

    def __init__(self, data_dir: str = "./data/feedback"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.feedback_file = self.data_dir / "user_ratings.json"
        self.sessions_file = self.data_dir / "feedback_sessions.json"
        self.logger = logging.getLogger(__name__)

        # Load existing data
        self.ratings = self._load_ratings()
        self.sessions = self._load_sessions()

        # Feedback collection settings
        self.feedback_prompt_enabled = True
        self.min_sessions_before_prompt = 2
        self.days_between_prompts = 7

    def collect_feedback_interactive(self, job_data: Dict[str, Any],
                                   original_template: str, selected_template: str) -> Optional[TemplateRating]:
        """
        Interactively collect user feedback on template selection

        Returns:
            TemplateRating object if feedback was collected
        """
        if not self.feedback_prompt_enabled:
            return None

        job_id = str(job_data.get('job_id', ''))
        job_title = job_data.get('job_title_original', '')

        # Check if we should prompt for feedback
        if not self._should_prompt_feedback(job_id):
            return None

        console.print("\n" + "="*60)
        console.print("📊 [bold blue]Template Selection Feedback[/bold blue]")
        console.print("="*60)

        console.print(f"\n📋 Job: [cyan]{job_title}[/cyan]")
        console.print(f"🎯 Selected Template: [green]{Path(selected_template).name}[/green]")

        if original_template != selected_template:
            console.print(f"🔄 Originally suggested: [yellow]{Path(original_template).name}[/yellow]")

        # Ask if user wants to provide feedback
        provide_feedback = Confirm.ask("\n🤔 Would you like to rate this template selection?")

        if not provide_feedback:
            self._record_session(job_id, job_title, original_template, selected_template, False)
            return None

        # Collect detailed feedback
        rating = self._collect_detailed_rating(selected_template, job_id, job_title)

        if rating:
            self.ratings.append(rating)
            self._record_session(job_id, job_title, original_template, selected_template, True)
            self._save_data()

            console.print("\n[green]✅ Thank you for your feedback! It will help improve future selections.[/green]")

        return rating

    def _collect_detailed_rating(self, template_path: str, job_id: str, job_title: str) -> Optional[TemplateRating]:
        """Collect detailed rating from user"""

        console.print("\n📝 [bold]Please rate the following aspects (1-5 stars):[/bold]")

        # Overall rating
        overall_rating = self._get_star_rating("Overall suitability for this job")

        if overall_rating == 0:  # User cancelled
            return None

        # Category ratings
        categories = {
            'role_fit': 'How well does it match the job role?',
            'skills_match': 'How well do the skills align?',
            'content_quality': 'Quality of the content structure?',
            'relevance': 'Overall relevance to the job?'
        }

        category_ratings = {}
        for category, question in categories.items():
            rating = self._get_star_rating(question, required=False)
            if rating > 0:
                category_ratings[category] = rating

        # Optional feedback text
        feedback_text = Prompt.ask("\n💬 Any additional comments? (optional)")

        return TemplateRating(
            template_path=template_path,
            job_id=job_id,
            rating=overall_rating,
            feedback_text=feedback_text if feedback_text else None,
            categories_rated=category_ratings
        )

    def _get_star_rating(self, question: str, required: bool = True) -> float:
        """Get a star rating from user (1-5)"""
        while True:
            console.print(f"\n⭐ {question}")

            # Show star options
            stars = ["1 ⭐", "2 ⭐⭐", "3 ⭐⭐⭐", "4 ⭐⭐⭐⭐", "5 ⭐⭐⭐⭐⭐"]
            if not required:
                stars.append("Skip")

            choice = questionary.select(
                "Your rating:",
                choices=stars,
                default=None
            ).ask()

            if choice == "Skip":
                return 0.0
            elif choice:
                # Extract number from choice
                rating = int(choice.split()[0])
                return float(rating)
            elif not required:
                return 0.0

    def _should_prompt_feedback(self, job_id: str) -> bool:
        """Determine if we should prompt for feedback"""

        # Check minimum sessions
        if len(self.sessions) < self.min_sessions_before_prompt:
            return True

        # Check if already rated this job
        for session in self.sessions:
            if session.job_id == job_id and session.feedback_collected:
                return False

        # Check time since last feedback
        last_feedback_time = None
        for session in sorted(self.sessions, key=lambda x: x.timestamp, reverse=True):
            if session.feedback_collected:
                last_feedback_time = datetime.fromisoformat(session.timestamp)
                break

        if last_feedback_time:
            days_since = (datetime.now() - last_feedback_time).days
            if days_since < self.days_between_prompts:
                return False

        return True

    def _record_session(self, job_id: str, job_title: str, original_template: str,
                       selected_template: str, feedback_collected: bool):
        """Record a feedback session"""

        import uuid
        session = FeedbackSession(
            session_id=str(uuid.uuid4()),
            job_id=job_id,
            job_title=job_title,
            original_template=original_template,
            selected_template=selected_template,
            feedback_collected=feedback_collected
        )

        self.sessions.append(session)

    def get_feedback_statistics(self) -> Dict[str, Any]:
        """Get statistics about collected feedback"""
        if not self.ratings:
            return {'total_ratings': 0, 'avg_rating': 0, 'feedback_enabled': self.feedback_prompt_enabled}

        ratings = [r.rating for r in self.ratings]
        avg_rating = sum(ratings) / len(ratings)

        # Category averages
        category_avgs = {}
        for rating in self.ratings:
            for category, score in rating.categories_rated.items():
                if category not in category_avgs:
                    category_avgs[category] = []
                category_avgs[category].append(score)

        category_averages = {
            cat: sum(scores) / len(scores)
            for cat, scores in category_avgs.items()
        }

        return {
            'total_ratings': len(self.ratings),
            'avg_rating': round(avg_rating, 2),
            'category_averages': {k: round(v, 2) for k, v in category_averages.items()},
            'feedback_enabled': self.feedback_prompt_enabled,
            'total_sessions': len(self.sessions),
            'feedback_rate': len([s for s in self.sessions if s.feedback_collected]) / max(len(self.sessions), 1)
        }

    def show_feedback_summary(self):
        """Display a summary of collected feedback"""
        stats = self.get_feedback_statistics()

        if stats['total_ratings'] == 0:
            console.print("[yellow]No feedback collected yet.[/yellow]")
            return

        table = Table(title="📊 User Feedback Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Ratings", str(stats['total_ratings']))
        table.add_row("Average Rating", f"{stats['avg_rating']:.1f}/5 ⭐")
        table.add_row("Feedback Rate", f"{stats['feedback_rate']:.1%}")
        table.add_row("Sessions", str(stats['total_sessions']))

        console.print(table)

        if stats['category_averages']:
            console.print("\n📈 Category Ratings:")
            for category, avg in stats['category_averages'].items():
                console.print(f"  • {category.replace('_', ' ').title()}: {avg:.1f}/5")

    def get_top_rated_templates(self, limit: int = 5) -> List[Tuple[str, float, int]]:
        """
        Get top-rated templates

        Returns:
            List of (template_path, avg_rating, count) tuples
        """
        template_stats = {}

        for rating in self.ratings:
            path = rating.template_path
            if path not in template_stats:
                template_stats[path] = {'ratings': [], 'count': 0}

            template_stats[path]['ratings'].append(rating.rating)
            template_stats[path]['count'] += 1

        # Calculate averages
        results = []
        for path, stats in template_stats.items():
            avg_rating = sum(stats['ratings']) / len(stats['ratings'])
            results.append((path, avg_rating, stats['count']))

        # Sort by average rating, then by count
        results.sort(key=lambda x: (x[1], x[2]), reverse=True)

        return results[:limit]

    def toggle_feedback_prompts(self, enabled: Optional[bool] = None):
        """Toggle feedback prompts on/off"""
        if enabled is not None:
            self.feedback_prompt_enabled = enabled
        else:
            self.feedback_prompt_enabled = not self.feedback_prompt_enabled

        status = "enabled" if self.feedback_prompt_enabled else "disabled"
        console.print(f"Feedback prompts {status}")

    def _load_ratings(self) -> List[TemplateRating]:
        """Load user ratings from file"""
        if not self.feedback_file.exists():
            return []

        try:
            with open(self.feedback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [TemplateRating(**item) for item in data]
        except Exception as e:
            self.logger.error(f"Error loading ratings: {e}")
            return []

    def _load_sessions(self) -> List[FeedbackSession]:
        """Load feedback sessions from file"""
        if not self.sessions_file.exists():
            return []

        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [FeedbackSession(**item) for item in data]
        except Exception as e:
            self.logger.error(f"Error loading sessions: {e}")
            return []

    def _save_data(self):
        """Save all feedback data"""
        try:
            # Save ratings
            with open(self.feedback_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(rating) for rating in self.ratings], f, indent=2, ensure_ascii=False)

            # Save sessions
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(session) for session in self.sessions], f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving feedback data: {e}")

    def export_feedback_report(self, output_file: str = "feedback_report.json"):
        """Export a comprehensive feedback report"""
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_feedback_statistics(),
            'top_templates': [
                {
                    'template': Path(path).name,
                    'avg_rating': rating,
                    'count': count
                }
                for path, rating, count in self.get_top_rated_templates()
            ],
            'recent_feedback': [
                {
                    'template': Path(r.template_path).name,
                    'rating': r.rating,
                    'job_title': r.job_title if hasattr(r, 'job_title') else 'Unknown',
                    'timestamp': r.timestamp
                }
                for r in sorted(self.ratings, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        console.print(f"📄 Feedback report exported to {output_path}")
