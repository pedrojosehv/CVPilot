"""
Data models for CVPilot using Pydantic
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum

class SeniorityLevel(str, Enum):
    """Seniority levels"""
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    UNKNOWN = "unknown"
    INTERN = "intern"

class ScheduleType(str, Enum):
    """Schedule types"""
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    REMOTE = "remote"
    HYBRID = "hybrid"

class JobData(BaseModel):
    """Job description data from DataPM"""
    job_id: str
    job_title_original: str
    job_title_short: str
    company: str
    country: str
    state: Optional[str] = None
    city: Optional[str] = None
    schedule_type: Optional[ScheduleType] = None
    experience_years: Optional[str] = None
    seniority: Optional[SeniorityLevel] = None
    skills: List[str] = Field(default_factory=list)
    degrees: List[str] = Field(default_factory=list)
    software: List[str] = Field(default_factory=list)
    
    @validator('skills', 'degrees', 'software', pre=True)
    def split_semicolon_fields(cls, v):
        """Split semicolon-separated fields into lists"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(';') if item.strip()]
        return v or []
    
    @validator('seniority', pre=True)
    def normalize_seniority(cls, v):
        """Normalize seniority values"""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            if v_lower in ['junior', 'jr']:
                return 'junior'
            elif v_lower in ['mid', 'middle', 'intermediate']:
                return 'mid'
            elif v_lower in ['senior', 'sr']:
                return 'senior'
            elif v_lower in ['lead']:
                return 'lead'
            elif v_lower in ['manager', 'mgr']:
                return 'manager'
            elif v_lower in ['director', 'dir']:
                return 'director'
            elif v_lower in ['intern', 'internship']:
                return 'intern'
            else:
                return 'unknown'
        return v

class ProfileType(str, Enum):
    """Profile types"""
    PRODUCT_MANAGEMENT = "product_management"
    GROWTH_PM = "growth_pm"
    DATA_PM = "data_pm"
    MOBILE_PM = "mobile_pm"
    TECHNICAL_PM = "technical_pm"
    ENTERPRISE_PM = "enterprise_pm"

class MatchResult(BaseModel):
    """Result of profile matching"""
    fit_score: float = Field(ge=0.0, le=1.0)
    gap_list: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    matched_software: List[str] = Field(default_factory=list)
    missing_software: List[str] = Field(default_factory=list)
    profile_type: ProfileType
    confidence: float = Field(ge=0.0, le=1.0)

class ReplacementBlock(BaseModel):
    """A single replacement block for the template"""
    placeholder: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Replacements(BaseModel):
    """Complete replacements for CV template"""
    profile_summary: ReplacementBlock
    top_bullets: List[ReplacementBlock]
    skill_list: ReplacementBlock
    software_list: ReplacementBlock
    objective_title: ReplacementBlock
    ats_recommendations: ReplacementBlock
    job_id: str
    company: str
    position: str
    generated_at: str
    
    @validator('top_bullets')
    def validate_top_bullets(cls, v):
        """Ensure we have 3-5 top bullets"""
        if len(v) < 3 or len(v) > 5:
            raise ValueError("Must have between 3 and 5 top bullets")
        return v

class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info

class ValidationResult(BaseModel):
    """Result of content validation"""
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationError] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)

class ProfileConfig(BaseModel):
    """Profile configuration"""
    profile_id: str
    name: str
    description: str
    skills: List[str] = Field(default_factory=list)
    software: List[str] = Field(default_factory=list)
    experience_years: Optional[str] = None
    seniority_level: Optional[SeniorityLevel] = None
    keywords: List[str] = Field(default_factory=list)
    template_placeholders: Dict[str, Any] = Field(default_factory=dict)  # Allow any type for placeholders
    
    class Config:
        extra = "allow"  # Allow additional fields

class LLMConfig(BaseModel):
    """LLM configuration"""
    provider: str = "openai"  # openai, anthropic, gemini
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: str = ""
    api_keys: Optional[List[str]] = None  # For Gemini rotation

class ProcessingResult(BaseModel):
    """Result of CV processing"""
    job_id: str
    output_file: str
    fit_score: float
    processing_time: float
    replacements: Replacements
    validation_result: ValidationResult
    success: bool
    error_message: Optional[str] = None
