#!/usr/bin/env python3
"""
Enhanced Template Selector - Complete Integration of All Future Iterations
CVPilot - Advanced template selection with ML, content analysis, fit scores, and user feedback
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import questionary
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.template_selector import TemplateSelector, TemplateCandidate
from utils.template_learning_system import TemplateLearningSystem
from utils.cv_content_analyzer import CVContentAnalyzer
from utils.fit_score_integrator import FitScoreIntegrator
from utils.user_feedback_system import UserFeedbackSystem

console = Console()

class EnhancedTemplateSelector:
    """Complete enhanced template selector with all future iterations integrated"""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)

        # Initialize all systems
        self.base_selector = TemplateSelector(output_dir)
        self.learning_system = TemplateLearningSystem()
        self.content_analyzer = CVContentAnalyzer()
        self.fit_integrator = FitScoreIntegrator()
        self.feedback_system = UserFeedbackSystem()

        # Enhanced candidate class to store additional data
        self.enhanced_candidates = []

        # Configuration
        self.enable_ml = True
        self.enable_content_analysis = True
        self.enable_fit_integration = True
        self.enable_user_feedback = True

        self.logger = logging.getLogger(__name__)

    def find_best_template_enhanced(self, job_data: Dict[str, Any], profile_type: str,
                                  interactive_feedback: bool = False) -> Optional[Tuple[str, float, str, Dict[str, Any]]]:
        """
        Find best template using all enhanced features

        Returns:
            Tuple of (template_path, score, explanation, details_dict)
        """
        console.print("\n🔬 [bold blue]Enhanced Template Selection[/bold blue]")
        console.print("=" * 60)

        # Step 1: Get base candidates
        console.print("📋 Step 1: Scanning existing templates...")
        candidates = self.base_selector._scan_existing_templates()

        if not candidates:
            console.print("[yellow]No templates found.[/yellow]")
            return None

        console.print(f"Found {len(candidates)} potential templates")

        # Step 2: Enhance candidates with additional analysis
        console.print("🧠 Step 2: Analyzing templates with enhanced features...")
        enhanced_candidates = []

        for candidate in candidates:
            enhanced = self._enhance_candidate(candidate, job_data, profile_type)
            enhanced_candidates.append(enhanced)

        # Step 3: Rank enhanced candidates
        console.print("🏆 Step 3: Ranking templates...")
        ranked_candidates = sorted(enhanced_candidates, key=lambda x: x.enhanced_score, reverse=True)

        best_candidate = ranked_candidates[0]

        # Step 4: Show analysis
        self._show_enhanced_analysis(ranked_candidates[:5], job_data)

        # Step 5: Interactive feedback (if enabled)
        if interactive_feedback and self.enable_user_feedback:
            console.print("\n🤔 Step 4: Collecting user feedback...")
            feedback = self.feedback_system.collect_feedback_interactive(
                job_data,
                best_candidate.file_path,  # Use as original for now
                best_candidate.file_path
            )

            if feedback:
                # Record the selection for learning
                self.learning_system.record_selection(
                    job_data=job_data,
                    selected_template=best_candidate.file_path,
                    auto_selected=True,
                    selection_score=best_candidate.enhanced_score,
                    user_rating=feedback.rating,
                    outcome="success"  # Assume success if rated
                )

        # Prepare return values
        details = {
            'base_score': best_candidate.score,
            'enhanced_score': best_candidate.enhanced_score,
            'ml_boost': getattr(best_candidate, 'ml_boost', 0.0),
            'content_score': getattr(best_candidate, 'content_score', 0.0),
            'fit_boost': getattr(best_candidate, 'fit_boost', 0.0),
            'insights': getattr(best_candidate, 'insights', []),
            'rank': 1,
            'total_candidates': len(candidates)
        }

        return (
            str(best_candidate.file_path),
            best_candidate.enhanced_score,
            best_candidate.enhanced_reason,
            details
        )

    def _enhance_candidate(self, candidate: TemplateCandidate, job_data: Dict[str, Any],
                          profile_type: str) -> Any:
        """Enhance a candidate with all additional analysis"""

        # Start with base score
        enhanced_score = candidate.score
        reasons = candidate.match_reasons.copy()
        insights = []

        # 1. ML Learning Boost
        if self.enable_ml:
            ml_recommendation = self.learning_system.get_ml_recommendation(job_data, [candidate])
            if ml_recommendation:
                ml_template, ml_score, ml_reason = ml_recommendation
                if ml_template == str(candidate.file_path):
                    ml_boost = (ml_score - candidate.score) * 0.3  # 30% ML influence
                    enhanced_score += ml_boost
                    reasons.append(f"ML: {ml_reason}")
                    candidate.ml_boost = ml_boost
                else:
                    candidate.ml_boost = 0.0
            else:
                candidate.ml_boost = 0.0

        # 2. Content Analysis
        if self.enable_content_analysis:
            content_analysis = self.content_analyzer.analyze_cv_content(candidate.file_path)
            if content_analysis:
                content_match = self.content_analyzer.match_content_to_job(content_analysis, job_data)
                content_score = content_match.get('content_score', 0.0)
                content_insights = content_match.get('insights', [])

                # Boost score by content analysis (20% influence)
                content_boost = (content_score - 0.5) * 0.2  # Center around neutral
                enhanced_score += content_boost

                if content_insights:
                    reasons.extend([f"Content: {insight}" for insight in content_insights])
                    insights.extend(content_insights)

                candidate.content_score = content_score
            else:
                candidate.content_score = 0.0

        # 3. Fit Score Integration
        if self.enable_fit_integration:
            fit_boost, fit_reason = self.fit_integrator.calculate_fit_score_boost(
                candidate.file_path, job_data, candidate.score
            )
            enhanced_score += fit_boost

            if fit_boost != 0:
                reasons.append(f"Fit: {fit_reason}")

            candidate.fit_boost = fit_boost

        # Store enhanced data
        candidate.enhanced_score = enhanced_score
        candidate.enhanced_reason = " | ".join(reasons)
        candidate.insights = insights

        return candidate

    def _show_enhanced_analysis(self, top_candidates: List[Any], job_data: Dict[str, Any]):
        """Show detailed analysis of top candidates"""

        table = Table(title=f"🎯 Top Template Candidates for: {job_data.get('job_title_original', '')}")
        table.add_column("Rank", style="cyan", justify="center")
        table.add_column("Template", style="green")
        table.add_column("Enhanced Score", style="magenta")
        table.add_column("Base Score", style="blue")
        table.add_column("Key Reasons", style="yellow")

        for i, candidate in enumerate(top_candidates, 1):
            template_name = Path(candidate.file_path).name
            reasons = candidate.match_reasons[:2]  # Show top 2 reasons

            table.add_row(
                str(i),
                template_name,
                f"{candidate.enhanced_score:.2f}",
                f"{candidate.score:.2f}",
                " | ".join(reasons)
            )

        console.print(table)

        # Show detailed breakdown for top candidate
        top = top_candidates[0]
        console.print(f"\n[bold green]🏆 Winner: {Path(top.file_path).name}[/bold green]")

        if hasattr(top, 'insights') and top.insights:
            console.print("\n💡 Content Insights:")
            for insight in top.insights:
                console.print(f"  • {insight}")

        # Show performance data if available
        perf = self.fit_integrator.get_template_success_rate(top.file_path)
        if perf[1] > 0:  # If template has been used
            success_rate, total_uses = perf
            console.print(f"\n📊 Performance: {success_rate:.1%} success rate ({total_uses} uses)")

    def show_system_status(self):
        """Show status of all enhanced systems"""

        console.print("\n🔧 [bold]Enhanced Template Selector Status[/bold]")
        console.print("=" * 50)

        # Learning system stats
        learning_stats = self.learning_system.get_statistics()
        console.print(f"🧠 ML Learning: {'✅ Active' if learning_stats['learning_active'] else '⏳ Learning'}")
        console.print(f"   Selections recorded: {learning_stats['total_selections']}")
        console.print(f"   Templates with ratings: {learning_stats['templates_with_ratings']}")
        if learning_stats['average_rating'] > 0:
            console.print(f"   Average rating: {learning_stats['average_rating']:.1f}/5")

        # Content analyzer
        console.print(f"\n📄 Content Analysis: {'✅ Enabled' if self.enable_content_analysis else '❌ Disabled'}")

        # Fit integrator
        console.print(f"📊 Fit Score Integration: {'✅ Enabled' if self.enable_fit_integration else '❌ Disabled'}")

        # User feedback
        feedback_stats = self.feedback_system.get_feedback_statistics()
        console.print(f"🤔 User Feedback: {'✅ Active' if feedback_stats['feedback_enabled'] else '❌ Disabled'}")
        console.print(f"   Ratings collected: {feedback_stats['total_ratings']}")
        console.print(f"   Feedback rate: {feedback_stats['feedback_rate']:.1%}")

        console.print(f"\n📁 Templates available: {len(list(self.output_dir.glob('**/*.docx')))}")

    def export_comprehensive_report(self, output_file: str = "enhanced_selector_report.json"):
        """Export comprehensive report of all systems"""

        report = {
            'generated_at': datetime.now().isoformat(),
            'systems_status': {
                'ml_learning': self.learning_system.get_statistics(),
                'user_feedback': self.feedback_system.get_feedback_statistics(),
                'template_performance': self.fit_integrator.template_performance
            },
            'top_rated_templates': [
                {
                    'template': Path(path).name,
                    'avg_rating': rating,
                    'count': count
                }
                for path, rating, count in self.feedback_system.get_top_rated_templates()
            ]
        }

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)

        console.print(f"\n📄 Comprehensive report exported to {output_path}")

    def toggle_system(self, system_name: str, enabled: Optional[bool] = None):
        """Toggle individual systems on/off"""

        systems = {
            'ml': 'enable_ml',
            'content': 'enable_content_analysis',
            'fit': 'enable_fit_integration',
            'feedback': 'enable_user_feedback'
        }

        if system_name not in systems:
            console.print(f"[red]Unknown system: {system_name}[/red]")
            return

        attr_name = systems[system_name]
        current_value = getattr(self, attr_name)

        if enabled is not None:
            new_value = enabled
        else:
            new_value = not current_value

        setattr(self, attr_name, new_value)
        status = "enabled" if new_value else "disabled"
        console.print(f"✅ {system_name.upper()} system {status}")

def interactive_enhanced_selector():
    """Interactive interface for the enhanced template selector"""

    selector = EnhancedTemplateSelector()

    while True:
        console.print("\n🚀 [bold cyan]Enhanced Template Selector[/bold cyan]")
        console.print("=" * 40)

        choices = [
            "🔍 Find best template for a job",
            "📊 Show system status",
            "⚙️  Configure systems",
            "📄 Export comprehensive report",
            "🧪 Test with sample job",
            "❌ Exit"
        ]

        choice = questionary.select(
            "What would you like to do?",
            choices=choices
        ).ask()

        if choice == "❌ Exit":
            break

        elif choice == "📊 Show system status":
            selector.show_system_status()

        elif choice == "⚙️  Configure systems":
            configure_systems_interactive(selector)

        elif choice == "📄 Export comprehensive report":
            selector.export_comprehensive_report()

        elif choice == "🧪 Test with sample job":
            test_with_sample_job(selector)

        elif choice == "🔍 Find best template for a job":
            find_template_interactive(selector)

def configure_systems_interactive(selector: EnhancedTemplateSelector):
    """Interactive system configuration"""

    console.print("\n⚙️ [bold]System Configuration[/bold]")

    systems = [
        ("ml", "Machine Learning"),
        ("content", "Content Analysis"),
        ("fit", "Fit Score Integration"),
        ("feedback", "User Feedback")
    ]

    for system_key, system_name in systems:
        current_status = getattr(selector, f"enable_{system_key}")
        status_emoji = "✅" if current_status else "❌"

        toggle = questionary.confirm(f"{status_emoji} {system_name} - Toggle?")
        if toggle:
            selector.toggle_system(system_key)

def test_with_sample_job(selector: EnhancedTemplateSelector):
    """Test with a sample job"""

    sample_jobs = [
        {
            'job_id': 'sample_1',
            'job_title_original': 'Senior Product Analyst - Data Analytics',
            'skills': ['Python', 'SQL', 'Tableau', 'Google Analytics'],
            'software': ['Excel', 'Power BI', 'R'],
            'company': 'TechCorp'
        },
        {
            'job_id': 'sample_2',
            'job_title_original': 'Product Manager - Growth',
            'skills': ['Product Strategy', 'Analytics', 'A/B Testing'],
            'software': ['Google Analytics', 'Mixpanel', 'Tableau'],
            'company': 'GrowthCo'
        }
    ]

    console.print("\n🧪 [bold]Testing with Sample Jobs[/bold]")

    for i, job_data in enumerate(sample_jobs, 1):
        console.print(f"\n📋 Sample Job {i}: {job_data['job_title_original']}")

        result = selector.find_best_template_enhanced(
            job_data,
            'product_management',
            interactive_feedback=False
        )

        if result:
            template_path, score, explanation, details = result
            console.print(f"✅ Selected: {Path(template_path).name}")
            console.print(f"   Score: {score:.2f}")
            console.print(f"   Details: {details}")

        input("\nPress Enter to continue...")

def find_template_interactive(selector: EnhancedTemplateSelector):
    """Interactive template finding"""

    console.print("\n🔍 [bold]Find Best Template[/bold]")

    job_title = questionary.text("Enter job title:").ask()
    if not job_title:
        return

    skills_input = questionary.text("Enter skills (comma-separated, optional):").ask()
    skills = [s.strip() for s in skills_input.split(',')] if skills_input else []

    software_input = questionary.text("Enter software/tools (comma-separated, optional):").ask()
    software = [s.strip() for s in software_input.split(',')] if software_input else []

    job_data = {
        'job_id': f'interactive_{int(datetime.now().timestamp())}',
        'job_title_original': job_title,
        'skills': skills,
        'software': software,
        'company': 'Interactive Test'
    }

    result = selector.find_best_template_enhanced(
        job_data,
        'product_management',
        interactive_feedback=True
    )

    if result:
        template_path, score, explanation, details = result
        console.print("
[green]🎯 Template found![/green]"        console.print(f"   File: {Path(template_path).name}")
        console.print(f"   Score: {score:.2f}")
        console.print(f"   Reason: {explanation}")

if __name__ == "__main__":
    interactive_enhanced_selector()
