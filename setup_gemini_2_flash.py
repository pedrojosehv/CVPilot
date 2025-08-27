#!/usr/bin/env python3
"""
Setup Gemini 2.0 Flash - Configure CVPilot to use Gemini 2.0 Flash as the default LLM
CVPilot - Quick setup for the fastest and most modern Gemini model
"""

import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()

def setup_gemini_1_5_flash():
    """Setup Gemini 1.5 Flash as the default LLM for CVPilot"""

    console.print("[bold blue]🚀 Setting up Gemini 1.5 Flash for CVPilot[/bold blue]")
    console.print("[bold cyan]Configuring the fast and modern Gemini model[/bold cyan]")
    console.print("=" * 60)

    # Check if DataPM API keys exist
    datapm_api_file = Path("D:/Work Work/Upwork/DataPM/csv_engine/engines/API_keys.txt")
    gemini_keys_found = False

    if datapm_api_file.exists():
        try:
            with open(datapm_api_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
                if keys:
                    gemini_keys_found = True
                    console.print(f"[green]✅ Found {len(keys)} Gemini API keys in DataPM[/green]")
        except Exception as e:
            console.print(f"[red]❌ Error reading DataPM API keys: {e}[/red]")
            return

    if not gemini_keys_found:
        console.print("[red]❌ No Gemini API keys found in DataPM[/red]")
        console.print("[cyan]Please ensure your Gemini API keys are in:[/cyan]")
        console.print("[yellow]D:/Work Work/Upwork/DataPM/csv_engine/engines/API_keys.txt[/yellow]")
        return

    # Set environment variables
    console.print("\n[cyan]🔧 Configuring environment variables...[/cyan]")

    os.environ["LLM_PROVIDER"] = "gemini"
    os.environ["LLM_MODEL"] = "gemini-2-0-flash-exp"

    console.print("[green]✅ LLM_PROVIDER=gemini[/green]")
    console.print("[green]✅ LLM_MODEL=gemini-2-0-flash-exp[/green]")

    # Create or update .env file
    env_file = Path(".env")
    env_content = ""

    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()

    # Update or add LLM configuration
    lines = env_content.split('\n')
    updated_lines = []
    llm_provider_found = False
    llm_model_found = False

    for line in lines:
        if line.startswith('LLM_PROVIDER='):
            updated_lines.append('LLM_PROVIDER=gemini')
            llm_provider_found = True
        elif line.startswith('LLM_MODEL='):
            updated_lines.append('LLM_MODEL=gemini-2-0-flash-exp')
            llm_model_found = True
        else:
            updated_lines.append(line)

    # Add if not found
    if not llm_provider_found:
        updated_lines.append('LLM_PROVIDER=gemini')
    if not llm_model_found:
        updated_lines.append('LLM_MODEL=gemini-2-0-flash-exp')

    # Write back to .env file
    with open(env_file, 'w') as f:
        f.write('\n'.join(updated_lines))

    console.print(f"[green]✅ Updated .env file: {env_file}[/green]")

    # Show configuration summary
    console.print("\n[bold green]🎉 Gemini 1.5 Flash Setup Complete![/bold green]")

    summary_panel = Panel(
        "[bold green]✅ Configuration Summary:[/bold green]\n\n"
        "• [cyan]Provider:[/cyan] Gemini\n"
        "• [cyan]Model:[/cyan] gemini-1.5-flash (1.5 Flash)\n"
        "• [cyan]API Keys:[/cyan] Loaded from DataPM\n"
        "• [cyan]Status:[/cyan] Ready to use\n\n"
        "[bold yellow]🚀 Next Steps:[/bold yellow]\n\n"
        "1. Test the configuration:\n"
        "   [green]python -m src.main --job-id 159[/green]\n\n"
        "2. Run auto-selection anytime:\n"
        "   [green]python auto_select_llm.py[/green]\n\n"
        "3. Switch models if needed:\n"
        "   [green]python switch_llm_model.py[/green]",
        title="Gemini 1.5 Flash Configuration",
        border_style="green"
    )

    console.print(summary_panel)

    # Test the configuration
    console.print("\n[cyan]🧪 Testing configuration...[/cyan]")
    try:
        from src.utils.config import Config
        import os
        config = Config()

        if config.llm_config.provider == "gemini" and config.llm_config.model == "gemini-2-0-flash-exp":
            console.print("[green]✅ Configuration test passed![/green]")
        else:
            console.print(f"[yellow]⚠️ Configuration loaded: {config.llm_config.provider} - {config.llm_config.model}[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Configuration test failed: {e}[/red]")

if __name__ == "__main__":
    setup_gemini_1_5_flash()
