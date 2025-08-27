"""
Configuration management for CVPilot
"""

import os
from pathlib import Path
from typing import Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "openai"  # openai, anthropic, gemini
    model: str = "gpt-4"
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
        
        # LLM configuration
        gemini_keys = os.getenv("GEMINI_API_KEYS", "")
        api_keys = gemini_keys.split(",") if gemini_keys else []
        
        self.llm_config = LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "openai"),
            model=os.getenv("LLM_MODEL", "gpt-4"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            api_key=os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY", ""),
            api_keys=api_keys
        )
        
        # DataPM paths
        self.datapm_path = Path("D:/Work Work/Upwork/DataPM")
        
        # Validation settings
        self.max_summary_length = 200
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
