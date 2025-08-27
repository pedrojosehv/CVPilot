#!/usr/bin/env python3
"""
Auto Select LLM - Quick script to automatically find and select the best LLM
CVPilot - One-click intelligent LLM selection
"""

from src.utils.auto_llm_selector import run_auto_selection
from rich.console import Console

console = Console()

def main():
    """Run automatic LLM selection"""

    console.print("[bold blue]🚀 CVPilot Auto LLM Selection[/bold blue]")
    console.print("[bold cyan]Finding the best available LLM for your CV generation[/bold cyan]")
    console.print("=" * 60)

    try:
        # Run automatic selection
        result = run_auto_selection(verbose=True)

        # Show next steps
        console.print("\n[bold green]🎯 NEXT STEPS:[/bold green]")
        console.print("1. [cyan]Test the selected model:[/cyan]")
        console.print("   [green]python -m src.main --job-id 159[/green]")
        console.print("")
        console.print("2. [cyan]View detailed results:[/cyan]")
        console.print("   [green]Check ./data/llm_tests/ for saved results[/green]")
        console.print("")
        console.print("3. [cyan]Run comparison anytime:[/cyan]")
        console.print("   [green]python auto_select_llm.py[/green]")

        console.print("\n[bold cyan]💡 TIP:[/bold cyan]")
        console.print("The selected model will be used automatically for all future CV generations.")

    except Exception as e:
        console.print(f"\n[bold red]❌ ERROR: {e}[/bold red]")
        console.print("\n[cyan]🔧 TROUBLESHOOTING:[/cyan]")
        console.print("1. Check that you have at least one API key configured")
        console.print("2. Verify your API keys are valid and have credits")
        console.print("3. Try running with a specific job ID:")
        console.print("   [green]python -c \"from src.utils.auto_llm_selector import AutoLLMSelector; AutoLLMSelector('159').auto_select_best_llm()\"[/green]")

if __name__ == "__main__":
    main()
