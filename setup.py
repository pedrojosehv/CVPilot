#!/usr/bin/env python3
"""
CVPilot Setup Script
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command: str) -> bool:
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 CVPilot Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not run_command("pip install -r requirements.txt"):
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("\n⚙️  Creating .env file...")
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            print("✓ Created .env file from template")
            print("⚠️  Please edit .env file with your API keys")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    
    # Check DataPM path
    datapm_path = Path("../../DataPM/csv/src/csv_processed")
    if datapm_path.exists():
        print(f"✓ DataPM data found at {datapm_path}")
    else:
        print(f"⚠️  DataPM data not found at {datapm_path}")
        print("   Please ensure DataPM CSV files are available")
    
    # Check for template files
    templates_path = Path("templates")
    if templates_path.exists():
        template_files = list(templates_path.glob("*.docx"))
        if template_files:
            print(f"✓ Found {len(template_files)} template file(s)")
        else:
            print("⚠️  No .docx template files found in templates/")
            print("   Please add your CV template with Jinja placeholders")
    
    print("\n✅ Setup completed!")
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Add your CV template to templates/ folder")
    print("3. Run: python src/main.py --job-id <job_id> --profile-type product_management")

if __name__ == "__main__":
    main()
