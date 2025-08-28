"""
Role Content Manager - Categorizes CV content by job roles
CVPilot - Organizes summaries, skills, and bullets by role for better learning
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime

from .logger import LoggerMixin
from .models import JobData


@dataclass
class RoleContent:
    """Content specific to a role"""
    role_name: str
    summaries: List[str]
    bullet_points: List[str]
    skills: List[str]
    software: List[str]
    achievements: List[str]
    cv_count: int
    last_updated: str
    success_metrics: Dict[str, float]  # fit_scores, user_ratings, etc.


class RoleContentManager(LoggerMixin):
    """Manages CV content categorized by job roles"""

    def __init__(self, data_dir: str = "./data/role_content"):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.content_file = self.data_dir / "role_content_database.json"
        
        # Role mapping and standardization
        self.role_mapping = {
            # Standard roles
            'product manager': 'Product Manager',
            'product analyst': 'Product Analyst', 
            'business analyst': 'Business Analyst',
            'data analyst': 'Data Analyst',
            'project manager': 'Project Manager',
            'product owner': 'Product Owner',
            'product operations specialist': 'Product Operations Specialist',
            'quality assurance analyst': 'Quality Assurance Analyst',
            'quality analyst': 'Quality Analyst',
            
            # Aliases and variations
            'pm': 'Product Manager',
            'pa': 'Product Analyst',
            'ba': 'Business Analyst', 
            'da': 'Data Analyst',
            'pjm': 'Project Manager',
            'po': 'Product Owner',
            'qa': 'Quality Assurance Analyst',
            'qaa': 'Quality Assurance Analyst'
        }
        
        # Load existing database
        self.role_database = self._load_role_database()
        
        self.logger.info(f"✅ RoleContentManager initialized with {len(self.role_database)} roles")

    def _load_role_database(self) -> Dict[str, RoleContent]:
        """Load role content database from file"""
        if not self.content_file.exists():
            return {}
        
        try:
            with open(self.content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict to RoleContent objects
            database = {}
            for role_name, content_data in data.items():
                database[role_name] = RoleContent(**content_data)
            
            return database
        except Exception as e:
            self.logger.error(f"❌ Error loading role database: {e}")
            return {}

    def _save_role_database(self):
        """Save role content database to file"""
        try:
            # Convert RoleContent objects to dict
            data = {}
            for role_name, content in self.role_database.items():
                data[role_name] = asdict(content)
            
            with open(self.content_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"💾 Role database saved with {len(data)} roles")
        except Exception as e:
            self.logger.error(f"❌ Error saving role database: {e}")

    def standardize_role_name(self, role_input: str) -> str:
        """Standardize role name using mapping"""
        role_lower = role_input.lower().strip()
        return self.role_mapping.get(role_lower, role_input.title())

    def add_cv_content(self, role_name: str, summary: str = None, 
                      bullet_points: List[str] = None, skills: List[str] = None,
                      software: List[str] = None, achievements: List[str] = None,
                      success_score: float = None):
        """Add content for a specific role"""
        
        standardized_role = self.standardize_role_name(role_name)
        
        # Initialize role if doesn't exist
        if standardized_role not in self.role_database:
            self.role_database[standardized_role] = RoleContent(
                role_name=standardized_role,
                summaries=[],
                bullet_points=[],
                skills=[],
                software=[],
                achievements=[],
                cv_count=0,
                last_updated="",
                success_metrics={}
            )
        
        role_content = self.role_database[standardized_role]
        
        # Add new content
        if summary and summary not in role_content.summaries:
            role_content.summaries.append(summary)
            
        if bullet_points:
            for bullet in bullet_points:
                if bullet not in role_content.bullet_points:
                    role_content.bullet_points.append(bullet)
        
        if skills:
            for skill in skills:
                if skill not in role_content.skills:
                    role_content.skills.append(skill)
        
        if software:
            for tool in software:
                if tool not in role_content.software:
                    role_content.software.append(tool)
                    
        if achievements:
            for achievement in achievements:
                if achievement not in role_content.achievements:
                    role_content.achievements.append(achievement)
        
        # Update metadata
        role_content.cv_count += 1
        role_content.last_updated = datetime.now().isoformat()
        
        if success_score:
            if 'fit_scores' not in role_content.success_metrics:
                role_content.success_metrics['fit_scores'] = []
            role_content.success_metrics['fit_scores'].append(success_score)
        
        self._save_role_database()
        self.logger.info(f"📊 Added content to {standardized_role} (CV count: {role_content.cv_count})")

    def get_role_content(self, role_name: str) -> Optional[RoleContent]:
        """Get content for a specific role"""
        standardized_role = self.standardize_role_name(role_name)
        return self.role_database.get(standardized_role)

    def get_role_summaries(self, role_name: str, limit: int = 5) -> List[str]:
        """Get summaries for a specific role"""
        role_content = self.get_role_content(role_name)
        if not role_content:
            return []
        return role_content.summaries[:limit]

    def get_role_bullets(self, role_name: str, limit: int = 10) -> List[str]:
        """Get bullet points for a specific role"""
        role_content = self.get_role_content(role_name)
        if not role_content:
            return []
        return role_content.bullet_points[:limit]

    def get_role_skills(self, role_name: str) -> List[str]:
        """Get skills for a specific role"""
        role_content = self.get_role_content(role_name)
        if not role_content:
            return []
        return role_content.skills

    def find_similar_role_content(self, target_role: str, content_type: str = 'summaries') -> Dict[str, List[str]]:
        """Find similar content from related roles"""
        
        # Define role relationships
        role_relationships = {
            'Product Manager': ['Product Owner', 'Product Analyst'],
            'Product Analyst': ['Product Manager', 'Business Analyst', 'Data Analyst'],
            'Business Analyst': ['Product Analyst', 'Data Analyst', 'Project Manager'],
            'Data Analyst': ['Product Analyst', 'Business Analyst'],
            'Project Manager': ['Product Manager', 'Business Analyst'],
            'Product Owner': ['Product Manager', 'Product Analyst']
        }
        
        standardized_role = self.standardize_role_name(target_role)
        related_roles = role_relationships.get(standardized_role, [])
        
        similar_content = {}
        for role in [standardized_role] + related_roles:
            role_content = self.get_role_content(role)
            if role_content:
                if content_type == 'summaries':
                    similar_content[role] = role_content.summaries
                elif content_type == 'bullets':
                    similar_content[role] = role_content.bullet_points
                elif content_type == 'skills':
                    similar_content[role] = role_content.skills
                elif content_type == 'software':
                    similar_content[role] = role_content.software
        
        return similar_content

    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary of the entire role database"""
        summary = {
            'total_roles': len(self.role_database),
            'roles_by_content': {},
            'total_content': {
                'summaries': 0,
                'bullet_points': 0,
                'skills': 0,
                'software': 0,
                'achievements': 0,
                'cvs': 0
            }
        }
        
        for role_name, content in self.role_database.items():
            summary['roles_by_content'][role_name] = {
                'summaries': len(content.summaries),
                'bullet_points': len(content.bullet_points),
                'skills': len(content.skills),
                'software': len(content.software),
                'achievements': len(content.achievements),
                'cv_count': content.cv_count,
                'avg_success_score': sum(content.success_metrics.get('fit_scores', [0])) / max(len(content.success_metrics.get('fit_scores', [1])), 1)
            }
            
            # Add to totals
            summary['total_content']['summaries'] += len(content.summaries)
            summary['total_content']['bullet_points'] += len(content.bullet_points)
            summary['total_content']['skills'] += len(content.skills)
            summary['total_content']['software'] += len(content.software)
            summary['total_content']['achievements'] += len(content.achievements)
            summary['total_content']['cvs'] += content.cv_count
        
        return summary

    def migrate_existing_data(self):
        """Migrate existing CVs and user profile data into role-based structure"""
        self.logger.info("🔄 Starting migration of existing data...")
        
        # 1. Migrate from user profile
        self._migrate_from_user_profile()
        
        # 2. Migrate from existing CVs
        self._migrate_from_existing_cvs()
        
        # 3. Migrate from bullet pool
        self._migrate_from_bullet_pool()
        
        self.logger.info("✅ Migration completed")

    def _migrate_from_user_profile(self):
        """Migrate data from user profile"""
        try:
            profile_file = Path("data/user_profiles/user_profile.json")
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                
                # Extract achievements by role
                for exp in profile.get('work_experience', []):
                    position = exp.get('position', '')
                    achievements = exp.get('achievements', [])
                    
                    if achievements:
                        self.add_cv_content(
                            role_name=position,
                            achievements=achievements
                        )
                
                self.logger.info("📊 Migrated data from user profile")
        except Exception as e:
            self.logger.error(f"❌ Error migrating from user profile: {e}")

    def _migrate_from_existing_cvs(self):
        """Migrate data from existing CV outputs"""
        try:
            output_dir = Path("output")
            if output_dir.exists():
                for folder in output_dir.iterdir():
                    if folder.is_dir():
                        # Extract role from folder name
                        folder_name = folder.name
                        role = self._extract_role_from_folder_name(folder_name)
                        
                        if role:
                            # Count CVs for this role
                            cvs = list(folder.glob("*.docx"))
                            for cv in cvs:
                                # For now, just count - could extract actual content later
                                self.add_cv_content(role_name=role)
                
                self.logger.info("📊 Migrated data from existing CVs")
        except Exception as e:
            self.logger.error(f"❌ Error migrating from existing CVs: {e}")

    def _migrate_from_bullet_pool(self):
        """Migrate bullets from bullet pool by role context"""
        try:
            from .intelligent_bullet_analyzer import EnhancedBulletAnalyzer
            
            analyzer = EnhancedBulletAnalyzer()
            bullet_pool = analyzer.bullet_pool
            
            # Extract bullets from advanced profile
            advanced_bullets = bullet_pool.get('advanced', {}).get('bullets', {})
            
            for company, bullets in advanced_bullets.items():
                # Try to infer role from company context or bullets
                inferred_roles = self._infer_roles_from_bullets(bullets)
                
                for role in inferred_roles:
                    self.add_cv_content(
                        role_name=role,
                        bullet_points=bullets
                    )
            
            self.logger.info("📊 Migrated data from bullet pool")
        except Exception as e:
            self.logger.error(f"❌ Error migrating from bullet pool: {e}")

    def _extract_role_from_folder_name(self, folder_name: str) -> Optional[str]:
        """Extract role from folder name"""
        folder_lower = folder_name.lower()
        
        if 'product manager' in folder_lower or 'pm' in folder_lower:
            return 'Product Manager'
        elif 'product analyst' in folder_lower or 'pa' in folder_lower:
            return 'Product Analyst'
        elif 'business analyst' in folder_lower or 'ba' in folder_lower:
            return 'Business Analyst'
        elif 'data analyst' in folder_lower or 'da' in folder_lower:
            return 'Data Analyst'
        elif 'project manager' in folder_lower or 'pjm' in folder_lower:
            return 'Project Manager'
        elif 'product owner' in folder_lower or 'po' in folder_lower:
            return 'Product Owner'
        
        return None

    def _infer_roles_from_bullets(self, bullets: List[str]) -> List[str]:
        """Infer roles from bullet content"""
        roles = set()
        
        for bullet in bullets:
            bullet_lower = bullet.lower()
            
            # Role-specific keywords
            if any(keyword in bullet_lower for keyword in ['product', 'roadmap', 'strategy']):
                roles.add('Product Manager')
            if any(keyword in bullet_lower for keyword in ['analysis', 'metrics', 'kpi']):
                roles.add('Product Analyst')
            if any(keyword in bullet_lower for keyword in ['business', 'requirements', 'process']):
                roles.add('Business Analyst')
            if any(keyword in bullet_lower for keyword in ['data', 'sql', 'tableau']):
                roles.add('Data Analyst')
            if any(keyword in bullet_lower for keyword in ['project', 'timeline', 'delivery']):
                roles.add('Project Manager')
        
        return list(roles) if roles else ['Product Analyst']  # Default fallback

