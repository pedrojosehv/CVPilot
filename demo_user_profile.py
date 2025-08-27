#!/usr/bin/env python3
"""
Demo script showing the User Profile System in action
"""

from pathlib import Path
from src.utils.user_profile_manager import UserProfileManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def demo_user_profile_system():
    """Demonstrate the user profile system capabilities"""

    console.print("[bold blue]👤 CVPilot User Profile System Demo[/bold blue]")
    console.print("=" * 50)

    # Initialize the profile manager
    console.print("\n[cyan]1. Initializing User Profile Manager...[/cyan]")
    profile_manager = UserProfileManager()

    # Clear existing profile to force fresh extraction
    console.print("[cyan]1b. Clearing existing profile for fresh extraction...[/cyan]")
    from pathlib import Path
    profile_file = Path("./data/user_profiles/user_profile.json")
    if profile_file.exists():
        profile_file.unlink()
        console.print("   ✅ Cleared existing profile")

    # Reinitialize to get fresh profile
    profile_manager = UserProfileManager()

    # Show initial profile
    console.print("[cyan]2. Initial Profile State:[/cyan]")
    initial_summary = profile_manager.get_profile_summary()
    console.print(f"   • User ID: {initial_summary['contact']['name'] or 'Not set'}")
    console.print(f"   • Experience Years: {initial_summary['experience_years']}")
    console.print(f"   • Skills Count: {initial_summary['learning_stats']['skills_count']}")
    console.print(f"   • Total Interactions: {initial_summary['learning_stats']['total_interactions']}")

    # Extract from template
    console.print("\n[cyan]3. Extracting Information from CV Template...[/cyan]")
    template_path = Path("templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx")
    if template_path.exists():
        profile_manager.extract_from_cv_template(str(template_path))
        console.print("   ✅ Template processed successfully")
    else:
        console.print("   ⚠️ Template not found, skipping extraction")

    # Show updated profile
    console.print("\n[cyan]4. Profile After Template Extraction:[/cyan]")
    updated_summary = profile_manager.get_profile_summary()
    console.print(f"   • User Name: {updated_summary['contact'].get('name', 'Not extracted')}")
    console.print(f"   • Experience Years: {updated_summary['experience_years']}")
    console.print(f"   • Work Experience: {len(updated_summary.get('work_experience', []))} positions")
    console.print(f"   • Skills Count: {len(updated_summary['top_skills'])}")
    console.print(f"   • Education: {updated_summary['education_count']} entries")

    # Show top skills
    if updated_summary['top_skills']:
        console.print("\n[cyan]5. Top Skills Extracted:[/cyan]")
        table = Table(title="User Skills")
        table.add_column("Skill", style="cyan")
        table.add_column("Category", style="magenta")
        table.add_column("Proficiency", style="green")

        for skill in updated_summary['top_skills'][:10]:
            table.add_row(
                skill['name'],
                skill['category'],
                "●" * skill['proficiency_level']
            )
        console.print(table)

    # Show work experience
    work_exp = updated_summary.get('work_experience', [])
    if work_exp:
        console.print("\n[cyan]6. Work Experience Extracted:[/cyan]")
        for exp in work_exp[:3]:
            console.print(f"   • {exp['position']} at {exp['company']} ({exp['start_date']} - {exp['end_date'] or 'Present'})")

    # Show learning statistics
    console.print("\n[cyan]7. Learning System Status:[/cyan]")
    stats = updated_summary['learning_stats']
    console.print(f"   • Total Interactions: {stats['total_interactions']}")
    console.print(f"   • Successful Predictions: {stats.get('successful_predictions', 0)}")
    console.print(f"   • Avg Fit Score Improvement: {stats.get('avg_fit_score', 0):.3f}")
    console.print(f"   • Content Reuse Rate: {stats.get('content_reuse_rate', 0):.1%}")

    # Demo personalized suggestions
    console.print("\n[cyan]8. Personalized Content Suggestions:[/cyan]")
    console.print("   (This would be used during CV generation)")

    # Save the profile
    console.print("\n[cyan]9. Saving Profile...[/cyan]")
    profile_manager.save_profile()
    console.print("   ✅ Profile saved successfully")

    # Show profile benefits
    console.print("\n[green]🎯 PROFILE SYSTEM BENEFITS:[/green]")
    benefits = [
        "✅ Automatic extraction of user information from CVs",
        "✅ Persistent storage of skills, experience, and preferences",
        "✅ Personalized content generation based on user profile",
        "✅ Learning from each interaction to improve future results",
        "✅ Intelligent suggestions for skill gaps and improvements",
        "✅ Reduced need to repeat information across sessions",
        "✅ Comprehensive user history and analytics"
    ]

    for benefit in benefits:
        console.print(f"   {benefit}")

    console.print("\n[bold green]🚀 User Profile System Demo Complete![/bold green]")

if __name__ == "__main__":
    demo_user_profile_system()
