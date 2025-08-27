"""
User Profile Manager - Comprehensive User Data Management System
CVPilot - Automatically learns and maintains complete user profiles
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import asdict
from collections import defaultdict
import re

from .models import (
    UserProfile, UserContact, WorkExperience, Education, SkillProficiency,
    IndustryPreference, UserPreferences, InteractionHistory, LearningMetrics,
    JobData, ProcessingResult
)
from .logger import LoggerMixin


class UserProfileManager(LoggerMixin):
    """Manages comprehensive user profiles with automatic learning"""

    def __init__(self, data_dir: str = "./data/user_profiles"):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.profile_file = self.data_dir / "user_profile.json"
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # Load or create user profile
        self.profile = self._load_profile()

        # Auto-save on changes
        self.auto_save = True

        self.logger.info(f"✅ UserProfileManager initialized for user: {self.profile.user_id}")

    def _load_profile(self) -> UserProfile:
        """Load user profile from file or create new one"""
        if not self.profile_file.exists():
            self.logger.info("📝 Creating new user profile")
            return UserProfile()

        try:
            with open(self.profile_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return UserProfile(**data)
        except Exception as e:
            self.logger.error(f"❌ Error loading profile: {e}")
            # Create backup of corrupted file
            backup_path = self.backup_dir / f"corrupted_profile_{int(datetime.now().timestamp())}.json"
            try:
                import shutil
                shutil.copy2(self.profile_file, backup_path)
                self.logger.info(f"📁 Corrupted profile backed up to: {backup_path}")
            except:
                pass

            return UserProfile()

    def save_profile(self):
        """Save current profile to file"""
        try:
            # Create backup before saving
            if self.profile_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backup_dir / f"profile_backup_{timestamp}.json"
                import shutil
                shutil.copy2(self.profile_file, backup_file)

                # Keep only last 10 backups
                backups = sorted(self.backup_dir.glob("profile_backup_*.json"))
                if len(backups) > 10:
                    for old_backup in backups[:-10]:
                        old_backup.unlink()

            # Save current profile
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profile.dict(), f, indent=2, ensure_ascii=False, default=str)

            self.logger.info("💾 Profile saved successfully")

        except Exception as e:
            self.logger.error(f"❌ Error saving profile: {e}")

    def extract_from_cv_template(self, template_path: str):
        """Extract user information from CV template"""
        try:
            from docx import Document

            doc = Document(template_path)
            text_content = []

            # Extract all text from document
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())

            full_text = "\n".join(text_content)

            # Extract contact information
            self._extract_contact_info(full_text)

            # Extract work experience
            self._extract_work_experience(full_text)

            # Extract skills
            self._extract_skills_from_cv(full_text)

            # Extract education
            self._extract_education(full_text)

            if self.auto_save:
                self.save_profile()

            self.logger.info(f"📊 Extracted profile data from: {Path(template_path).name}")

        except Exception as e:
            self.logger.error(f"❌ Error extracting from CV template: {e}")

    def _extract_contact_info(self, text: str):
        """Extract contact information from text"""
        # Name extraction (usually first line or prominent text)
        lines = text.split('\n')[:5]  # Check first 5 lines
        for line in lines:
            line = line.strip()
            if len(line) > 3 and not any(keyword in line.lower() for keyword in
                                        ['curriculum', 'cv', 'resume', 'professional', 'experience']):
                # Likely a name - update if we don't have one
                if not self.profile.contact.name or self.profile.contact.name == "":
                    self.profile.contact.name = line
                    self.logger.info(f"📝 Extracted name: {line}")
                    break

    def _extract_work_experience(self, text: str):
        """Extract work experience from CV text - Enhanced version"""
        lines = text.split('\n')
        extracted_experience = []

        # Enhanced patterns for job titles and companies
        title_patterns = [
            # Direct title patterns - expanded to capture ALL roles from CV
            r'(Product Analyst|Product Operations Specialist|Quality Assurance Analyst|Product Manager|Business Operations|Digital Product Specialist|Project Manager|Business Analyst|Operations Specialist|Data Analyst|Senior .+|Junior .+|Lead .+|Principal .+|Mobile B2C Application|Internal Operations Platform|Noddok Saas Application)',
            # Title with specialization (parentheses)
            r'(Product Analyst|Product Operations Specialist|Quality Assurance Analyst|Product Manager|Business Operations|Digital Product Specialist|Project Manager|Business Analyst|Operations Specialist|Data Analyst|Senior .+|Junior .+|Lead .+|Principal .+|Mobile B2C Application|Internal Operations Platform|Noddok Saas Application)\s*\(([^)]+)\)',
            # Title followed by company
            r'(.+?)\s*[-–]\s*(.+?)\s*(?:\d{1,2}/\d{4}|\d{4})',
            # Company - Title format
            r'(.+?)\s*[-–]\s*(.+?)\s*(?:\d{1,2}/\d{4}|\d{4})'
        ]

        date_patterns = [
            r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current|Today)',
            r'(\d{1,2}/\d{4})\s*[-–]\s*Present',
            r'(\d{4})\s*[-–]\s*(\d{4}|Present)',
            r'(\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{4})'
        ]

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Look for date patterns first
            found_date = None
            for date_pattern in date_patterns:
                date_match = re.search(date_pattern, line)
                if date_match:
                    found_date = date_match.group(0)
                    break

            if found_date:
                # Found a date, look for job title in nearby lines
                search_range = 5  # Look 5 lines up and down
                title_found = None
                company_found = None

                # Search in current line and nearby lines
                for j in range(max(0, i-search_range), min(len(lines), i+search_range+1)):
                    if j == i:  # Skip the date line itself
                        continue

                    nearby_line = lines[j].strip()
                    if not nearby_line:
                        continue

                    # Look for job titles
                    for title_pattern in title_patterns:
                        title_match = re.search(title_pattern, nearby_line, re.IGNORECASE)
                        if title_match:
                            if len(title_match.groups()) >= 1:
                                title_found = title_match.group(1).strip()
                                # If there's a specialization in parentheses, include it
                                if len(title_match.groups()) >= 2 and title_match.group(2):
                                    title_found += f" ({title_match.group(2)})"

                                # Try to extract company from the same line
                                company_match = re.search(r'(.+?)\s*[-–]\s*' + re.escape(title_found), nearby_line, re.IGNORECASE)
                                if company_match:
                                    company_found = company_match.group(1).strip()
                                break

                    if title_found:
                        break

                # If we found a title and date, create experience entry
                if title_found and found_date:
                    # Parse dates
                    date_match = re.search(r'(\d{1,2}/\d{4}|\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|\d{4}|Present|Current|Today)', found_date)
                    if date_match:
                        start_date = date_match.group(1)
                        end_date_raw = date_match.group(2)

                        # Convert 4-digit years to MM/YYYY format if needed
                        if len(start_date) == 4:
                            start_date = f"01/{start_date}"
                        if end_date_raw and len(end_date_raw) == 4 and end_date_raw not in ['Present', 'Current', 'Today']:
                            end_date_raw = f"01/{end_date_raw}"

                        end_date = None if end_date_raw in ['Present', 'Current', 'Today'] else end_date_raw
                        is_current = end_date_raw in ['Present', 'Current', 'Today']

                        # Find company in nearby lines if not found yet
                        if not company_found:
                            # First try to find company in the same line or lines above
                            for j in range(max(0, i-3), i+1):  # Check lines above the date line
                                nearby_line = lines[j].strip()
                                # Look for company patterns - improved to capture real CV format
                                company_patterns = [
                                    r'(.+?)\s*[-–]\s*' + re.escape(title_found),  # Company - Title
                                    r'(.+?)\s*,\s*(.+?)\s*[-–]',  # Company, Description — Location
                                    r'(.+?)\s*[-–]\s*(.+?)\s*\(',  # Company — Description (Location)
                                ]
                                for pattern in company_patterns:
                                    company_match = re.search(pattern, nearby_line, re.IGNORECASE)
                                    if company_match:
                                        company_found = company_match.group(1).strip()
                                        break
                                if company_found:
                                    break

                        exp = WorkExperience(
                            company=company_found or "Unknown Company",
                            position=title_found,
                            start_date=start_date,
                            end_date=end_date,
                            is_current=is_current
                        )

                        # Check if this experience already exists
                        existing_exp = None
                        for existing in self.profile.work_experience:
                            if (existing.position.lower() == exp.position.lower() and
                                existing.company.lower() == exp.company.lower()):
                                existing_exp = existing
                                break

                        # Extract achievements/logros from lines following the job entry
                        achievements = []
                        # Look for achievement patterns in the next few lines
                        for k in range(i+1, min(len(lines), i+8)):  # Look up to 8 lines after the job
                            achievement_line = lines[k].strip()
                            if not achievement_line:
                                continue

                            # Stop if we hit another job title or date pattern (next job)
                            if re.search(r'\d{1,2}/\d{4}|\d{4}', achievement_line) or re.search(r'\b(Senior|Junior|Lead|Principal|Product|Business|Data|Quality|Operations|Project|Manager|Analyst|Specialist)\b', achievement_line, re.IGNORECASE):
                                if achievement_line != lines[i]:  # Don't stop on the current line
                                    break

                            # Look for achievement patterns (lines starting with action verbs and containing metrics)
                            if re.search(r'^(Led|Drove|Achieved|Increased|Implemented|Designed|Developed|Optimized|Reduced|Improved|Created|Managed|Delivered|Built|Streamlined)', achievement_line, re.IGNORECASE):
                                achievements.append(achievement_line)
                                # Also extract technologies mentioned
                                tech_matches = re.findall(r'\b(Python|SQL|Tableau|Power BI|Excel|Jira|Confluence|Mixpanel|GA4|Figma|React|JavaScript|HTML|CSS|Docker|AWS|Azure|GCP)\b', achievement_line, re.IGNORECASE)
                                if tech_matches:
                                    exp.technologies.extend([tech.title() for tech in tech_matches])

                        if achievements:
                            exp.achievements.extend(achievements)
                            self.logger.info(f"🎯 Added {len(achievements)} achievements for {exp.position}")

                        if not existing_exp:
                            self.profile.add_work_experience(exp)
                            extracted_experience.append(exp)
                            self.logger.info(f"💼 Added work experience: {exp.position} at {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})")
                        else:
                            self.logger.info(f"📝 Updated existing experience: {exp.position}")

            i += 1

        # Debug logging
        if extracted_experience:
            self.logger.info(f"✅ Extracted {len(extracted_experience)} work experience entries")
            for exp in extracted_experience[:3]:  # Log first 3
                self.logger.info(f"   • {exp.position} at {exp.company}")
        else:
            self.logger.warning("⚠️ No work experience entries extracted - checking raw text...")

            # Debug: Look for any Business Operations mentions
            if 'Business Operations' in text:
                self.logger.info("🔍 Found 'Business Operations' in raw text - extraction may need improvement")
            else:
                self.logger.warning("🔍 'Business Operations' not found in raw text")

    def _extract_skills_from_cv(self, text: str):
        """Extract skills from CV text"""
        # Common skill categories and keywords
        skill_categories = {
            'technical': ['python', 'sql', 'javascript', 'java', 'c++', 'react', 'node.js', 'html', 'css'],
            'tool': ['excel', 'tableau', 'power bi', 'jira', 'confluence', 'slack', 'github', 'docker'],
            'soft': ['leadership', 'communication', 'problem solving', 'team management', 'agile', 'scrum'],
            'domain': ['data analysis', 'product management', 'business intelligence', 'marketing', 'finance']
        }

        found_skills = set()

        for category, keywords in skill_categories.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    found_skills.add((keyword.title(), category))

        for skill_name, category in found_skills:
            skill = SkillProficiency(
                name=skill_name,
                category=category,
                proficiency_level=3,  # Default proficiency
                confidence_score=0.7  # Medium confidence from CV extraction
            )
            self.profile.add_skill(skill)

        if found_skills:
            self.logger.info(f"🛠️ Added {len(found_skills)} skills from CV")

    def _extract_education(self, text: str):
        """Extract education information from CV text"""
        # Look for education section
        education_keywords = ['education', 'university', 'college', 'degree', 'bachelor', 'master', 'phd']

        lines = text.split('\n')
        in_education_section = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if we're entering education section
            if any(keyword in line.lower() for keyword in education_keywords):
                in_education_section = True
                continue

            # If we're in education section, try to extract institution and degree
            if in_education_section and len(line) > 10:
                # Look for degree patterns
                degree_match = re.search(r'(Bachelor|Master|PhD|Associate|B\.S\.|M\.S\.|MBA|MBA)', line, re.IGNORECASE)
                if degree_match:
                    degree = degree_match.group(0)

                    # Extract institution (usually the rest of the line)
                    institution = re.sub(r'(Bachelor|Master|PhD|Associate|B\.S\.|M\.S\.|MBA|MBA).*', '', line, flags=re.IGNORECASE).strip()

                    if institution and len(institution) > 3:
                        education = Education(
                            institution=institution,
                            degree=degree
                        )

                        # Check if already exists
                        exists = any(edu.institution == education.institution and edu.degree == education.degree
                                   for edu in self.profile.education)

                        if not exists:
                            self.profile.education.append(education)
                            self.logger.info(f"🎓 Added education: {degree} from {institution}")

    def learn_from_interaction(self, job_data: JobData, result: ProcessingResult,
                             user_feedback: Optional[str] = None):
        """Learn from user interaction and update profile"""

        # Record the interaction
        interaction = InteractionHistory(
            interaction_id=f"int_{int(datetime.now().timestamp())}",
            timestamp=datetime.now().isoformat(),
            interaction_type="cv_generation",
            job_id=job_data.job_id,
            details={
                "job_title": job_data.job_title_original,
                "fit_score": result.fit_score,
                "processing_time": result.processing_time,
                "replacements_count": len(result.replacements.blocks),
                "company": job_data.company
            },
            outcome="success" if result.success else "error",
            user_feedback=user_feedback,
            processing_time=result.processing_time
        )

        self.profile.add_interaction(interaction)

        # Update learning metrics
        self.profile.learning_metrics.total_interactions += 1
        if result.success:
            self.profile.learning_metrics.successful_predictions += 1

        if result.fit_score > 0:
            # Update average fit score improvement (simplified)
            current_avg = self.profile.learning_metrics.average_fit_score_improvement
            new_avg = (current_avg + result.fit_score) / 2
            self.profile.learning_metrics.average_fit_score_improvement = new_avg

        # Extract skills from job requirements
        for skill in job_data.skills:
            existing_skill = next((s for s in self.profile.skills if s.name.lower() == skill.lower()), None)
            if not existing_skill:
                new_skill = SkillProficiency(
                    name=skill,
                    category=self._categorize_skill(skill),
                    proficiency_level=2,  # Job requirement level
                    confidence_score=0.8
                )
                self.profile.add_skill(new_skill)

        # Learn preferred industries
        industry = self._infer_industry_from_job(job_data)
        if industry:
            existing_pref = next((p for p in self.profile.industry_preferences
                                if p.industry_name == industry), None)
            if existing_pref:
                existing_pref.experience_years += 1
            else:
                pref = IndustryPreference(
                    industry_name=industry,
                    interest_level=3,
                    experience_years=1
                )
                self.profile.industry_preferences.append(pref)

        if self.auto_save:
            self.save_profile()

        self.logger.info(f"🧠 Learned from interaction: {job_data.job_title_original}")

    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill automatically"""
        skill_lower = skill.lower()

        if any(keyword in skill_lower for keyword in ['python', 'java', 'javascript', 'sql', 'html', 'css', 'c++', 'php']):
            return 'technical'
        elif any(keyword in skill_lower for keyword in ['excel', 'tableau', 'power bi', 'jira', 'slack', 'github']):
            return 'tool'
        elif any(keyword in skill_lower for keyword in ['leadership', 'communication', 'management', 'agile', 'scrum']):
            return 'soft'
        else:
            return 'domain'

    def _infer_industry_from_job(self, job_data: JobData) -> Optional[str]:
        """Infer industry from job data"""
        text_to_analyze = f"{job_data.company} {job_data.job_title_original} {' '.join(job_data.skills)}"

        industry_keywords = {
            "Technology/SaaS": ["saas", "software", "cloud", "digital", "platform", "api", "web", "mobile", "tech"],
            "Manufacturing": ["manufacturing", "production", "industrial", "supply chain", "factory"],
            "Financial Services": ["financial", "fintech", "banking", "payment", "trading", "investment"],
            "Healthcare": ["healthcare", "medical", "clinical", "patient", "pharma", "biotech"],
            "Retail/E-commerce": ["retail", "ecommerce", "customer", "sales", "commerce"],
            "Consulting": ["consulting", "advisory", "strategy", "transformation"],
            "Business Operations": ["operations", "business", "management", "process"]
        }

        for industry, keywords in industry_keywords.items():
            if any(keyword in text_to_analyze.lower() for keyword in keywords):
                return industry

        return None

    def get_personalized_content_suggestions(self, job_data: JobData) -> Dict[str, Any]:
        """Get personalized content suggestions based on user profile"""

        suggestions = {
            "recommended_skills": [],
            "relevant_experience": [],
            "industry_alignment": 0,
            "skill_match_score": 0,
            "experience_years": self.profile.calculate_experience_years()
        }

        # Get matching skills
        job_skills = set(job_data.skills)
        user_skills = {skill.name for skill in self.profile.skills}

        matching_skills = job_skills.intersection(user_skills)
        suggestions["skill_match_score"] = len(matching_skills) / len(job_skills) if job_skills else 0

        # Get relevant experience
        industry = self._infer_industry_from_job(job_data)
        if industry:
            relevant_exp = self.profile.get_industry_experience(industry)
            suggestions["relevant_experience"] = [exp.dict() for exp in relevant_exp[:3]]

        # Calculate industry alignment
        if industry:
            industry_pref = next((p for p in self.profile.industry_preferences
                                if p.industry_name == industry), None)
            if industry_pref:
                suggestions["industry_alignment"] = industry_pref.interest_level / 5.0

        return suggestions

    def get_profile_summary(self) -> Dict[str, Any]:
        """Get comprehensive profile summary"""
        return {
            "contact": self.profile.contact.dict(),
            "experience_years": self.profile.calculate_experience_years(),
            "top_skills": [skill.dict() for skill in self.profile.get_top_skills(10)],
            "recent_experience": [exp.dict() for exp in self.profile.get_recent_experience(3)],
            "education_count": len(self.profile.education),
            "industry_preferences": [pref.dict() for pref in self.profile.industry_preferences],
            "learning_stats": {
                "total_interactions": len(self.profile.interaction_history),
                "avg_fit_score": self.profile.learning_metrics.average_fit_score_improvement,
                "skills_count": len(self.profile.skills),
                "experience_entries": len(self.profile.work_experience)
            },
            "last_updated": self.profile.updated_at
        }

    def export_profile(self, output_file: str = "user_profile_export.json"):
        """Export complete profile for backup/analysis"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "profile": self.profile.dict(),
            "summary": self.get_profile_summary()
        }

        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

        self.logger.info(f"📤 Profile exported to: {output_path}")
        return output_path
