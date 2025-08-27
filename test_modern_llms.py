#!/usr/bin/env python3
"""
Test Modern LLMs - Compare quality between different modern models
CVPilot - Test GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro
"""

from pathlib import Path
from src.generation.content_generator import ContentGenerator
from src.utils.models import JobData, MatchResult, LLMConfig
from src.utils.config import Config
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

def test_modern_llms():
    """Test different modern LLM models for summary generation"""

    console.print("[bold blue]🚀 TESTING MODERN LLMs[/bold blue]")
    console.print("[bold yellow]Comparing GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro[/bold yellow]")
    console.print("=" * 70)

    # Sample job data for testing
    job_data = JobData(
        job_id="test_159",
        job_title_original="Business Operations",
        job_title_short="Business Operations",
        company="Test Company",
        country="Spain",
        skills=["SQL", "Oracle", "Python", "Excel"],
        software=["SQL Server", "Oracle", "Tableau"],
        experience_years="3-5"
    )

    # Mock match result
    match_result = MatchResult(
        matched_skills=["SQL", "Oracle", "Python"],
        fit_score=0.75,
        confidence=0.8,
        matched_keywords=["business operations", "data analysis"],
        missing_skills=["Advanced Excel"],
        recommendations=["Add more Excel experience"]
    )

    # Test configurations for different modern models
    model_configs = [
        {
            'provider': 'openai',
            'model': 'gpt-4o',
            'name': 'GPT-4o (OpenAI)',
            'description': 'Most advanced GPT-4 model with improved reasoning'
        },
        {
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet',
            'name': 'Claude 3.5 Sonnet (Anthropic)',
            'description': 'Most advanced Claude model with superior analysis'
        },
        {
            'provider': 'gemini',
            'model': 'gemini-1-5-pro',
            'name': 'Gemini 1.5 Pro (Google)',
            'description': 'Most capable Gemini model with advanced reasoning'
        }
    ]

    results = []

    for config in model_configs:
        console.print(f"\n[cyan]🧠 Testing {config['name']}[/cyan]")
        console.print(f"[dim]{config['description']}[/dim]")

        try:
            # Create LLM config for this model
            llm_config = LLMConfig(
                provider=config['provider'],
                model=config['model'],
                temperature=0.7,
                max_tokens=300
            )

            # Create content generator
            generator = ContentGenerator(
                llm_config=llm_config,
                datapm_path=Path("D:/Work Work/Upwork/DataPM"),
                templates_path=Path("templates")
            )

            # Generate summary
            replacements = generator.generate_replacements(job_data, match_result)
            summary = replacements.blocks[0].content  # ProfileSummary

            # Calculate quality score
            quality_score = generator._calculate_summary_quality(summary, job_data)

            results.append({
                'model': config['name'],
                'summary': summary,
                'quality_score': quality_score,
                'word_count': len(summary.split()),
                'characters': len(summary)
            })

            console.print("✅ Generated successfully"            console.print(f"📊 Quality Score: {quality_score:.2f}")
            console.print(f"📝 Length: {len(summary.split())} words, {len(summary)} chars")
            console.print(f"[dim]Summary: {summary[:100]}...[/dim]")

        except Exception as e:
            console.print(f"❌ Failed: {e}")
            results.append({
                'model': config['name'],
                'summary': f"Error: {e}",
                'quality_score': 0.0,
                'word_count': 0,
                'characters': 0
            })

    # Display comparison results
    console.print("
[bold green]📊 MODEL COMPARISON RESULTS[/bold green]")

    table = Table(title="Modern LLM Comparison")
    table.add_column("Model", style="cyan", width=25)
    table.add_column("Quality Score", style="green", justify="center")
    table.add_column("Word Count", style="yellow", justify="center")
    table.add_column("Characters", style="magenta", justify="center")

    for result in results:
        table.add_row(
            result['model'],
            f"{result['quality_score']:.2f}",
            str(result['word_count']),
            str(result['characters'])
        )

    console.print(table)

    # Show best performing model
    best_result = max(results, key=lambda x: x['quality_score'])
    console.print("
[bold green]🏆 BEST PERFORMING MODEL:[/bold green]")
    console.print(f"[cyan]{best_result['model']}[/cyan]")
    console.print(f"[green]Quality Score: {best_result['quality_score']:.2f}[/green]")

    # Show best summary
    console.print("
[bold green]💡 BEST SUMMARY:[/bold green]")
    panel = Panel(
        best_result['summary'],
        title=f"Best Summary from {best_result['model']}",
        border_style="green"
    )
    console.print(panel)

    # Recommendations
    console.print("
[bold blue]🎯 RECOMMENDATIONS:[/bold blue]")

    if best_result['quality_score'] >= 0.8:
        console.print("✅ Excellent quality - the modern model is working perfectly!"    elif best_result['quality_score'] >= 0.6:
        console.print("🟡 Good quality - the modern model shows improvement"    else:
        console.print("🟠 Moderate quality - may need further optimization"    # Suggest best model for production
    console.print(f"\n[cyan]💡 For production use, recommend: {best_result['model']}[/cyan]")
    console.print("[dim]Set LLM_PROVIDER and LLM_MODEL environment variables to use this model[/dim]")

if __name__ == "__main__":
    test_modern_llms()
