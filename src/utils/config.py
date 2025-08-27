"""
Configuration management for CVPilot
"""

import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from rich.console import Console

console = Console()

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "gemini"  # openai, anthropic, gemini
    model: str = "gemini-2-0-flash-exp"  # Fast and available Gemini model (same version as DataPM)
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: str = ""
    api_keys: list[str] = None  # For Gemini rotation

@dataclass
class Config:
    """Main configuration class"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Base paths
        self.base_path = Path(__file__).parent.parent.parent
        self.data_path = self.base_path / "data"
        self.templates_path = self.base_path / "templates"
        self.profiles_path = self.base_path / "profiles"
        self.logs_path = self.base_path / "logs"
        self.backups_path = self.base_path / "backups"
        self.manual_exports_path = self.base_path / "manual_exports"
        
        # Default template
        self.default_template_path = self.templates_path / "PedroHerrera_PA_SaaS_B2B_Remote_2025.docx"
        self.cover_letter_template_path = self.templates_path / "cover_letter.txt"
        
        # LLM configuration - Auto-detect available APIs
        gemini_keys = os.getenv("GEMINI_API_KEYS", "")
        if not gemini_keys:
            # Try to load from DataPM API_keys.txt (user's primary key storage)
            datapm_api_file = Path("D:/Work Work/Upwork/DataPM/csv_engine/engines/API_keys.txt")
            if datapm_api_file.exists():
                try:
                    with open(datapm_api_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        keys = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
                        if keys:
                            gemini_keys = ",".join(keys)
                            console.print(f"[green]✅ Loaded {len(keys)} Gemini API keys from DataPM[/green]")
                except Exception as e:
                    console.print(f"[yellow]⚠️ Could not load DataPM API keys: {e}[/yellow]")

        api_keys = gemini_keys.split(",") if gemini_keys else []

        # Auto-select provider based on available keys
        default_provider = "gemini" if gemini_keys else os.getenv("LLM_PROVIDER", "openai")
        default_model = "gemini-2-0-flash-exp" if gemini_keys else os.getenv("LLM_MODEL", "gpt-4o")

        self.llm_config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", default_provider),
            model=os.getenv("LLM_MODEL", default_model),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY", ""),
            api_keys=api_keys
        )

        # Log modern model configuration
        console.print(f"[blue]🤖 Using modern LLM: {self.llm_config.provider.upper()} - {self.llm_config.model}[/blue]")
        
        # DataPM paths
        self.datapm_path = Path("D:/Work Work/Upwork/DataPM")
        
        # Validation settings
        self.max_summary_length = 450  # Maximum 450 characters for summary (strict limit - no truncation)
        self.max_bullet_length = 150
        self.max_skills_count = 15
        self.max_software_count = 10
        
        # Forbidden tokens
        self.forbidden_tokens = [
            "confidential", "secret", "internal", "proprietary",
            "draft", "template", "placeholder", "example"
        ]
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.data_path,
            self.templates_path,
            self.profiles_path,
            self.logs_path,
            self.backups_path,
            self.manual_exports_path
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
    
    def get_datapm_files(self) -> list[Path]:
        """Get list of DataPM CSV files"""
        if self.datapm_path.exists():
            return list(self.datapm_path.glob("*.csv"))
        return []
    
    def get_template_files(self) -> list[Path]:
        """Get list of template files"""
        return list(self.templates_path.glob("*.docx"))
    
    def get_profile_files(self) -> list[Path]:
        """Get list of profile files"""
        return list(self.profiles_path.glob("*.json"))
