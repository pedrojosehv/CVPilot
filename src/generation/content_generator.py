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
from ..utils.template_learning_system import TemplateLearningSystem

class ContentGenerator(LoggerMixin):
    """Generate CV content using LLMs"""

    def __init__(self, llm_config: LLMConfig, datapm_path: str = None, templates_path: str = None, user_profile_manager=None):
        super().__init__()
        self.config = llm_config
        self.datapm_path = datapm_path
        self.templates_path = templates_path
        self.user_profile_manager = user_profile_manager
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

        # Initialize learning system for successful summaries
        self.learning_system = TemplateLearningSystem()
    
    def _setup_llm_client(self):
        """Setup LLM client based on provider"""
        if self.config.provider == "openai":
            openai.api_key = self.config.api_key
            self.openai_model = self.config.get_model_name()
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
        """Generate professional summary using learning system"""

        # FIRST: Try to find a similar successful summary to reuse
        job_data_dict = {
            'job_title_original': job_data.job_title_original,
            'company': job_data.company,
            'skills': job_data.skills,
            'software': job_data.software
        }

        similar_summary = self.learning_system.find_similar_successful_summary(job_data_dict)

        if similar_summary:
            self.log_info(f"🎯 Using similar successful summary from learning system")
            return ReplacementBlock(
                placeholder="ProfileSummary",
                content=similar_summary.strip(),
                confidence=match_result.confidence,
                metadata={
                    "source": "learning_system_reuse",
                    "word_count": len(similar_summary.split()),
                    "reused": True
                }
            )

        # SECOND: If no similar summary found, generate new one using LLM
        self.log_info(f"🔄 No similar successful summary found, generating new one with LLM")

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
        
        # Extract key information for better prompt
        skills_str = ', '.join(job_data.skills[:12]) if job_data.skills else 'various technical and analytical skills'
        software_str = ', '.join(job_data.software[:8]) if job_data.software else 'industry-standard tools'

        # Detect role type for more specific focus
        role_type = detect_role_type(job_data.job_title_original)

        # Get real examples from existing templates instead of generic examples
        template_examples = self._get_template_summary_examples(job_data, match_result)

        # Get comprehensive user profile information
        user_profile_context = ""
        user_specific_achievements = []
        user_relevant_experience = []

        if self.user_profile_manager:
            try:
                profile_suggestions = self.user_profile_manager.get_personalized_content_suggestions(job_data)
                profile_summary = self.user_profile_manager.get_profile_summary()

                # Extract specific achievements from user's work experience
                recent_experience = profile_summary.get('recent_experience', [])
                for exp in recent_experience[:3]:  # Use most recent 3 experiences
                    if exp.get('achievements'):
                        user_specific_achievements.extend(exp['achievements'][:2])  # 2 achievements per role
                        user_relevant_experience.append({
                            'position': exp.get('position', ''),
                            'company': exp.get('company', ''),
                            'achievements': exp.get('achievements', [])[:2]
                        })

                # Build comprehensive user context
                exp_years = profile_summary.get('experience_years', 0)
                if exp_years > 0:
                    user_profile_context += f"User has {exp_years} years of professional experience. "

                # Add specific skills from profile
                top_skills = profile_summary.get('top_skills', [])[:5]
                if top_skills:
                    skill_names = [skill.get('name', '') for skill in top_skills if skill.get('name')]
                    if skill_names:
                        user_profile_context += f"User's key skills include: {', '.join(skill_names)}. "

                # Add specific technologies
                for exp in recent_experience[:2]:
                    technologies = exp.get('technologies', [])
                    if technologies:
                        user_profile_context += f"User has experience with: {', '.join(technologies[:3])}. "

                # Add industry background
                user_industries = [pref['industry_name'] for pref in profile_summary.get('industry_preferences', [])]
                if user_industries:
                    user_profile_context += f"User has background in: {', '.join(user_industries[:3])}. "

                self.log_info(f"✅ Extracted {len(user_specific_achievements)} specific achievements from user profile")

            except Exception as e:
                self.log_warning(f"Failed to get user profile context: {e}")
                # Fallback to basic context
                user_profile_context = "Professional with relevant experience in the field. "

        # Extract business context from job description
        business_context = self._extract_business_context(job_data, original_description)

        # Build comprehensive user achievements section
        user_achievements_text = ""
        if user_specific_achievements:
            user_achievements_text = "\n🎯 USER'S PROVEN ACHIEVEMENTS (use these as inspiration):\n"
            for i, achievement in enumerate(user_specific_achievements[:5], 1):
                user_achievements_text += f"{i}. {achievement}\n"
        elif user_relevant_experience:
            user_achievements_text = "\n🎯 USER'S RELEVANT EXPERIENCE:\n"
            for exp in user_relevant_experience[:2]:
                user_achievements_text += f"• {exp['position']} - {exp['company']}\n"
                for achievement in exp.get('achievements', [])[:2]:
                    user_achievements_text += f"  - {achievement}\n"

        prompt = f"""
        Write a high-quality CV summary for a {job_data.job_title_original} position. This MUST be exceptional quality - no generic phrases allowed.

        🎯 JOB REQUIREMENTS:
        - Position: {job_data.job_title_original}
        - Required Skills: {skills_str}
        - Required Software: {software_str}
        - Industry: {self._infer_industry_context(job_data, original_description)}

        💼 USER'S ACTUAL BACKGROUND:
        {user_profile_context}

        {user_achievements_text}

        📝 CRITICAL WRITING REQUIREMENTS:

        1. LENGTH: Write a comprehensive summary (MINIMUM 350 characters, MAXIMUM 550 characters)

        2. QUALITY STANDARDS - MUST FOLLOW ALL:
           ✅ Write in first person, neutral tone, no company names
           ✅ Include 3-4 SPECIFIC, MEASURABLE achievements with real numbers
           ✅ Use industry-specific terminology and challenges
           ✅ Show clear value proposition for this specific role
           ✅ Demonstrate deep understanding of role responsibilities
           ✅ Reference specific technologies and methodologies from user's background

        3. ABSOLUTELY FORBIDDEN PHRASES:
           ❌ "proven ability to optimize processes"
           ❌ "strong analytical and technical skills"
           ❌ "results-oriented professional"
           ❌ "experienced in [vague area]"
           ❌ "team player" or "detail-oriented"
           ❌ "passionate about" or "enthusiastic"
           ❌ Any placeholder text (X%, Y%, Z new processes)

        4. REQUIRED CONTENT STRUCTURE:
           • Start with years of experience + primary expertise area
           • Include 3-4 specific achievements with concrete metrics
           • Mention relevant tools/technologies from user's actual experience
           • Highlight methodology expertise (agile, data analysis, etc.)
           • End with unique value proposition for this role

        7. STRICT LENGTH ENFORCEMENT:
           • Do not exceed 550 characters under any circumstances
           • Count characters carefully before finalizing

        5. STUDY THESE EXCELLENT EXAMPLES (emulate their quality):
        {template_examples}

        6. QUALITY CHECKLIST (ensure all are true):
           ✅ LENGTH: 350-550 characters (current summary has {len(user_profile_context) + len(user_achievements_text)} chars of context)
           ✅ Contains 3+ specific numbers/metrics from user's real achievements
           ✅ Uses industry-specific language and methodologies
           ✅ Shows clear business impact with measurable results
           ✅ Demonstrates deep role understanding
           ✅ References user's actual technologies and tools
           ✅ Flows naturally and professionally
           ✅ Would impress a senior hiring manager
           ✅ STRICT LENGTH: Does not exceed 550 characters

        Write a summary that showcases the candidate's real expertise and achievements. Use the user's actual background and achievements as the foundation - do not invent or generalize.
        """
        
        # Generate initial content with higher token limit for comprehensive summaries
        content = self._call_llm(prompt, max_tokens=600)

        # Validate and improve quality if needed
        validated_content, quality_score = self._validate_and_improve_summary(
            content, job_data, match_result, template_examples
        )

        # Log quality information
        if quality_score < 0.7:
            self.log_warning(f"⚠️ Summary quality score: {quality_score:.2f} - may need improvement")
        else:
            self.log_info(f"✅ Summary quality score: {quality_score:.2f} - good quality")

        return ReplacementBlock(
            placeholder="ProfileSummary",
            content=validated_content.strip(),
            confidence=match_result.confidence,
            metadata={
                "word_count": len(validated_content.split()),
                "quality_score": quality_score,
                "regenerated": quality_score < 0.7
            }
        )

    def _get_template_summary_examples(self, job_data: JobData, match_result: MatchResult) -> str:
        """Get high-quality summary examples based on role type and industry"""

        # High-quality example summaries for different roles
        role_examples = {
            'business_operations': [
                "Business operations professional with 5+ years of experience optimizing SaaS platforms using SQL Server and Oracle databases. Successfully improved operational efficiency by 15% through database analysis and process redesign, resulting in $200k cost savings. Proficient in project management methodologies, consistently delivering on time and within budget. Leverages advanced Excel and Power BI for data-driven decision making and operational reporting.",
                "Operations specialist experienced in streamlining SaaS business processes and implementing data-driven solutions. Led cross-functional initiatives resulting in 25% reduction in operational bottlenecks through automated workflow optimization. Expert in SQL, Oracle, and process improvement methodologies, with proven track record of enhancing team productivity and reducing operational costs.",
                "Business operations expert specializing in SaaS platform optimization and operational excellence. Implemented automated reporting systems using SQL Server and Oracle, improving data accuracy by 30% and reducing manual processing time by 20 hours weekly. Skilled in stakeholder management and process redesign for scalable business operations."
            ],
            'product_management': [
                "Product manager with 4+ years driving SaaS product development from concept to launch. Led cross-functional teams in delivering 3 mobile applications, achieving 95% user satisfaction scores. Expert in agile methodologies, user research, and data-driven product decisions using analytics tools like Mixpanel and Google Analytics.",
                "Senior product manager experienced in B2B SaaS platforms and mobile applications. Successfully launched 2 products generating $2M+ in annual revenue. Proficient in user experience design, A/B testing, and stakeholder management. Uses SQL, Tableau, and Jira to drive product decisions and measure success metrics.",
                "Product management professional specializing in SaaS growth and user acquisition. Redesigned onboarding flow resulting in 40% improvement in user retention within 3 months. Expert in product analytics, user research methodologies, and cross-functional collaboration using agile frameworks and design thinking principles."
            ],
            'data_analysis': [
                "Data analyst with 5+ years transforming raw data into actionable business insights for SaaS companies. Built automated reporting dashboards using Tableau and Power BI, reducing reporting time by 60%. Expert in SQL, Python, and statistical analysis, with proven success in identifying revenue optimization opportunities and operational efficiencies.",
                "Business intelligence analyst experienced in SaaS metrics and KPI optimization. Developed comprehensive analytics framework using SQL Server, Oracle, and Tableau, improving data-driven decision making across 5 departments. Skilled in data visualization, trend analysis, and presenting complex findings to executive teams.",
                "Data analytics specialist focusing on SaaS product performance and user behavior analysis. Implemented advanced cohort analysis using SQL and Python, identifying $150k in annual revenue leakage. Proficient in A/B testing frameworks, statistical modeling, and automated reporting systems for operational dashboards."
            ],
            'project_management': [
                "Project manager with 6+ years delivering complex SaaS implementations and digital transformation initiatives. Managed 15+ cross-functional projects with 98% on-time delivery rate. Expert in agile and waterfall methodologies, stakeholder management, and risk mitigation strategies using Jira, Confluence, and MS Project.",
                "Senior project manager specializing in SaaS platform development and deployment. Led technical teams in 8 successful product launches, managing budgets up to $500k. Proficient in agile ceremonies, sprint planning, and resource allocation. Uses data analytics to optimize project timelines and predict delivery risks.",
                "Project management professional experienced in coordinating SaaS development teams and business stakeholders. Implemented project tracking systems using Jira and Excel, improving team productivity by 25% and reducing project delays by 30%. Skilled in change management, risk assessment, and vendor relationship management."
            ]
        }

        # Determine role type
        role_type = self._detect_role_type_for_examples(job_data.job_title_original)

        # Get relevant examples
        examples = role_examples.get(role_type, role_examples['business_operations'])

        # Format examples
        formatted_examples = []
        for i, example in enumerate(examples[:3], 1):
            formatted_examples.append(f"{i}. \"{example}\"")

        return "\n".join(formatted_examples)

    def _validate_and_improve_summary(self, content: str, job_data: JobData,
                                    match_result: MatchResult, template_examples: str, max_attempts: int = 2) -> tuple[str, float]:
        """Validate summary quality and regenerate if needed (with loop protection)"""

        current_content = content
        current_score = self._calculate_summary_quality(current_content, job_data)
        attempts = 0

        while attempts < max_attempts:
            char_count = len(current_content)

            # Check if content meets basic requirements
            if char_count >= 350 and char_count <= 600 and current_score >= 0.7:
                return current_content, current_score

            # If we've reached max attempts, return the best version we have
            if attempts >= max_attempts - 1:
                self.log_info(f"🔄 Max regeneration attempts reached. Using best available content ({char_count} chars, score: {current_score:.2f})")
                return current_content, current_score

            attempts += 1
            self.log_info(f"🔄 Regenerating summary (attempt {attempts}/{max_attempts}) - chars: {char_count}, score: {current_score:.2f}")

            # Create regeneration prompt based on the specific issue
            if char_count < 350:
                length_instruction = f"CRITICAL: Write a MUCH LONGER summary (aim for 420-480 characters, minimum 380)"
            elif char_count > 550:
                length_instruction = f"CRITICAL: Write a SHORTER summary (aim for 420-480 characters, maximum 520)"
            else:
                length_instruction = f"Write a comprehensive summary (aim for 450-550 characters)"

            improved_prompt = f"""
            The previous summary needs improvement. Please create a much better version:

            ORIGINAL SUMMARY: "{current_content}"

            SPECIFIC ISSUES TO FIX:
            - Length: {char_count} characters (aim for 450-550 characters)
            - Quality Score: {current_score:.2f} (needs to be > 0.7)

            REQUIREMENTS FOR THE NEW SUMMARY:
            1. {length_instruction}
            2. Include 3-4 SPECIFIC, MEASURABLE achievements with real numbers
            3. Remove all generic phrases (like "proven ability", "strong skills", etc.)
            4. Use industry-specific terminology for {job_data.job_title_original}
            5. Show clear business impact and measurable results
            6. Include specific technologies and methodologies from user's background
            7. STRICT LENGTH ENFORCEMENT: Do not exceed 550 characters under any circumstances

            EXCELLENT EXAMPLES TO EMULATE:
            {template_examples}

            Write a significantly better summary that would impress a hiring manager.
            """

            improved_content = self._call_llm(improved_prompt, max_tokens=500)
            improved_score = self._calculate_summary_quality(improved_content, job_data)
            improved_char_count = len(improved_content)

            # Use the improved version if it's better OR significantly closer to target length
            if (improved_score > current_score) or (abs(improved_char_count - 500) < abs(char_count - 500)):
                current_content = improved_content
                current_score = improved_score
                self.log_info(f"✅ Summary improved to {improved_char_count} chars, score: {improved_score:.2f}")
            else:
                self.log_warning(f"⚠️ Improvement attempt failed - keeping current version")

        return current_content, current_score

    def _calculate_summary_quality(self, content: str, job_data: JobData) -> float:
        """Calculate quality score for a summary (0.0 to 1.0)"""

        if not content or len(content.strip()) < 50:
            return 0.0

        score = 0.0
        content_lower = content.lower()

        # Length check - penalize summaries that are too short
        char_count = len(content)
        word_count = len(content.split())

        if char_count < 350:  # Reject summaries that are too short
            score -= 0.5  # Heavy penalty for being too short
        elif 350 <= char_count <= 550:  # Good length range
            score += 0.2
        elif char_count > 550:  # Too long
            score -= 0.3  # Heavy penalty for being too long

        # Additional word count check
        if word_count < 60:  # Too few words
            score -= 0.3
        elif 60 <= word_count <= 130:  # Good word count range
            score += 0.1

        # Contains specific numbers/metrics (+0.3 if has numbers)
        if any(char.isdigit() for char in content):
            # Check for percentage, dollar amounts, or other metrics
            if ('%' in content or '$' in content or any(term in content_lower for term in
                ['reduction', 'increase', 'improvement', 'efficiency', 'productivity', 'revenue'])):
                score += 0.3
            else:
                score += 0.1

        # Avoids forbidden generic phrases (-0.2 each)
        forbidden_phrases = [
            "proven ability", "strong analytical", "technical skills", "results-oriented",
            "experienced in", "team player", "detail-oriented", "passionate about",
            "enthusiastic", "hardworking", "dedicated", "motivated"
        ]

        for phrase in forbidden_phrases:
            if phrase in content_lower:
                score -= 0.1
                break

        # Contains job-specific terminology (+0.2)
        job_keywords = set(job_data.job_title_original.lower().split() +
                          job_data.skills + job_data.software)
        job_matches = sum(1 for keyword in job_keywords if keyword.lower() in content_lower)
        if job_matches >= 2:
            score += 0.2
        elif job_matches == 1:
            score += 0.1

        # Has professional structure (+0.2)
        if any(word in content_lower for word in ['years', 'experience', 'specialist', 'expert', 'professional']):
            score += 0.1
        if any(word in content for word in ['SQL', 'Oracle', 'Tableau', 'Python', 'Excel']):
            score += 0.1

        # Natural flow and professionalism (+0.1)
        if not content.endswith('.') and not content.endswith('!') and not content.endswith('?'):
            score -= 0.1  # Incomplete sentence

        # No placeholders or generic terms (+0.1)
        if 'x%' not in content_lower and 'y%' not in content_lower and 'z ' not in content_lower:
            score += 0.1

        return max(0.0, min(1.0, score))

    def _detect_role_type_for_examples(self, job_title: str) -> str:
        """Detect role type for selecting appropriate examples"""
        title_lower = job_title.lower()

        if any(keyword in title_lower for keyword in ['business operations', 'operations specialist', 'operations manager']):
            return 'business_operations'
        elif any(keyword in title_lower for keyword in ['product manager', 'product owner', 'product analyst']):
            return 'product_management'
        elif any(keyword in title_lower for keyword in ['data analyst', 'business analyst', 'business intelligence']):
            return 'data_analysis'
        elif any(keyword in title_lower for keyword in ['project manager', 'program manager']):
            return 'project_management'
        else:
            return 'business_operations'  # default

    def _extract_business_context(self, job_data: JobData, original_description: str) -> str:
        """Extract specific business context from job description to avoid generic content"""

        if not original_description:
            return f"Business Operations specialist supporting {job_data.company} operations using SQL Server, Oracle, and SQL technologies."

        # Look for specific business indicators
        description_lower = original_description.lower()

        # Digital/SaaS indicators
        if any(keyword in description_lower for keyword in ['saas', 'cloud', 'digital', 'platform', 'api', 'web', 'mobile', 'software']):
            return f"Digital operations specialist supporting {job_data.company}'s SaaS/cloud platforms using SQL Server, Oracle, and SQL for database management and business intelligence."

        # Manufacturing/Industrial indicators
        elif any(keyword in description_lower for keyword in ['manufacturing', 'production', 'industrial', 'supply chain', 'logistics', 'factory']):
            return f"Manufacturing operations specialist optimizing {job_data.company}'s production processes using SQL Server, Oracle, and SQL for operational data management."

        # Financial/Fintech indicators
        elif any(keyword in description_lower for keyword in ['financial', 'fintech', 'banking', 'payment', 'trading', 'investment']):
            return f"Financial operations specialist managing {job_data.company}'s financial data systems using SQL Server, Oracle, and SQL for transaction processing and reporting."

        # Healthcare/Medical indicators
        elif any(keyword in description_lower for keyword in ['healthcare', 'medical', 'clinical', 'patient', 'pharma', 'biotech']):
            return f"Healthcare operations specialist managing {job_data.company}'s clinical/administrative data using SQL Server, Oracle, and SQL for patient records and operational analytics."

        # Retail/E-commerce indicators
        elif any(keyword in description_lower for keyword in ['retail', 'ecommerce', 'customer', 'sales', 'commerce', 'merchandise']):
            return f"Retail operations specialist optimizing {job_data.company}'s customer data and sales operations using SQL Server, Oracle, and SQL for business analytics."

        # Default business context
        else:
            return f"Business Operations specialist supporting {job_data.company} core operations using SQL Server, Oracle, and SQL for data management and business intelligence."

    def _infer_industry_context(self, job_data: JobData, original_description: str) -> str:
        """Infer the specific industry context from job details"""

        if not original_description:
            return "Business Operations"

        description_lower = original_description.lower()
        company_lower = job_data.company.lower()

        # Digital/SaaS companies
        if any(keyword in description_lower or keyword in company_lower for keyword in ['saas', 'cloud', 'digital', 'platform', 'api', 'web', 'mobile', 'software', 'tech']):
            return "Digital/SaaS Technology"

        # Manufacturing/Industrial
        elif any(keyword in description_lower or keyword in company_lower for keyword in ['manufacturing', 'production', 'industrial', 'supply chain', 'factory', 'automotive']):
            return "Manufacturing & Industrial"

        # Financial/Fintech
        elif any(keyword in description_lower or keyword in company_lower for keyword in ['financial', 'fintech', 'banking', 'payment', 'trading', 'investment', 'finance']):
            return "Financial Services & Fintech"

        # Healthcare
        elif any(keyword in description_lower or keyword in company_lower for keyword in ['healthcare', 'medical', 'clinical', 'patient', 'pharma', 'biotech', 'hospital']):
            return "Healthcare & Life Sciences"

        # Retail/E-commerce
        elif any(keyword in description_lower or keyword in company_lower for keyword in ['retail', 'ecommerce', 'customer', 'sales', 'commerce', 'merchandise', 'consumer']):
            return "Retail & E-commerce"

        # Consulting
        elif any(keyword in description_lower or keyword in company_lower for keyword in ['consulting', 'advisory', 'strategy', 'transformation']):
            return "Management Consulting"

        # Default
        else:
            return "Business Operations"

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

        2. MINIMUM QUANTITY REQUIREMENT:
           - Each line MUST contain at least 8 specific skills
           - Do not use generic terms - be specific and detailed
           - Expand with industry-specific skills when needed

        3. QUALITY STANDARDS:
           - Use specific, industry-relevant skills
           - Include methodologies (Agile, Scrum, Kanban)
           - Add technical skills when relevant
           - Use professional terminology
           - Avoid generic terms like "Leadership" alone
           - Group related skills together
           - Keep each line under 120 characters

        4. EXAMPLES OF HIGH-QUALITY SKILLS (minimum 8 per line):
           - "Project Management, Agile (Scrum, Kanban), Stakeholder Management, Cross-functional Collaboration, Risk Assessment, Budget Planning, Team Leadership, Process Optimization"
           - "Python, Azure Machine Learning, Excel (advanced), SQL, Power BI, Tableau, Agile tools (Jira, Confluence, Slack), Git, Docker"

        5. CONTEXT-AWARE:
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
                    # Use the model name directly (for OpenAI it's just the model name)
                    model_name = self.config.model
                    if hasattr(self.config, 'get_model_name'):
                        model_name = self.config.get_model_name()
                    response = client.chat.completions.create(
                        model=model_name,
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
                    
                    # Use the model name directly (for Anthropic we need the full name)
                    model_name = self.config.model
                    if hasattr(self.config, 'get_model_name'):
                        model_name = self.config.get_model_name()
                    response = self.anthropic_client.messages.create(
                        model=model_name,
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
        # Use modern model from configuration
        model_name = self.config.model
        if hasattr(self.config, 'get_model_name'):
            model_name = self.config.get_model_name()
        # Handle Gemini models specifically - use the exact model names from the API
        if model_name == "gemini-2-0-flash-exp":
            model_name = "gemini-2.0-flash-exp"  # This is the correct name for the API
        elif model_name == "gemini-1.5-flash":
            model_name = "gemini-1.5-flash"  # This is also correct
        elif model_name == "gemini-2.5-flash":
            model_name = "gemini-2.5-flash"  # Available model
        self.gemini_model = genai.GenerativeModel(model_name)
    
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
