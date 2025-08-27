#!/usr/bin/env python3
"""
Check API Keys - Verify which API keys are available and configured
CVPilot - Debug API key configuration
"""

import os
from pathlib import Path
from rich.console import Console

console = Console()

def check_api_keys():
    """Check all available API keys and their configuration"""

    console.print("[bold blue]🔑 API Keys Configuration Check[/bold blue]")
    console.print("=" * 50)

    # Check DataPM API keys file
    datapm_file = Path('D:/Work Work/Upwork/DataPM/csv_engine/engines/API_keys.txt')
    console.print(f"\n[cyan]1. DataPM API Keys File:[/cyan]")

    if datapm_file.exists():
        try:
            with open(datapm_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

            console.print(f"   ✅ Found {len(keys)} API keys in DataPM")
            for i, key in enumerate(keys, 1):
                key_preview = key[:20] + "..." if len(key) > 20 else key
                console.print(f"   Key {i}: {key_preview}")

            # Try to identify provider for each key
            console.print(f"\n[cyan]   Key Analysis:[/cyan]")
            for i, key in enumerate(keys, 1):
                if key.startswith('sk-'):
                    console.print(f"   Key {i}: OpenAI")
                elif key.startswith('sk-ant-'):
                    console.print(f"   Key {i}: Anthropic")
                elif len(key) > 30:  # Gemini keys are typically longer
                    console.print(f"   Key {i}: Gemini")
                else:
                    console.print(f"   Key {i}: Unknown format")

        except Exception as e:
            console.print(f"   ❌ Error reading DataPM keys: {e}")
    else:
        console.print(f"   ❌ DataPM API keys file not found at: {datapm_file}")

    # Check environment variables
    console.print(f"\n[cyan]2. Environment Variables:[/cyan]")

    env_vars = {
        'OPENAI_API_KEY': 'OpenAI',
        'ANTHROPIC_API_KEY': 'Anthropic',
        'GEMINI_API_KEYS': 'Gemini',
        'LLM_PROVIDER': 'Current Provider',
        'LLM_MODEL': 'Current Model'
    }

    for var, description in env_vars.items():
        value = os.getenv(var)
        if value:
            if var in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
                display_value = value[:20] + "..." if len(value) > 20 else value
            elif var == 'GEMINI_API_KEYS':
                keys_count = len(value.split(',')) if value else 0
                display_value = f"{keys_count} keys configured"
            else:
                display_value = value

            console.print(f"   ✅ {description}: {display_value}")
        else:
            console.print(f"   ❌ {description}: NOT SET")

    # Summary and recommendations
    console.print(f"\n[bold green]📊 SUMMARY:[/bold green]")

    recommendations = []

    # Check if any providers are configured
    has_openai = bool(os.getenv('OPENAI_API_KEY'))
    has_anthropic = bool(os.getenv('ANTHROPIC_API_KEY'))
    has_gemini = bool(os.getenv('GEMINI_API_KEYS'))

    if has_openai or has_anthropic or has_gemini:
        console.print(f"   ✅ At least one LLM provider is configured")

        if has_openai:
            recommendations.append("OpenAI (GPT) is available")
        if has_anthropic:
            recommendations.append("Anthropic (Claude) is available")
        if has_gemini:
            recommendations.append("Gemini (Google) is available")
    else:
        console.print(f"   ❌ No LLM providers configured")
        recommendations.append("Set up at least one API key (OpenAI, Anthropic, or Gemini)")

    # Check current configuration
    current_provider = os.getenv('LLM_PROVIDER')
    current_model = os.getenv('LLM_MODEL')

    if current_provider and current_model:
        console.print(f"   ✅ Current: {current_provider.upper()} - {current_model}")
    else:
        console.print(f"   ⚠️  No current LLM configuration")
        recommendations.append("Configure LLM_PROVIDER and LLM_MODEL")

    console.print(f"\n[bold cyan]💡 RECOMMENDATIONS:[/bold cyan]")
    for i, rec in enumerate(recommendations, 1):
        console.print(f"   {i}. {rec}")

    # Quick setup if needed
    if not current_provider or not current_model:
        console.print(f"\n[bold yellow]🚀 QUICK SETUP:[/bold yellow]")
        console.print(f"   Run: [green]python auto_select_llm.py[/green]")
        console.print(f"   Or:  [green]python -m src.main --job-id 159 --auto-select-llm[/green]")

if __name__ == "__main__":
    check_api_keys()
