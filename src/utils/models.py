"""
Data models for CVPilot using Pydantic
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime

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
    """LLM configuration with modern model support"""
    provider: str = "gemini"  # openai, anthropic, gemini
    model: str = "gemini-2-0-flash-exp"  # Gemini 2.0 Flash Exp (same as DataPM)
    temperature: float = 0.7
    max_tokens: int = 2000
    api_key: str = ""
    api_keys: Optional[List[str]] = None  # For Gemini rotation

    # Modern model mappings
    @property
    def modern_models(self) -> dict:
        """Get modern model names for each provider"""
        return {
            'openai': {
                'gpt-4o': 'gpt-4o',           # Most advanced GPT-4 model
                'gpt-4-turbo': 'gpt-4-turbo-preview',  # Previous most advanced
                'gpt-4': 'gpt-4'              # Standard GPT-4
            },
            'anthropic': {
                'claude-3-5-sonnet': 'claude-3-5-sonnet-20241022',  # Most advanced
                'claude-3-opus': 'claude-3-opus-20240229',          # Previous best
                'claude-3-haiku': 'claude-3-haiku-20240307'         # Fast and efficient
            },
            'gemini': {
                'gemini-2-0-flash-exp': 'gemini-2.0-flash-exp',  # Most modern and fastest
                'gemini-1-5-pro': 'gemini-1.5-pro',      # Most capable
                'gemini-1-5-flash': 'gemini-1.5-flash',  # Fast and efficient
                'gemini-pro': 'gemini-pro'               # Previous generation
            }
        }

    def get_model_name(self) -> str:
        """Get the actual model name for API calls"""
        models = self.modern_models.get(self.provider, {})
        return models.get(self.model, self.model)

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


# ============================================================================
# USER PROFILE SYSTEM - Comprehensive User Data Management
# ============================================================================

class UserContact(BaseModel):
    """User contact information"""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None


class WorkExperience(BaseModel):
    """Individual work experience entry"""
    company: str
    position: str
    start_date: str  # Format: MM/YYYY
    end_date: Optional[str] = None  # None for current position
    location: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    is_current: bool = False
    industry: Optional[str] = None


class Education(BaseModel):
    """Education entry"""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_date: Optional[str] = None  # Format: MM/YYYY
    gpa: Optional[str] = None
    honors: List[str] = Field(default_factory=list)


class SkillProficiency(BaseModel):
    """Skill with proficiency level"""
    name: str
    category: str  # 'technical', 'soft', 'domain', 'tool'
    proficiency_level: int = Field(..., ge=1, le=5)  # 1-5 scale
    years_experience: Optional[int] = None
    last_used: Optional[str] = None  # ISO date string
    confidence_score: float = 1.0  # Based on usage and validation


class IndustryPreference(BaseModel):
    """User preference for specific industries"""
    industry_name: str
    interest_level: int = Field(..., ge=1, le=5)  # 1-5 scale
    experience_years: int = 0
    preferred_roles: List[str] = Field(default_factory=list)


class WritingStyle(BaseModel):
    """User's preferred writing style"""
    tone: str = "professional"  # 'professional', 'technical', 'conversational', 'executive'
    detail_level: str = "concise"  # 'brief', 'concise', 'detailed', 'comprehensive'
    language_complexity: str = "intermediate"  # 'simple', 'intermediate', 'advanced'
    include_metrics: bool = True
    avoid_generic_phrases: bool = True
    preferred_industries: List[str] = Field(default_factory=list)


class UserPreferences(BaseModel):
    """User preferences and settings"""
    writing_style: WritingStyle = Field(default_factory=WritingStyle)
    preferred_template_formats: List[str] = Field(default_factory=lambda: ["modern", "professional"])
    industries_of_interest: List[str] = Field(default_factory=list)
    role_progression_goals: List[str] = Field(default_factory=list)
    salary_expectations: Optional[str] = None
    remote_work_preference: str = "flexible"  # 'remote', 'onsite', 'hybrid', 'flexible'
    travel_willingness: str = "moderate"  # 'none', 'minimal', 'moderate', 'extensive'


class InteractionHistory(BaseModel):
    """Record of user interactions for learning"""
    interaction_id: str
    timestamp: str
    interaction_type: str  # 'cv_generation', 'feedback', 'template_selection', 'content_edit'
    job_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    outcome: str = "unknown"  # 'success', 'modified', 'rejected', 'error'
    user_feedback: Optional[str] = None
    processing_time: Optional[float] = None


class LearningMetrics(BaseModel):
    """Metrics for measuring system learning effectiveness"""
    total_interactions: int = 0
    successful_predictions: int = 0
    user_satisfaction_score: float = 0.0
    average_processing_time: float = 0.0
    template_success_rate: Dict[str, float] = Field(default_factory=dict)
    content_reuse_rate: float = 0.0
    average_fit_score_improvement: float = 0.0


class UserProfile(BaseModel):
    """Comprehensive user profile consolidating all user data"""
    user_id: str = Field(default_factory=lambda: f"user_{int(datetime.now().timestamp())}")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    # Personal Information
    contact: UserContact = Field(default_factory=UserContact)

    # Professional Data
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    skills: List[SkillProficiency] = Field(default_factory=list)

    # Preferences & Style
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    # Industry Knowledge
    industry_preferences: List[IndustryPreference] = Field(default_factory=list)

    # Learning & History
    interaction_history: List[InteractionHistory] = Field(default_factory=list)
    learning_metrics: LearningMetrics = Field(default_factory=LearningMetrics)

    # System Integration
    template_learning_enabled: bool = True
    auto_extract_from_cvs: bool = True
    feedback_collection_enabled: bool = True

    def update_timestamp(self):
        """Update the last modified timestamp"""
        self.updated_at = datetime.now().isoformat()

    def add_work_experience(self, experience: WorkExperience):
        """Add work experience and update profile"""
        self.work_experience.append(experience)
        self.update_timestamp()

    def add_skill(self, skill: SkillProficiency):
        """Add or update skill proficiency"""
        # Remove existing skill with same name if exists
        self.skills = [s for s in self.skills if s.name != skill.name]
        self.skills.append(skill)
        self.update_timestamp()

    def add_interaction(self, interaction: InteractionHistory):
        """Add interaction to history"""
        self.interaction_history.append(interaction)
        self.update_timestamp()

    def get_top_skills(self, limit: int = 10, category: Optional[str] = None) -> List[SkillProficiency]:
        """Get top skills by proficiency, optionally filtered by category"""
        skills = self.skills
        if category:
            skills = [s for s in skills if s.category == category]

        return sorted(skills, key=lambda s: s.proficiency_level, reverse=True)[:limit]

    def get_recent_experience(self, years: int = 5) -> List[WorkExperience]:
        """Get recent work experience within specified years"""
        current_year = datetime.now().year
        recent_exp = []

        for exp in self.work_experience:
            start_year = int(exp.start_date.split('/')[-1]) if '/' in exp.start_date else current_year
            if current_year - start_year <= years:
                recent_exp.append(exp)

        return sorted(recent_exp, key=lambda e: e.start_date, reverse=True)

    def get_industry_experience(self, industry: str) -> List[WorkExperience]:
        """Get work experience in specific industry"""
        return [exp for exp in self.work_experience if exp.industry and industry.lower() in exp.industry.lower()]

    def calculate_experience_years(self) -> float:
        """Calculate total years of professional experience"""
        total_months = 0
        current_date = datetime.now()

        for exp in self.work_experience:
            try:
                start_parts = exp.start_date.split('/')
                start_date = datetime(int(start_parts[-1]), int(start_parts[0]), 1)

                if exp.end_date:
                    end_parts = exp.end_date.split('/')
                    end_date = datetime(int(end_parts[-1]), int(end_parts[0]), 28)
                else:
                    end_date = current_date

                months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_months += max(0, months)
            except:
                continue

        return round(total_months / 12, 1)
