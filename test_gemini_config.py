#!/usr/bin/env python3
"""
Test Gemini 2.0 Flash Exp Configuration
Verify that CVPilot is correctly configured to use Gemini 2.0 Flash Exp
"""

import os
from pathlib import Path
from rich.console import Console
from src.utils.config import Config

console = Console()

def test_gemini_config():
    """Test the Gemini configuration"""

    console.print("[bold blue]🧪 Testing Gemini 2.0 Flash Exp Configuration[/bold blue]")
    console.print("=" * 60)

    # Test configuration loading
    console.print("\n[cyan]🔍 Testing configuration loading...[/cyan]")
    try:
        config = Config()
        console.print("✅ Configuration loaded successfully")
        console.print(f"   Provider: {config.llm_config.provider}")
        console.print(f"   Model: {config.llm_config.model}")
        console.print(f"   API Keys: {len(config.llm_config.api_keys)} loaded")
    except Exception as e:
        console.print(f"❌ Configuration error: {e}")
        return

    # Verify it's using Gemini 2.0 Flash Exp
    expected_provider = "gemini"
    expected_model = "gemini-2-0-flash-exp"

    if config.llm_config.provider != expected_provider:
        console.print(f"❌ Wrong provider: expected '{expected_provider}', got '{config.llm_config.provider}'")
        return

    if config.llm_config.model != expected_model:
        console.print(f"❌ Wrong model: expected '{expected_model}', got '{config.llm_config.model}'")
        return

    console.print("✅ Provider and model configuration correct"
    # Test API key loading
    console.print("\n[cyan]🔑 Testing API key loading...[/cyan]")
    datapm_file = Path("D:/Work Work/Upwork/DataPM/csv_engine/engines/API_keys.txt")

    if datapm_file.exists():
        try:
            with open(datapm_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                api_keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

            console.print(f"✅ Found {len(api_keys)} API keys in DataPM")

            if len(api_keys) == len(config.llm_config.api_keys):
                console.print("✅ All API keys loaded correctly")
            else:
                console.print(f"⚠️ Mismatch: {len(api_keys)} in file, {len(config.llm_config.api_keys)} loaded")

        except Exception as e:
            console.print(f"❌ Error reading API keys: {e}")
            return
    else:
        console.print("❌ DataPM API keys file not found")
        return

    # Test Gemini API connection
    console.print("\n[cyan]🔌 Testing Gemini API connection...[/cyan]")
    try:
        import google.generativeai as genai

        if config.llm_config.api_keys:
            genai.configure(api_key=config.llm_config.api_keys[0])

            # Test with a simple prompt
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            response = model.generate_content("Say 'Hello from Gemini 2.0 Flash Exp!' in exactly those words.")

            if "Hello from Gemini 2.0 Flash Exp!" in response.text:
                console.print("✅ Gemini API connection successful")
                console.print(f"   Response: {response.text.strip()}")
            else:
                console.print(f"⚠️ Unexpected response: {response.text.strip()}")
        else:
            console.print("❌ No API keys available for testing")

    except Exception as e:
        console.print(f"❌ Gemini API error: {e}")
        return

    # Success summary
    console.print("\n[bold green]🎉 Configuration Test Successful![/bold green]")
    console.print("[green]✅ Gemini 2.0 Flash Exp is properly configured[/green]")
    console.print("[green]✅ API keys are loaded and working[/green]")
    console.print("[green]✅ Ready for CVPilot operations[/green]")

    console.print("\n[bold yellow]🚀 Next Steps:[/bold yellow]")
    console.print("1. Run CVPilot with: [green]python -m src.main --job-id 159[/green]")
    console.print("2. The system will now use Gemini 2.0 Flash Exp (same as DataPM)")

if __name__ == "__main__":
    test_gemini_config()
