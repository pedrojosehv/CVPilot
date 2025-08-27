"""
Content generation module using LLMs
"""

import json
from datetime import datetime
from typing import List, Dict, Any
import openai
import anthropic

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from ..utils.models import JobData, MatchResult, Replacements, ReplacementBlock, LLMConfig
from ..utils.logger import LoggerMixin
from ..ingest.datapm_loader import DataPMLoader
from ..utils.multi_template_processor import MultiTemplateProcessor
from ..utils.enriched_skills_config import get_skills_for_role, get_priority_skills
from ..utils.api_key_manager import get_api_key, mark_api_error
from ..utils.skills_templates import get_role_specific_skills, detect_role_type
from ..utils.intelligent_bullet_analyzer import EnhancedBulletAnalyzer
from ..utils.experience_analyzer import ExperienceAnalyzer

class ContentGenerator(LoggerMixin):
    """Generate CV content using LLMs"""
    
    def __init__(self, llm_config: LLMConfig, datapm_path: str = None, templates_path: str = None):
        super().__init__()
        self.config = llm_config
        self.datapm_path = datapm_path
        self.templates_path = templates_path
        self._setup_llm_client()
        
        # Initialize DataPM loader if path provided
        if datapm_path:
            from pathlib import Path
            self.datapm_loader = DataPMLoader(Path(datapm_path))
        else:
            self.datapm_loader = None
        
        # Initialize MultiTemplateProcessor if templates path provided
        if templates_path:
            from pathlib import Path
            self.multi_template_processor = MultiTemplateProcessor(Path(templates_path))
        else:
            self.multi_template_processor = None
        
        # Initialize enhanced analyzers
        self.bullet_analyzer = EnhancedBulletAnalyzer()
        self.experience_analyzer = ExperienceAnalyzer()
    
    def _setup_llm_client(self):
        """Setup LLM client based on provider"""
        if self.config.provider == "openai":
            openai.api_key = self.config.api_key
        elif self.config.provider == "anthropic":
            self.anthropic_client = anthropic.Anthropic(api_key=self.config.api_key)
        elif self.config.provider == "gemini" and GEMINI_AVAILABLE:
            # Setup Gemini with API key rotation
            if self.config.api_keys:
                self.gemini_keys = self.config.api_keys
                self.current_key_idx = 0
                self._configure_gemini_for_key(self.gemini_keys[self.current_key_idx])
            else:
                raise ValueError("Gemini API keys required for gemini provider")
    
    def generate_replacements(self, job_data: JobData, match_result: MatchResult) -> Replacements:
        """Generate all replacement content for the CV template"""
        
        self.log_info(f"Generating content for job: {job_data.job_title_original} at {job_data.company}")
        
        # Generate profile summary
        profile_summary = self._generate_profile_summary(job_data, match_result)
        
        # Generate top bullets
        top_bullets = self._generate_top_bullets(job_data, match_result)
        
        # Generate skill list
        skill_list = self._generate_skill_list(job_data, match_result)
        
        # Generate software list
        software_list = self._generate_software_list(job_data, match_result)
        
        # Generate objective title
        objective_title = self._generate_objective_title(job_data, match_result)
        
        # Generate ATS recommendations
        ats_recommendations = self._generate_ats_recommendations(job_data, match_result)
        
        return Replacements(
            profile_summary=profile_summary,
            top_bullets=top_bullets,
            skill_list=skill_list,
            software_list=software_list,
            objective_title=objective_title,
            ats_recommendations=ats_recommendations,
            job_id=job_data.job_id,
            company=job_data.company,
            position=job_data.job_title_original,
            generated_at=datetime.now().isoformat()
        )
    
    def generate_optimized_replacements(self, job_data: JobData, match_result: MatchResult, base_template: str) -> Replacements:
        """Generate optimized replacements using multi-template approach"""
        
        if not self.multi_template_processor:
            self.log_warning("MultiTemplateProcessor not available, falling back to standard generation")
            return self.generate_replacements(job_data, match_result)
        
        self.log_info(f"Generating optimized content for job: {job_data.job_title_original}")
        
        # Generate optimized content using multi-template approach
        optimized_content = self.multi_template_processor.generate_optimized_cv_content(
            job_data, match_result, base_template
        )
        
        # Generate high-quality summary using LLM (even with multi-template)
        profile_summary = self._generate_profile_summary(job_data, match_result)
        
        # Use optimized content for other elements
        summary_content = profile_summary.content
        
        # Ensure bullet points content is string
        bullet_points = optimized_content.get('bullet_points', [])
        if isinstance(bullet_points, list):
            bullet_content = "\n".join([f"• {bullet}" for bullet in bullet_points]) if bullet_points else "• Led successful projects with measurable results\n• Managed cross-functional teams effectively\n• Implemented strategic initiatives driving growth"
        elif not bullet_points:
            bullet_content = "• Led successful projects with measurable results\n• Managed cross-functional teams effectively\n• Implemented strategic initiatives driving growth"
        else:
            bullet_content = bullet_points
        
        # Create multiple bullet ReplacementBlocks (need 3-5 for validation)
        bullet_lines = bullet_content.split('\n') if bullet_content else []
        bullet_blocks = []
        
        # If we don't have enough bullets, create fallback ones
        if len(bullet_lines) < 3:
            fallback_bullets = [
                "Led successful projects with measurable results",
                "Managed cross-functional teams effectively", 
                "Implemented strategic initiatives driving growth",
                "Delivered projects on time and within budget",
                "Improved operational efficiency through process optimization"
            ]
            bullet_lines = fallback_bullets[:4]  # Take 4 bullets
        
        # Create individual ReplacementBlocks for each bullet
        for i, bullet in enumerate(bullet_lines[:5]):  # Max 5 bullets
            clean_bullet = bullet.strip().lstrip('•- ').strip()
            if clean_bullet:
                bullet_blocks.append(ReplacementBlock(
                    placeholder=f"TopBullet{i+1}",
                    content=clean_bullet,
                    confidence=match_result.confidence,
                    metadata={"source": "multi_template", "bullet_index": i+1}
                ))
        
        # Ensure we have at least 3 bullets
        while len(bullet_blocks) < 3:
            bullet_blocks.append(ReplacementBlock(
                placeholder=f"TopBullet{len(bullet_blocks)+1}",
                content="Delivered exceptional results through strategic project management",
                confidence=match_result.confidence,
                metadata={"source": "fallback", "bullet_index": len(bullet_blocks)+1}
            ))
        
        # Generate high-quality skills and software using LLM (even with multi-template)
        skill_list = self._generate_skill_list(job_data, match_result)
        software_list = self._generate_software_list(job_data, match_result)
        
        # Generate objective title and ATS recommendations using LLM
        objective_title = self._generate_objective_title(job_data, match_result)
        ats_recommendations = self._generate_ats_recommendations(job_data, match_result)
        
        return Replacements(
            profile_summary=profile_summary,
            top_bullets=bullet_blocks,  # Use the list of bullet blocks
            skill_list=skill_list,
            software_list=software_list,
            objective_title=objective_title,
            ats_recommendations=ats_recommendations,
            job_id=job_data.job_id,
            company=job_data.company,
            position=job_data.job_title_original,
            generated_at=datetime.now().isoformat()
        )
    
    def _generate_profile_summary(self, job_data: JobData, match_result: MatchResult) -> ReplacementBlock:
        """Generate professional summary"""
        
        # Try to get original job description from DataPM
        original_description = ""
        if self.datapm_loader:
            try:
                job_desc_data = self.datapm_loader.find_job_description(
                    job_data.job_title_original, 
                    job_data.company
                )
                if job_desc_data and job_desc_data.get('description'):
                    original_description = job_desc_data['description']
                    self.log_info(f"✅ Found original job description from {job_desc_data['source_file']}")
                else:
                    self.log_info("⚠️ No original job description found in DataPM files")
            except Exception as e:
                self.log_error(f"Error retrieving original job description: {str(e)}")
        
        # Get template insights if available
        template_insights = ""
        if self.multi_template_processor and hasattr(self.multi_template_processor, 'template_pool'):
            template_summaries = []
            for template_name, template_content in self.multi_template_processor.template_pool.items():
                if template_content.summary:
                    template_summaries.append(template_content.summary)
            if template_summaries:
                template_insights = f"\nTemplate Summary Examples:\n" + "\n".join(template_summaries[:3])
        
        prompt = f"""
        Generate a professional summary for a CV targeting this specific job:
        
        Job Title: {job_data.job_title_original}
        Company: {job_data.company}
        Required Skills: {', '.join(job_data.skills[:10])}
        Required Software: {', '.join(job_data.software[:5])}
        Seniority: {job_data.seniority or 'Not specified'}
        
        Profile Match Score: {match_result.fit_score:.2f}
        Matched Skills: {', '.join(match_result.matched_skills[:8])}
        
        Original Job Description:
        {original_description if original_description else 'Not available'}
        
        {template_insights}
        
        Requirements:
        - Generate EXACTLY 450 characters maximum (no truncation needed)
        - Focus on relevant experience and achievements
        - Highlight skills that match the job requirements
        - Use professional, confident tone
        - Include quantifiable achievements if possible
        - Avoid generic statements
        - If original description is available, incorporate key elements from it
        - Use the original job description and required skills as primary inspiration
        - Keep language neutral and professional - avoid mentioning specific companies or industries
        - Focus on capabilities and value proposition, not future goals or company-specific missions
        - If template examples are provided, use them as inspiration for style and structure
        
        Generate a compelling professional summary that focuses on your capabilities and value proposition without mentioning specific companies or future goals:
        """
        
        content = self._call_llm(prompt, max_tokens=300)
        
        return ReplacementBlock(
            placeholder="ProfileSummary",
            content=content.strip(),
            confidence=match_result.confidence,
            metadata={"word_count": len(content.split())}
        )
    
    def _generate_top_bullets(self, job_data: JobData, match_result: MatchResult) -> List[ReplacementBlock]:
        """Generate top achievement bullets using intelligent bullet analyzer"""
        
        # Try to get original job description from DataPM
        original_description = ""
        if self.datapm_loader:
            try:
                job_desc_data = self.datapm_loader.find_job_description(
                    job_data.job_title_original, 
                    job_data.company
                )
                if job_desc_data and job_desc_data.get('description'):
                    original_description = job_desc_data['description']
                    self.log_info(f"✅ Found original job description for bullet analysis")
            except Exception as e:
                self.log_error(f"Error retrieving job description for bullets: {str(e)}")
        
        # Use intelligent bullet analyzer
        try:
            job_data_dict = {
                'job_title_original': job_data.job_title_original,
                'company': job_data.company,
                'skills': job_data.skills,
                'software': job_data.software,
                'seniority': job_data.seniority
            }
            
            selected_bullets = self.bullet_analyzer.analyze_job_and_select_bullets(
                job_data_dict, original_description
            )
            
            # Convert to ReplacementBlock format
            bullet_blocks = []
            for i, bullet in enumerate(selected_bullets[:5]):  # Limit to 5 bullets
                # Clean up bullet text
                clean_bullet = bullet.strip()
                if clean_bullet.startswith(tuple('0123456789')):
                    clean_bullet = re.sub(r'^\d+\.\s*', '', clean_bullet)
                
                bullet_blocks.append(ReplacementBlock(
                    placeholder=f"TopBullet{i+1}",
                    content=clean_bullet,
                    confidence=match_result.confidence,
                    metadata={
                        "source": "intelligent_analyzer",
                        "bullet_index": i+1,
                        "length": len(clean_bullet)
                    }
                ))
            
            # Ensure we have at least 3 bullets
            while len(bullet_blocks) < 3:
                bullet_blocks.append(ReplacementBlock(
                    placeholder=f"TopBullet{len(bullet_blocks)+1}",
                    content="Delivered exceptional results through strategic project management and cross-functional collaboration",
                    confidence=match_result.confidence,
                    metadata={
                        "source": "fallback",
                        "bullet_index": len(bullet_blocks)+1,
                        "length": len("Delivered exceptional results through strategic project management and cross-functional collaboration")
                    }
                ))
            
            self.log_info(f"✅ Generated {len(bullet_blocks)} bullets using intelligent analyzer")
            return bullet_blocks
            
        except Exception as e:
            self.log_error(f"Intelligent bullet generation failed: {e}, using fallback")
            # Fallback to traditional LLM generation
            return self._generate_fallback_bullets(job_data, match_result)
    
    def _generate_fallback_bullets(self, job_data: JobData, match_result: MatchResult) -> List[ReplacementBlock]:
        """Fallback bullet generation using traditional LLM approach"""
        prompt = f"""
        Generate 4-5 compelling achievement bullets for a CV targeting this job:
        
        Job Title: {job_data.job_title_original}
        Company: {job_data.company}
        Key Skills Required: {', '.join(job_data.skills[:8])}
        Industry: {job_data.company} (infer from company name)
        
        Requirements for each bullet:
        - Start with strong action verbs
        - Include quantifiable results (%, $, numbers)
        - Focus on relevant achievements
        - Keep each bullet under 150 characters
        - Make them specific and impactful
        - Align with the job requirements
        
        Generate 4-5 achievement bullets in this format:
        1. [Action verb] [specific achievement] [quantifiable result]
        2. [Action verb] [specific achievement] [quantifiable result]
        ...
        """
        
        content = self._call_llm(prompt, max_tokens=500)
        
        # Parse bullets from response
        bullets = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                # Clean up the bullet
                clean_bullet = line.lstrip('1234567890.•- ').strip()
                if clean_bullet and len(clean_bullet) > 10:
                    bullets.append(ReplacementBlock(
                        placeholder="TopBullet",
                        content=clean_bullet,
                        confidence=match_result.confidence,
                        metadata={"length": len(clean_bullet)}
                    ))
        
        # Ensure we have 3-5 bullets
        if len(bullets) < 3:
            # Generate additional bullets if needed
            additional_prompt = f"Generate 2 more achievement bullets for {job_data.job_title_original} position:"
            additional_content = self._call_llm(additional_prompt, max_tokens=200)
            # Parse additional bullets...
        
        return bullets[:5]  # Limit to 5 bullets
    
    def _generate_skill_list(self, job_data: JobData, match_result: MatchResult) -> ReplacementBlock:
        """Generate intelligent skill list using LLM + enriched schema"""
        
        # Try to get original job description from DataPM
        original_description = ""
        if self.datapm_loader:
            try:
                job_desc_data = self.datapm_loader.find_job_description(
                    job_data.job_title_original, 
                    job_data.company
                )
                if job_desc_data and job_desc_data.get('description'):
                    original_description = job_desc_data['description']
                    self.log_info(f"✅ Found original job description for skills generation")
            except Exception as e:
                self.log_error(f"Error retrieving job description for skills: {str(e)}")
        
        # Create intelligent prompt for skills generation
        prompt = f"""
        Generate a professional, high-quality skills section for a CV targeting this specific role:
        
        JOB DETAILS:
        - Title: {job_data.job_title_original}
        - Company: {job_data.company}
        - Required Skills: {', '.join(job_data.skills[:10])}
        - Required Software: {', '.join(job_data.software[:5])}
        - Seniority: {job_data.seniority or 'Not specified'}
        
        PROFILE MATCH:
        - Fit Score: {match_result.fit_score:.2f}
        - Matched Skills: {', '.join(match_result.matched_skills[:8])}
        
        ORIGINAL JOB DESCRIPTION:
        {original_description if original_description else 'Not available'}
        
        REQUIREMENTS:
        1. Generate EXACTLY 2 lines of skills in this format:
           Line 1: Core professional skills (Project Management, Agile, etc.)
           Line 2: Technical skills and tools (Python, Azure ML, etc.)
        
        2. QUALITY STANDARDS:
           - Use specific, industry-relevant skills
           - Include methodologies (Agile, Scrum, Kanban)
           - Add technical skills when relevant
           - Use professional terminology
           - Avoid generic terms like "Leadership" alone
           - Group related skills together
           - Keep each line under 120 characters
        
        3. EXAMPLES OF HIGH-QUALITY SKILLS:
           - "Project Management, Agile (Scrum, Kanban), Stakeholder Management, Cross-functional Collaboration"
           - "Python, Azure Machine Learning, Excel (advanced), Agile tools (Jira, Confluence, Slack)"
        
        4. CONTEXT-AWARE:
           - If AI/ML role: Include technical skills (Python, ML frameworks, data analysis)
           - If construction: Include project planning, safety, regulatory compliance
           - If healthcare: Include regulatory compliance, clinical processes
           - If finance: Include financial analysis, risk management, compliance
        
        Generate the 2-line skills section:
        LINE 1 (Core Skills):
        LINE 2 (Technical Skills):
        """
        
        try:
            # Call LLM for intelligent skills generation
            llm_response = self._call_llm(prompt, max_tokens=300)
            
            # Parse the response
            lines = llm_response.strip().split('\n')
            core_skills = ""
            technical_skills = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith('LINE 1') or line.startswith('Core Skills'):
                    core_skills = line.split(':', 1)[1].strip() if ':' in line else line
                elif line.startswith('LINE 2') or line.startswith('Technical Skills'):
                    technical_skills = line.split(':', 1)[1].strip() if ':' in line else line
            
            # Combine into final skills content
            if core_skills and technical_skills:
                skills_content = f"{core_skills}. {technical_skills}."
            elif core_skills:
                skills_content = core_skills
            elif technical_skills:
                skills_content = technical_skills
            else:
                # Fallback to high-quality templates if LLM fails
                skills_content = self._generate_template_fallback_skills(job_data, match_result)
            
            return ReplacementBlock(
                placeholder="SkillList",
                content=skills_content,
                confidence=match_result.confidence,
                metadata={
                    "skill_count": len(skills_content.split(',')),
                    "source": "llm_generated",
                    "has_core_skills": bool(core_skills),
                    "has_technical_skills": bool(technical_skills)
                }
            )
            
        except Exception as e:
            self.log_error(f"LLM skills generation failed: {e}, using template fallback")
            # Fallback to high-quality templates
            return self._generate_template_fallback_skills(job_data, match_result)
    
    def _generate_fallback_skills(self, job_data: JobData, match_result: MatchResult) -> str:
        """Generate fallback skills using enriched schema"""
        
        # Get role-specific skills based on job title and requirements
        role_skills = get_skills_for_role(
            job_title=job_data.job_title_original,
            seniority=job_data.seniority,
            industry=self._detect_industry(job_data.job_title_original)
        )
        
        # Get high-priority skills
        high_priority_skills = get_priority_skills('high_priority')
        
        # Combine role-specific and high-priority skills
        all_skills = role_skills + high_priority_skills
        
        # Filter out skills that are already in software list
        job_software_lower = [sw.lower() for sw in job_data.software]
        filtered_skills = []
        
        for skill in all_skills:
            # Check if skill is not already in software list
            if not any(sw in skill.lower() or skill.lower() in sw for sw in job_software_lower):
                filtered_skills.append(skill)
        
        # Remove duplicates and take top 12
        unique_skills = list(dict.fromkeys(filtered_skills))
        selected_skills = unique_skills[:12]
        
        # If we don't have enough skills, add some generic PM skills
        if len(selected_skills) < 8:
            fallback_skills = [
                'Project Management', 'Stakeholder Management', 'Team Leadership',
                'Communication', 'Problem Solving', 'Strategic Thinking', 'Analytical Skills',
                'Time Management', 'Organization', 'Planning', 'Risk Management', 'Quality Management'
            ]
            for skill in fallback_skills:
                if skill not in selected_skills and len(selected_skills) < 12:
                    selected_skills.append(skill)
        
        return ", ".join(selected_skills)
    
    def _generate_template_fallback_skills(self, job_data: JobData, match_result: MatchResult) -> str:
        """Generate high-quality skills using role-specific templates"""
        
        # Use the template system for guaranteed high-quality skills
        skills_content = get_role_specific_skills(
            job_title=job_data.job_title_original,
            company=job_data.company,
            skills=job_data.skills
        )
        
        self.log_info(f"✅ Using high-quality skills template for role type: {detect_role_type(job_data.job_title_original, job_data.company)}")
        
        return skills_content
    
    def _detect_industry(self, job_title: str) -> str:
        """Detect industry from job title"""
        job_title_lower = job_title.lower()
        
        if any(keyword in job_title_lower for keyword in ['it', 'software', 'technology', 'digital', 'tech']):
            return 'it_technology'
        elif any(keyword in job_title_lower for keyword in ['construction', 'engineering', 'architect']):
            return 'construction_engineering'
        elif any(keyword in job_title_lower for keyword in ['manufacturing', 'production', 'industrial']):
            return 'manufacturing'
        elif any(keyword in job_title_lower for keyword in ['healthcare', 'medical', 'pharma', 'clinical']):
            return 'healthcare_pharma'
        elif any(keyword in job_title_lower for keyword in ['finance', 'banking', 'financial', 'investment']):
            return 'finance_banking'
        
        return None
        
        return ReplacementBlock(
            placeholder="SkillList",
            content=", ".join(unique_skills),
            confidence=match_result.confidence,
            metadata={"skill_count": len(unique_skills), "matched_count": len(match_result.matched_skills)}
        )
    
    def _generate_software_list(self, job_data: JobData, match_result: MatchResult) -> ReplacementBlock:
        """Generate intelligent software list using LLM + context"""
        
        # Try to get original job description from DataPM
        original_description = ""
        if self.datapm_loader:
            try:
                job_desc_data = self.datapm_loader.find_job_description(
                    job_data.job_title_original, 
                    job_data.company
                )
                if job_desc_data and job_desc_data.get('description'):
                    original_description = job_desc_data['description']
                    self.log_info(f"✅ Found original job description for software generation")
            except Exception as e:
                self.log_error(f"Error retrieving job description for software: {str(e)}")
        
        # Create intelligent prompt for software generation
        prompt = f"""
        Generate a professional, high-quality software/tools section for a CV targeting this specific role:
        
        JOB DETAILS:
        - Title: {job_data.job_title_original}
        - Company: {job_data.company}
        - Required Software: {', '.join(job_data.software[:8])}
        - Required Skills: {', '.join(job_data.skills[:5])}
        - Seniority: {job_data.seniority or 'Not specified'}
        
        PROFILE MATCH:
        - Matched Software: {', '.join(match_result.matched_software[:5])}
        
        ORIGINAL JOB DESCRIPTION:
        {original_description if original_description else 'Not available'}
        
        REQUIREMENTS:
        1. Generate a single line of software/tools in this format:
           "Tool1, Tool2, Tool3, Tool4, Tool5"
        
        2. QUALITY STANDARDS:
           - Prioritize software mentioned in job requirements
           - Include industry-standard tools for the role
           - Group related tools together (e.g., "Agile tools (Jira, Confluence, Slack)")
           - Use specific versions when relevant (e.g., "Excel (advanced)")
           - Keep under 120 characters total
           - Avoid generic terms, be specific
        
        3. EXAMPLES OF HIGH-QUALITY SOFTWARE LISTS:
           - "Python, Azure Machine Learning, Excel (advanced), Agile tools (Jira, Confluence, Slack)"
           - "Tableau, Power BI, SQL, Python, Google Analytics, Excel, Jira"
           - "Figma, Adobe Creative Suite, InVision, Miro, Slack, Jira, Confluence"
        
        4. CONTEXT-AWARE SELECTION:
           - AI/ML roles: Python, ML frameworks, data analysis tools
           - Product roles: Design tools, analytics, project management
           - Data roles: BI tools, databases, programming languages
           - Construction: CAD tools, project management, safety software
           - Healthcare: Clinical systems, regulatory tools, data analysis
        
        Generate the software/tools line:
        """
        
        try:
            # Call LLM for intelligent software generation
            llm_response = self._call_llm(prompt, max_tokens=200)
            
            # Clean and validate the response
            software_content = llm_response.strip()
            
            # Remove quotes and extra formatting
            software_content = software_content.strip('"').strip("'")
            
            # Ensure it's not too long
            if len(software_content) > 120:
                # Truncate intelligently
                words = software_content.split(', ')
                truncated = []
                current_length = 0
                for word in words:
                    if current_length + len(word) + 2 <= 120:  # +2 for ", "
                        truncated.append(word)
                        current_length += len(word) + 2
                    else:
                        break
                software_content = ', '.join(truncated)
            
            # If LLM response is empty or invalid, use fallback
            if not software_content or len(software_content) < 10:
                software_content = self._generate_fallback_software(job_data, match_result)
            
            return ReplacementBlock(
                placeholder="SoftwareList",
                content=software_content,
                confidence=match_result.confidence,
                metadata={
                    "software_count": len(software_content.split(',')),
                    "source": "llm_generated",
                    "length": len(software_content)
                }
            )
            
        except Exception as e:
            self.log_error(f"LLM software generation failed: {e}, using fallback")
            # Fallback to static approach
            return self._generate_fallback_software(job_data, match_result)
    
    def _generate_fallback_software(self, job_data: JobData, match_result: MatchResult) -> str:
        """Generate fallback software list using static approach"""
        
        # Define technical software/tools categories
        software_tools = [
            # Analytics & BI
            'Power BI', 'Tableau', 'Looker', 'Google Analytics', 'Mixpanel', 'Amplitude', 'Hotjar',
            # Development & Cloud
            'Jira', 'Confluence', 'GitHub', 'GitLab', 'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes',
            # Design & Prototyping
            'Figma', 'Sketch', 'Adobe XD', 'InVision', 'Marvel', 'Balsamiq', 'Miro', 'Lucidchart',
            # Communication & Collaboration
            'Slack', 'Microsoft Teams', 'Zoom', 'Notion', 'Asana', 'Trello', 'Monday.com',
            # CRM & Sales
            'Salesforce', 'HubSpot', 'Pipedrive', 'Zendesk', 'Intercom',
            # Programming & Databases
            'SQL', 'Python', 'R', 'JavaScript', 'MongoDB', 'PostgreSQL', 'MySQL',
            # Testing & Optimization
            'Optimizely', 'VWO', 'Google Optimize', 'Selenium', 'Cypress',
            # Office & Productivity
            'Excel', 'Power Query', 'Google Sheets', 'PowerPoint', 'Word'
        ]
        
        # Extract software from job requirements and match results
        all_software = list(set(job_data.software + match_result.matched_software))
        
        # Filter to include only actual software/tools
        filtered_software = []
        for item in all_software:
            item_lower = item.lower()
            # Check if it matches known software tools
            if any(tool.lower() in item_lower or item_lower in tool.lower() for tool in software_tools):
                filtered_software.append(item)
        
        # If we don't have enough software, add some common ones based on role
        if len(filtered_software) < 8:
            job_title_lower = job_data.job_title_original.lower()
            if 'product' in job_title_lower:
                default_software = ['Jira', 'Confluence', 'Figma', 'Google Analytics', 'Excel', 'Slack', 'Miro']
            elif 'data' in job_title_lower:
                default_software = ['SQL', 'Python', 'Tableau', 'Power BI', 'Excel', 'R', 'Google Analytics']
            else:
                default_software = ['Excel', 'PowerPoint', 'Slack', 'Jira', 'Google Analytics']
            
            for sw in default_software:
                if sw not in filtered_software and len(filtered_software) < 10:
                    filtered_software.append(sw)
        
        # Sort by relevance (job requirements first, then matched software)
        software_priority = {}
        for sw in filtered_software:
            priority = 0
            if sw in job_data.software:
                priority += 200  # Highest priority for required software
            if sw in match_result.matched_software:
                priority += 100
            software_priority[sw] = priority
        
        sorted_software = sorted(filtered_software, key=lambda x: software_priority[x], reverse=True)
        
        # Take top 8 software and format nicely
        top_software = sorted_software[:8]
        
        # Group related tools
        if 'Jira' in top_software and 'Confluence' in top_software:
            # Replace individual entries with grouped version
            top_software = [sw for sw in top_software if sw not in ['Jira', 'Confluence']]
            top_software.insert(0, 'Agile tools (Jira, Confluence)')
        
        return ", ".join(top_software)
    
    def _generate_objective_title(self, job_data: JobData, match_result: MatchResult) -> ReplacementBlock:
        """Generate objective title using bullet pool selection"""
        
        # Convert job data to dict for bullet analyzer
        job_dict = {
            'job_title': job_data.job_title_original,
            'company': job_data.company,
            'seniority': job_data.seniority,
            'skills': job_data.skills,
            'software': job_data.software
        }
        
        # Determine profile type (basic or advanced)
        profile_type = "basic"  # Default
        if match_result.profile_type in ["product_management", "growth_pm", "data_pm"]:
            profile_type = "advanced"
        
        # Select appropriate role title from bullet pool - extract just the role title from the job title
        job_title_for_selection = job_dict.get('job_title', '')
        
        # Clean the job title to extract just the role part
        if '¡buscamos' in job_title_for_selection.lower():
            # Remove "¡Buscamos" and "!" from the beginning and end
            clean_title = job_title_for_selection.lower().replace('¡buscamos', '').replace('!', '').strip()
            # Extract the main role title (before "de" if present)
            if ' de ' in clean_title:
                clean_title = clean_title.split(' de ')[0].strip()
        else:
            clean_title = job_title_for_selection
        
        # Create a temporary job dict with the cleaned title
        temp_job_dict = job_dict.copy()
        temp_job_dict['job_title'] = clean_title
        
        selected_title = self.bullet_analyzer.select_appropriate_role_title(temp_job_dict, profile_type)
        
        self.log_info(f"🎯 Generated objective title: {selected_title} (profile: {profile_type})")
        
        return ReplacementBlock(
            placeholder="ObjectiveTitle",
            content=selected_title,
            confidence=match_result.confidence,
            metadata={"length": len(selected_title), "profile_type": profile_type, "source": "bullet_pool"}
        )
    
    def _generate_ats_recommendations(self, job_data: JobData, match_result: MatchResult) -> ReplacementBlock:
        """Generate ATS optimization recommendations"""
        prompt = f"""
        Generate ATS (Applicant Tracking System) optimization recommendations for this CV:
        
        Job Title: {job_data.job_title_original}
        Company: {job_data.company}
        Key Skills: {', '.join(job_data.skills[:10])}
        Required Software: {', '.join(job_data.software[:5])}
        
        Requirements:
        - Keep it under 100 words
        - Focus on keyword optimization
        - Include relevant industry terms
        - Suggest improvements for ATS scanning
        - Be specific and actionable
        
        Generate ATS recommendations:
        """
        
        content = self._call_llm(prompt, max_tokens=200)
        
        return ReplacementBlock(
            placeholder="ATSRecommendations",
            content=content.strip(),
            confidence=match_result.confidence,
            metadata={"word_count": len(content.split())}
        )
    
    def _call_llm(self, prompt: str, max_tokens: int = None) -> str:
        """Call the configured LLM with automatic API key rotation"""
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                if self.config.provider == "openai":
                    # Get API key from manager
                    api_key = get_api_key("round_robin")
                    if not api_key:
                        raise ValueError("No OpenAI API key available")
                    
                    client = openai.OpenAI(api_key=api_key)
                    response = client.chat.completions.create(
                        model=self.config.model,
                        messages=[
                            {"role": "system", "content": "You are a professional CV writer and career consultant. Generate high-quality, tailored content for job applications."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=self.config.temperature,
                        max_tokens=max_tokens or self.config.max_tokens
                    )
                    return response.choices[0].message.content
                
                elif self.config.provider == "anthropic":
                    # Get API key from manager
                    api_key = get_api_key("round_robin")
                    if not api_key:
                        raise ValueError("No Anthropic API key available")
                    
                    response = self.anthropic_client.messages.create(
                        model=self.config.model,
                        max_tokens=max_tokens or self.config.max_tokens,
                        temperature=self.config.temperature,
                        system="You are a professional CV writer and career consultant. Generate high-quality, tailored content for job applications.",
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response.content[0].text
                
                elif self.config.provider == "gemini" and GEMINI_AVAILABLE:
                    return self._call_gemini(prompt, max_tokens)
                
                else:
                    raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit errors
                if any(keyword in error_msg for keyword in ['rate limit', 'quota', 'too many requests']):
                    self.log_warning(f"Rate limit hit on attempt {attempt + 1}, rotating API key...")
                    mark_api_error(api_key, "rate_limit")
                    continue
                
                # Check for API key errors
                elif any(keyword in error_msg for keyword in ['invalid api key', 'authentication', 'unauthorized']):
                    self.log_error(f"API key error: {e}")
                    mark_api_error(api_key, "invalid_key")
                    continue
                
                # Other errors
                else:
                    self.log_error(f"LLM call failed: {e}")
                    if attempt == max_retries - 1:
                        break
                    continue
        
        # If all retries failed, return fallback content
        return self._generate_fallback_content(prompt)
    
    def _generate_fallback_content(self, prompt: str) -> str:
        """Generate fallback content when LLM fails"""
        if "summary" in prompt.lower():
            return "Experienced professional with proven track record in relevant field. Demonstrated expertise in key areas with measurable achievements."
        elif "bullet" in prompt.lower():
            return "• Led successful projects resulting in significant improvements\n• Managed cross-functional teams to deliver results\n• Implemented strategic initiatives driving growth"
        elif "skill" in prompt.lower():
            return "Project Management, Leadership, Strategic Planning, Communication, Problem Solving"
        elif "software" in prompt.lower():
            return "Microsoft Office, Project Management Tools, Analytics Platforms"
        elif "title" in prompt.lower():
            return "Senior Professional"
        elif "ats" in prompt.lower():
            return "Optimize keywords, use industry terminology, include quantifiable achievements, ensure proper formatting for ATS scanning."
        else:
            return "Professional content tailored to position requirements."
    
    def _configure_gemini_for_key(self, api_key: str):
        """Configure Gemini with a specific API key"""
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    
    def _call_gemini(self, prompt: str, max_tokens: int = None) -> str:
        """Call Gemini API with automatic key rotation"""
        max_retries = 5
        
        for attempt in range(max_retries):
            try:
                # Get API key from manager
                api_key = get_api_key("round_robin")
                if not api_key:
                    raise ValueError("No Gemini API key available")
                
                # Configure Gemini with current key
                self._configure_gemini_for_key(api_key)
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.config.temperature,
                        max_output_tokens=max_tokens or self.config.max_tokens
                    )
                )
                return response.text
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check for rate limit errors
                if any(keyword in error_msg for keyword in ['rate limit', 'quota', 'too many requests']):
                    self.log_warning(f"Gemini rate limit hit on attempt {attempt + 1}, rotating API key...")
                    mark_api_error(api_key, "rate_limit")
                    continue
                
                # Check for API key errors
                elif any(keyword in error_msg for keyword in ['invalid api key', 'authentication', 'unauthorized']):
                    self.log_error(f"Gemini API key error: {e}")
                    mark_api_error(api_key, "invalid_key")
                    continue
                
                # Other errors
                else:
                    self.log_error(f"Gemini API call failed: {e}")
                    if attempt == max_retries - 1:
                        break
                    continue
        
        # If all retries failed, return fallback content
        self.log_error("All Gemini API keys exhausted, using fallback content")
        return self._generate_fallback_content(prompt)
