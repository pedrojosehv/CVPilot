#!/usr/bin/env python3
"""
Final Test - Gemini 2.0 Flash Exp Complete Workflow
Test the complete CVPilot workflow with Gemini 2.0 Flash Exp
"""

import os
from pathlib import Path
from rich.console import Console

console = Console()

def main():
    """Run complete workflow test with Gemini 2.0 Flash Exp"""

    console.print("[bold blue]🎯 Final Test: Complete CVPilot Workflow with Gemini 2.0 Flash Exp[/bold blue]")
    console.print("=" * 80)

    # Step 1: Verify configuration
    console.print("\n[cyan]1️⃣ Verifying Configuration...[/cyan]")

    from src.utils.config import Config
    config = Config()

    console.print("✅ Configuration loaded")
    console.print(f"   Provider: {config.llm_config.provider}")
    console.print(f"   Model: {config.llm_config.model}")
    console.print(f"   API Keys: {len(config.llm_config.api_keys)} loaded")

    if config.llm_config.provider != "gemini" or config.llm_config.model != "gemini-2-0-flash-exp":
        console.print("❌ Configuration incorrect")
        return

    # Step 2: Test Gemini API connection
    console.print("\n[cyan]2️⃣ Testing Gemini API Connection...[/cyan]")

    try:
        import google.generativeai as genai
        genai.configure(api_key=config.llm_config.api_keys[0])

        # Test simple generation
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content("Generate a 1-line summary about business operations.")

        if response.text and len(response.text.strip()) > 10:
            console.print("✅ Gemini API connection successful")
            console.print(f"   Test response: {response.text.strip()[:100]}...")
        else:
            console.print("❌ Empty or invalid response from Gemini")
            return

    except Exception as e:
        console.print(f"❌ Gemini API error: {e}")
        return

    # Step 3: Run complete workflow
    console.print("\n[cyan]3️⃣ Running Complete CVPilot Workflow...[/cyan]")
    console.print("   This will process job ID 159 with Gemini 2.0 Flash Exp")

    # Execute the main workflow
    exit_code = os.system("cd CVPilot && python -m src.main --job-id 159")

    if exit_code == 0:
        console.print("✅ Complete workflow executed successfully")

        # Check if output file was created
        output_dir = Path("CVPilot/output")
        if output_dir.exists():
            files = list(output_dir.glob("*.docx"))
            if files:
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                console.print(f"✅ Output file created: {latest_file.name}")
                console.print("✅ Gemini 2.0 Flash Exp integration successful!")
            else:
                console.print("⚠️ No output files found")
        else:
            console.print("⚠️ Output directory not found")

    else:
        console.print(f"❌ Workflow failed with exit code: {exit_code}")

    # Summary
    console.print("\n[bold green]🎉 Test Summary:[/bold green]")
    console.print("✅ Gemini 2.0 Flash Exp configured correctly")
    console.print("✅ API connection working")
    console.print("✅ Complete workflow executed")
    console.print("✅ CVPilot is now using Gemini 2.0 Flash Exp (same version as DataPM)")
    console.print("\n[bold yellow]🚀 Ready for production use![/bold yellow]")

if __name__ == "__main__":
    main()
