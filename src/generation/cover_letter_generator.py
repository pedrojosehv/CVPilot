"""
Cover letter generator for CVPilot
Generates personalized cover letters based on job requirements and CV content
"""

import re
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.models import JobData, MatchResult, LLMConfig
from ..utils.logger import LoggerMixin


class CoverLetterGenerator(LoggerMixin):
    """Generate personalized cover letters"""

    def __init__(self, llm_config: LLMConfig, datapm_path: str = None):
        super().__init__()
        self.config = llm_config
        self.datapm_path = datapm_path
        self._setup_llm_client()

        if datapm_path:
            from pathlib import Path
            from ..ingest.datapm_loader import DataPMLoader
            self.datapm_loader = DataPMLoader(Path(datapm_path))
        else:
            self.datapm_loader = None

    def _setup_llm_client(self):
        """Setup LLM client with API key rotation"""
        self.llm_provider = self.config.provider.lower()
        # Handle both string and list for api_keys
        if isinstance(self.config.api_keys, str):
            self.api_keys = self.config.api_keys.split(',') if self.config.api_keys else []
        else:
            self.api_keys = self.config.api_keys if self.config.api_keys else []
        self.current_key_index = 0

        if self.llm_provider == 'openai':
            import openai
            self.client = openai.OpenAI(api_key=self.api_keys[0] if self.api_keys else None)
        elif self.llm_provider == 'anthropic':
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_keys[0] if self.api_keys else None)
        elif self.llm_provider == 'gemini':
            import google.generativeai as genai
            if self.api_keys:
                genai.configure(api_key=self.api_keys[0])
            self.client = genai.GenerativeModel(self.config.model)

    def _call_llm(self, prompt: str, max_retries: int = 5) -> str:
        """Call LLM with retry logic and API key rotation"""
        for attempt in range(max_retries):
            try:
                if self.llm_provider == 'openai':
                    response = self.client.chat.completions.create(
                        model=self.config.model,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    return response.choices[0].message.content.strip()

                elif self.llm_provider == 'anthropic':
                    response = self.client.messages.create(
                        model=self.config.model,
                        max_tokens=1000,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text.strip()

                elif self.llm_provider == 'gemini':
                    response = self.client.generate_content(prompt)
                    return response.text.strip()

            except Exception as e:
                self.log_warning(f"LLM API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")

                # Rotate API key if available
                if len(self.api_keys) > 1:
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    self._configure_for_key(self.api_keys[self.current_key_index])
                    self.log_info(f"Rotating API key... (key {self.current_key_index + 1}/{len(self.api_keys)})")

                if attempt == max_retries - 1:
                    raise Exception(f"LLM API call failed after {max_retries} attempts: {str(e)}")

        return ""

    def _configure_for_key(self, api_key: str):
        """Configure LLM client with new API key"""
        if self.llm_provider == 'openai':
            import openai
            self.client = openai.OpenAI(api_key=api_key)
        elif self.llm_provider == 'anthropic':
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
        elif self.llm_provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=api_key)

            # Handle Gemini model name conversion (same as content_generator.py)
            model_name = self.config.model
            if model_name == "gemini-2-0-flash-exp":
                model_name = "gemini-2.0-flash-exp"
            elif model_name == "gemini-1.5-flash":
                model_name = "gemini-1.5-flash"

            self.client = genai.GenerativeModel(model_name)

    def generate_cover_letter(self, job_data: JobData, match_result: MatchResult,
                            cv_content: Dict[str, str]) -> str:
        """Generate a personalized cover letter"""

        self.log_info(f"Generating cover letter for job: {job_data.job_title_original} at {job_data.company}")

        # Get original job description if available
        original_description = ""
        if self.datapm_loader:
            job_desc_data = self.datapm_loader.find_job_description(
                job_data.job_title_original, job_data.company
            )
            if job_desc_data:
                original_description = job_desc_data.get('job_description', '')

        # Extract key information from CV content (ensure they are strings)
        professional_summary = str(cv_content.get('profile_summary', ''))
        skills = str(cv_content.get('skill_list', ''))
        software = str(cv_content.get('software_list', ''))

        prompt = f"""
        Generate a personalized cover letter for this specific job application.

        JOB INFORMATION:
        - Position: {job_data.job_title_original}
        - Company: {job_data.company}
        - Required Skills: {', '.join(job_data.skills)}
        - Required Software: {', '.join(job_data.software)}
        - Seniority Level: {job_data.seniority}
        - Role Type: {'GROWTH' if 'growth' in job_data.job_title_original.lower() else 'DATA' if 'data' in job_data.job_title_original.lower() else 'PRODUCT'}

        ORIGINAL JOB DESCRIPTION:
        {original_description if original_description else 'Not available'}

        CV CONTENT:
        - Professional Summary: {professional_summary}
        - Skills: {skills}
        - Software: {software}

        MATCH ANALYSIS:
        - Initial Fit Score: {match_result.fit_score:.3f}
        - Matched Skills: {', '.join(match_result.matched_skills)}
        - Matched Software: {', '.join(match_result.matched_software)}

        CRITICAL REQUIREMENTS:
        1. Replace [Company] with: {job_data.company}
        2. TOTAL LENGTH: MAXIMUM 1000 characters (including spaces) - plan your content accordingly
        3. Structure: Exactly 3 paragraphs + greeting + closing
        4. Professional, confident tone
        5. Neutral language - avoid mentioning specific companies or industries
        6. Focus on capabilities and value proposition, not future goals
        7. CASE DEVELOPMENT FOCUS: Use ONLY development-focused cases from the available examples:
           - SaaS Accounting (Noddok) - Product delivery, user research to engineering handoff
           - Azure Model Training & Reliability - Technical improvement, model training
           - Billing Model Redesign - Business strategy + UX optimization
           - Interface Redesign & Efficiency - UX improvements, multidisciplinary teams
           - Mobile App (Compartaxi) - Full product lifecycle, user flows to market
           - Independent Project (DataPM) - AI tools development, modular design
        8. NATURAL CONNECTIONS: Introduction and closure MUST naturally relate to the development case chosen in paragraph 2

        PARAGRAPH STRUCTURE:
        - Paragraph 1 (Introduction): Connect your development experience with the role's needs - show how your development approach matches what they're seeking
        - Paragraph 2 (Development Case): Choose ONE development-focused case from your available examples. Develop it fully with specific technical/business details, metrics, and outcomes
        - Paragraph 3 (Closure): Build naturally from the development case - show how this approach delivers value in their specific context

        TEMPLATE STRUCTURE:
        Dear [Company] Recruitment Team,

        [Paragraph 1: Development-focused introduction - ~250 chars]

        [Paragraph 2: Detailed development case study - ~400 chars]

        [Paragraph 3: Natural closure building from the case - ~250 chars]

        Thank you for your time and consideration.

        Sincerely,
        Pedro Herrera
        pjherrera23@gmail.com
        +34 655 77 35 19

        Generate a compelling cover letter that fits within 1000 characters:
        """

        try:
            cover_letter = self._call_llm(prompt)

            # Validate length (should fit naturally now)
            if len(cover_letter) > 1250:
                self.log_warning(f"Cover letter too long ({len(cover_letter)} chars), truncating...")
                cover_letter = cover_letter[:1250]

            self.log_info(f"Cover letter generated successfully ({len(cover_letter)} characters)")
            return cover_letter

        except Exception as e:
            self.log_error(f"Cover letter generation failed: {str(e)}")
            raise

    def load_template(self, template_path: Path) -> str:
        """Load cover letter template"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            self.log_info(f"Cover letter template loaded from: {template_path}")
            return template
        except Exception as e:
            self.log_error(f"Failed to load cover letter template: {str(e)}")
            raise
