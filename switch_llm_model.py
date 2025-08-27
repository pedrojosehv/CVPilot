#!/usr/bin/env python3
"""
Switch LLM Model - Easily change between modern LLM models
CVPilot - Quick utility to switch between GPT-4o, Claude 3.5 Sonnet, and Gemini 1.5 Pro
"""

import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from src.utils.model_selector import ModelSelector, setup_environment_for_model

console = Console()

def switch_llm_model():
    """Interactive utility to switch between modern LLM models"""

    console.print("[bold blue]🔄 LLM Model Switcher[/bold blue]")
    console.print("[bold yellow]Switch between modern AI models for better CV generation[/bold yellow]")
    console.print("=" * 60)

    # Initialize model selector
    selector = ModelSelector()

    # Show current configuration
    current_provider = os.getenv("LLM_PROVIDER", "openai")
    current_model = os.getenv("LLM_MODEL", "gpt-4o")

    console.print(f"\n[cyan]📊 Current Configuration:[/cyan]")
    console.print(f"   Provider: {current_provider.upper()}")
    console.print(f"   Model: {current_model}")

    # Show available models
    console.print(f"\n[cyan]🤖 Available Modern Models:[/cyan]")
    selector.list_available_models()

    # Quick recommendations
    console.print(f"\n[cyan]💡 Quick Recommendations:[/cyan]")
    console.print(f"   [green]🎯 Best Quality:[/green] {selector.recommend_model('quality').display_name}")
    console.print(f"   [yellow]⚡ Best Speed:[/yellow] {selector.recommend_model('speed').display_name}")
    console.print(f"   [blue]💰 Best Cost:[/blue] {selector.recommend_model('cost').display_name}")

    # Interactive selection
    console.print(f"\n[bold cyan]🎮 Choose your model:[/bold cyan]")
    console.print("1. Best Quality (GPT-4o)"    console.print("2. Best Speed (Gemini 1.5 Flash)"    console.print("3. Best Cost (Gemini 1.5 Flash)"    console.print("4. Claude 3.5 Sonnet (Balanced)"    console.print("5. Custom Selection"    console.print("6. Keep Current"    console.print()

    choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5", "6"], default="1")

    if choice == "6":
        console.print("[green]✅ Keeping current configuration[/green]")
        return

    # Select model based on choice
    if choice == "1":
        model = selector.recommend_model("quality")
        console.print(f"[green]🎯 Selected: Best Quality ({model.display_name})[/green]")
    elif choice == "2":
        model = selector.recommend_model("speed")
        console.print(f"[green]⚡ Selected: Best Speed ({model.display_name})[/green]")
    elif choice == "3":
        model = selector.recommend_model("cost")
        console.print(f"[green]💰 Selected: Best Cost ({model.display_name})[/green]")
    elif choice == "4":
        model = selector.models['claude-3-5-sonnet']
        console.print(f"[green]🧠 Selected: Claude 3.5 Sonnet[/green]")
    else:
        # Custom selection
        model = selector.interactive_selection()
        if not model:
            return

    # Confirm selection
    console.print(f"\n[bold cyan]🔧 Configuration Preview:[/bold cyan]")
    console.print(f"   LLM_PROVIDER={model.provider}")
    console.print(f"   LLM_MODEL={model.model}")
    console.print(f"   Model: {model.display_name}")
    console.print(f"   Description: {model.description}")

    # Update environment variables
    if Confirm.ask(f"\n🤔 Apply this configuration now?"):
        # Set environment variables
        os.environ["LLM_PROVIDER"] = model.provider
        os.environ["LLM_MODEL"] = model.model

        console.print("[green]✅ Environment variables updated![/green]")
        console.print("[cyan]💡 For permanent changes, add to your .env file:[/cyan]")
        setup_environment_for_model(model)

        console.print("
[bold green]🎉 Ready to test![/bold green]")
        console.print("Run: [cyan]python -m src.main --job-id 159[/cyan]")

        # Offer to test immediately
        if Confirm.ask("🚀 Test with job ID 159 now?"):
            console.print("[blue]Running test...[/blue]")
            os.system("python -m src.main --job-id 159")

    else:
        console.print("[yellow]ℹ️ Configuration not applied[/yellow]")

def show_model_comparison():
    """Show detailed comparison between modern models"""

    console.print("[bold blue]📊 Modern LLM Model Comparison[/bold blue]")
    console.print("=" * 50)

    models = {
        'GPT-4o': {
            'provider': 'OpenAI',
            'quality': '⭐⭐⭐⭐⭐ (95%)',
            'speed': '⭐⭐⭐⭐ (80%)',
            'cost': '⭐⭐⭐⭐ (70%)',
            'best_for': 'Maximum quality, complex analysis'
        },
        'Claude 3.5 Sonnet': {
            'provider': 'Anthropic',
            'quality': '⭐⭐⭐⭐⭐ (92%)',
            'speed': '⭐⭐⭐⭐⭐ (85%)',
            'cost': '⭐⭐⭐⭐⭐ (80%)',
            'best_for': 'Creative writing, detailed analysis'
        },
        'Gemini 1.5 Pro': {
            'provider': 'Google',
            'quality': '⭐⭐⭐⭐ (88%)',
            'speed': '⭐⭐⭐⭐⭐ (90%)',
            'cost': '⭐⭐⭐⭐⭐ (90%)',
            'best_for': 'Fast processing, good balance'
        },
        'Gemini 1.5 Flash': {
            'provider': 'Google',
            'quality': '⭐⭐⭐⭐ (82%)',
            'speed': '⭐⭐⭐⭐⭐ (95%)',
            'cost': '⭐⭐⭐⭐⭐ (95%)',
            'best_for': 'High volume, cost-effective'
        }
    }

    from rich.table import Table

    table = Table(title="Modern LLM Comparison")
    table.add_column("Model", style="cyan", width=20)
    table.add_column("Provider", style="magenta", width=12)
    table.add_column("Quality", style="green", width=15)
    table.add_column("Speed", style="yellow", width=12)
    table.add_column("Cost", style="blue", width=12)
    table.add_column("Best For", style="white", width=25)

    for model_name, specs in models.items():
        table.add_row(
            model_name,
            specs['provider'],
            specs['quality'],
            specs['speed'],
            specs['cost'],
            specs['best_for']
        )

    console.print(table)

    console.print("\n[bold cyan]🎯 Recommendations:[/bold cyan]")
    console.print("   [green]🎯 Maximum Quality → GPT-4o or Claude 3.5 Sonnet[/green]")
    console.print("   [yellow]⚡ Maximum Speed → Gemini 1.5 Flash[/yellow]")
    console.print("   [blue]💰 Cost Effective → Gemini models[/blue]")
    console.print("   [purple]🧠 Balanced → Claude 3.5 Sonnet[/purple]")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        show_model_comparison()
    else:
        switch_llm_model()
