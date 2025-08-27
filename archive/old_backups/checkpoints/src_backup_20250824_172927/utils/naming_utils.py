"""
Naming utilities for CVPilot
Handles intelligent file and folder naming based on job roles and software categories
"""

import re
from typing import List, Dict, Tuple
from pathlib import Path

class NamingUtils:
    """Utilities for intelligent naming of files and folders"""
    
    # Role abbreviations mapping
    ROLE_ABBREVIATIONS = {
        'product manager': 'PM',
        'product analyst': 'PA',
        'growth product manager': 'GPM',
        'senior product manager': 'SPM',
        'product lead': 'PL',
        'product director': 'PD',
        'data analyst': 'DA',
        'data scientist': 'DS',
        'business analyst': 'BA',
        'marketing manager': 'MM',
        'sales manager': 'SM',
        'engineering manager': 'EM',
        'technical lead': 'TL',
        'software engineer': 'SE',
        'frontend developer': 'FD',
        'backend developer': 'BD',
        'full stack developer': 'FSD',
        'devops engineer': 'DE',
        'data engineer': 'DEng',
        'machine learning engineer': 'MLE',
        'ui/ux designer': 'UX',
        'product designer': 'PD',
        'visual designer': 'VD',
        'content strategist': 'CS',
        'product marketing manager': 'PMM',
        'customer success manager': 'CSM',
        'operations manager': 'OM',
        'project manager': 'PJM',
        'scrum master': 'SM',
        'agile coach': 'AC'
    }
    
    # Software category mappings
    SOFTWARE_CATEGORIES = {
        # AI & Machine Learning (HIGHEST PRIORITY)
        'ai_ml': ['python', 'tensorflow', 'pytorch', 'scikit-learn', 'keras', 'opencv', 'numpy', 'pandas', 'matplotlib', 'jupyter', 'c++', 'cuda', 'gpu', 'deep learning', 'machine learning', 'computer vision', 'nlp', 'neural networks'],
        # Analytics & Data
        'analytics': ['google analytics', 'mixpanel', 'amplitude', 'looker', 'tableau', 'power bi', 'snowflake', 'bigquery', 'redshift'],
        # Testing & Optimization
        'testing': ['optimizely', 'vwo', 'google optimize', 'hotjar', 'fullstory', 'mixpanel', 'amplitude', 'crazy egg', 'lucky orange'],
        # Design & Prototyping
        'design': ['figma', 'sketch', 'adobe xd', 'invision', 'framer', 'principle', 'protopie', 'marvel', 'balsamiq'],
        # Development & Code
        'development': ['git', 'github', 'gitlab', 'bitbucket', 'jenkins', 'docker', 'kubernetes', 'aws', 'azure', 'gcp'],
        # Communication & Collaboration
        'collaboration': ['slack', 'microsoft teams', 'zoom', 'notion', 'confluence', 'jira', 'asana', 'trello', 'monday.com'],
        # CRM & Sales
        'crm': ['salesforce', 'hubspot', 'pipedrive', 'zoho', 'freshsales', 'close', 'copper'],
        # Marketing & Automation
        'marketing': ['mailchimp', 'sendgrid', 'klaviyo', 'intercom', 'drift', 'zendesk', 'freshdesk']
    }
    
    # Business model abbreviations
    BUSINESS_MODELS = {
        'b2b': 'B2B',
        'b2c': 'B2C',
        'b2b2c': 'B2B2C',
        'saas': 'SaaS',
        'marketplace': 'MP',
        'ecommerce': 'EC',
        'fintech': 'FT',
        'healthtech': 'HT',
        'edtech': 'ET',
        'proptech': 'PT',
        'insurtech': 'IT',
        'legaltech': 'LT'
    }
    
    @staticmethod
    def extract_role_initials(job_title: str) -> str:
        """Extract role initials from job title (max 3 characters)"""
        if not job_title:
            return "PM"
        
        job_title_lower = job_title.lower().strip()
        
        # Check for exact matches first
        for role, abbreviation in NamingUtils.ROLE_ABBREVIATIONS.items():
            if role in job_title_lower:
                return abbreviation[:3]  # Limit to 3 characters
        
        # If no exact match, try to extract from common patterns
        words = job_title.split()
        
        # Look for key role words
        role_keywords = ['manager', 'analyst', 'engineer', 'developer', 'designer', 'lead', 'director']
        found_keywords = []
        
        for word in words:
            word_lower = word.lower()
            for keyword in role_keywords:
                if keyword in word_lower:
                    found_keywords.append(word)
                    break
        
        if found_keywords:
            # Take first letter of each found keyword
            initials = ''.join([word[0].upper() for word in found_keywords[:3]])
            return initials[:3]
        
        # Fallback: take first letters of first 3 words
        initials = ''.join([word[0].upper() for word in words[:3]])
        return initials[:3]
    
    @staticmethod
    def extract_software_category(software_list: List[str]) -> str:
        """Extract software category initials (max 4 characters)"""
        if not software_list:
            return "GEN"
        
        # Count software by category
        category_counts = {}
        for software in software_list:
            software_lower = software.lower()
            for category, tools in NamingUtils.SOFTWARE_CATEGORIES.items():
                if any(tool in software_lower for tool in tools):
                    category_counts[category] = category_counts.get(category, 0) + 1
        
        if not category_counts:
            return "GEN"
        
        # Priority categories (AI/ML should be prioritized)
        priority_categories = ['ai_ml', 'analytics', 'development']
        
        # Check if we have priority categories
        for priority_cat in priority_categories:
            if priority_cat in category_counts:
                if priority_cat == 'ai_ml':
                    return "AIML"  # Special abbreviation for AI/ML
                elif priority_cat == 'analytics':
                    return "ANAL"
                elif priority_cat == 'development':
                    return "CODE"
        
        # Get top 2 categories if no priority categories found
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        top_categories = [cat for cat, _ in sorted_categories[:2]]
        
        # Create abbreviation
        if len(top_categories) == 1:
            return top_categories[0][:4].upper()
        else:
            return ''.join([cat[:2].upper() for cat in top_categories])
    
    @staticmethod
    def extract_business_model(job_title: str, company: str = "") -> str:
        """Extract business model initials (max 3 characters)"""
        text_to_check = f"{job_title} {company}".lower()
        
        for model, abbreviation in NamingUtils.BUSINESS_MODELS.items():
            if model in text_to_check:
                return abbreviation[:3]
        
        # Default to SaaS if no specific model found
        return "SaaS"
    
    @staticmethod
    def get_specialization(job_title: str) -> str:
        """Extract role specialization using intelligent semantic analysis"""
        job_title_lower = job_title.lower()
        
        # Define specialization categories with weighted keywords
        specialization_scores = {
            'AI/ML': {
                'keywords': {
                    'artificial intelligence': 10,
                    'inteligencia artificial': 10,
                    'machine learning': 8,
                    'deep learning': 8,
                    'computer vision': 8,
                    'vision artificial': 8,
                    'neural networks': 6,
                    'ai': 5,
                    'ml': 5,
                    'tensorflow': 4,
                    'pytorch': 4,
                    'opencv': 4,
                    'nlp': 4,
                    'natural language processing': 4
                }
            },
            'Data Analytics': {
                'keywords': {
                    'data': 6,
                    'analytics': 8,
                    'business intelligence': 7,
                    'bi': 5,
                    'data science': 8,
                    'statistical analysis': 6,
                    'reporting': 5,
                    'dashboards': 5,
                    'kpis': 4,
                    'metrics': 4
                }
            },
            'Technical': {
                'keywords': {
                    'technical': 8,
                    'engineering': 7,
                    'software': 6,
                    'development': 6,
                    'programming': 6,
                    'architecture': 6,
                    'system': 5,
                    'platform': 5,
                    'infrastructure': 5
                }
            },
            'Growth': {
                'keywords': {
                    'growth': 10,
                    'acquisition': 7,
                    'marketing': 6,
                    'conversion': 6,
                    'retention': 6,
                    'user acquisition': 8,
                    'customer acquisition': 8,
                    'funnel': 5,
                    'optimization': 5
                }
            },
            'Agile': {
                'keywords': {
                    'agile': 8,
                    'scrum': 7,
                    'kanban': 6,
                    'sprint': 5,
                    'backlog': 5,
                    'sprint planning': 6,
                    'retrospective': 5,
                    'ceremonies': 4
                }
            },
            'Strategy': {
                'keywords': {
                    'strategy': 8,
                    'strategic': 7,
                    'roadmap': 6,
                    'vision': 6,
                    'planning': 5,
                    'business strategy': 8,
                    'product strategy': 8,
                    'go-to-market': 7,
                    'gtm': 5
                }
            }
        }
        
        # Calculate scores for each specialization
        scores = {}
        for specialization, config in specialization_scores.items():
            score = 0
            for keyword, weight in config['keywords'].items():
                if keyword in job_title_lower:
                    score += weight
            scores[specialization] = score
        
        # Find the highest scoring specialization
        if scores:
            best_specialization = max(scores, key=scores.get)
            best_score = scores[best_specialization]
            
            # Only return specialization if score is significant
            if best_score >= 5:
                return best_specialization
        
        # Fallback logic for common patterns
        if 'product owner' in job_title_lower:
            return 'Agile'
        elif 'product manager' in job_title_lower:
            return 'Strategy'
        elif 'data' in job_title_lower or 'analytics' in job_title_lower:
            return 'Data Analytics'
        elif 'technical' in job_title_lower or 'engineering' in job_title_lower:
            return 'Technical'
        
        return "General"
    
    @staticmethod
    def get_top_software_by_category(software_list: List[str], job_title: str = "", max_per_category: int = 1) -> List[str]:
        """Get top software tools using intelligent role-based prioritization"""
        if not software_list:
            return []
        
        job_title_lower = job_title.lower() if job_title else ""
        
        # Define role-specific software priorities with weighted scoring
        role_software_weights = {
            'ai_ml': {
                'python': 10,
                'c++': 9,
                'tensorflow': 8,
                'pytorch': 8,
                'opencv': 8,
                'scikit-learn': 7,
                'keras': 7,
                'jupyter': 6,
                'numpy': 6,
                'pandas': 6,
                'matplotlib': 5,
                'git': 5,
                'jira': 4,
                'confluence': 4,
                'figma': 3
            },
            'data_analytics': {
                'python': 9,
                'sql': 8,
                'tableau': 8,
                'power bi': 8,
                'google analytics': 7,
                'mixpanel': 7,
                'amplitude': 7,
                'looker': 7,
                'excel': 6,
                'r': 6,
                'jupyter': 6,
                'jira': 4,
                'confluence': 4
            },
            'development': {
                'git': 9,
                'github': 8,
                'docker': 8,
                'jenkins': 7,
                'kubernetes': 7,
                'aws': 7,
                'azure': 7,
                'python': 6,
                'java': 6,
                'javascript': 6,
                'jira': 5,
                'confluence': 5
            },
            'collaboration': {
                'jira': 9,
                'confluence': 8,
                'slack': 7,
                'teams': 7,
                'zoom': 6,
                'notion': 6,
                'asana': 6,
                'trello': 5,
                'figma': 4
            }
        }
        
        # Determine role context from job title
        role_context = NamingUtils._determine_role_context(job_title_lower)
        
        # Get appropriate weights for the role context
        software_weights = role_software_weights.get(role_context, {})
        
        # Score each software based on role relevance
        software_scores = []
        for software in software_list:
            software_lower = software.lower()
            score = 0
            
            # Check exact matches first
            if software_lower in software_weights:
                score = software_weights[software_lower]
            else:
                # Check partial matches
                for weight_software, weight in software_weights.items():
                    if weight_software in software_lower or software_lower in weight_software:
                        score = max(score, weight * 0.8)  # Partial match gets 80% of score
            
            # Bonus for technical software in technical roles
            if role_context in ['ai_ml', 'development'] and any(tech in software_lower for tech in ['python', 'c++', 'java', 'git', 'docker']):
                score += 2
            
            software_scores.append((software, score))
        
        # Sort by score and return top software
        software_scores.sort(key=lambda x: x[1], reverse=True)
        top_software = [software for software, score in software_scores[:3]]
        
        return top_software
    
    @staticmethod
    def _determine_role_context(job_title_lower: str) -> str:
        """Determine the primary role context from job title"""
        
        # AI/ML context keywords
        ai_ml_keywords = ['artificial intelligence', 'inteligencia artificial', 'machine learning', 
                         'deep learning', 'computer vision', 'vision artificial', 'neural networks', 
                         'ai', 'ml', 'tensorflow', 'pytorch', 'opencv', 'nlp']
        
        # Data analytics context keywords
        data_keywords = ['data', 'analytics', 'business intelligence', 'bi', 'data science', 
                        'statistical analysis', 'reporting', 'dashboards', 'kpis', 'metrics']
        
        # Development context keywords
        dev_keywords = ['technical', 'engineering', 'software', 'development', 'programming', 
                       'architecture', 'system', 'platform', 'infrastructure', 'devops']
        
        # Count matches for each context
        ai_ml_score = sum(1 for keyword in ai_ml_keywords if keyword in job_title_lower)
        data_score = sum(1 for keyword in data_keywords if keyword in job_title_lower)
        dev_score = sum(1 for keyword in dev_keywords if keyword in job_title_lower)
        
        # Return the context with highest score
        scores = {
            'ai_ml': ai_ml_score,
            'data_analytics': data_score,
            'development': dev_score
        }
        
        max_score = max(scores.values())
        if max_score > 0:
            return max(scores, key=scores.get)
        
        # Default to collaboration for project/product management roles
        return 'collaboration'
    
    @staticmethod
    def generate_filename(job_title: str, software_list: List[str], company: str = "", file_type: str = "cv") -> str:
        """Generate filename in format: PedroHerrera_[ROLE]_[SOFTWARE]_[MODEL]_2025.[ext]"""
        role_initials = NamingUtils.extract_role_initials(job_title)
        software_category = NamingUtils.extract_software_category(software_list)
        business_model = NamingUtils.extract_business_model(job_title, company)
        
        if file_type == "cover_letter":
            return f"PedroHerrera_{role_initials}_{software_category}_{business_model}_2025_CoverLetter.txt"
        else:
            return f"PedroHerrera_{role_initials}_{software_category}_{business_model}_2025.docx"
    
    @staticmethod
    def generate_folder_name(job_title: str, software_list: List[str]) -> str:
        """Generate folder name in format: [Role] - [Specialization] - [Top Software]"""
        # Extract main role directly from job title
        job_title_lower = job_title.lower()
        
        # Check for specific roles first
        if 'product owner' in job_title_lower:
            main_role = "Product Owner"
        elif 'product manager' in job_title_lower:
            main_role = "Product Manager"
        elif 'product analyst' in job_title_lower:
            main_role = "Product Analyst"
        elif 'data analyst' in job_title_lower:
            main_role = "Data Analyst"
        elif 'data scientist' in job_title_lower:
            main_role = "Data Scientist"
        elif 'business analyst' in job_title_lower:
            main_role = "Business Analyst"
        elif 'marketing manager' in job_title_lower:
            main_role = "Marketing Manager"
        elif 'sales manager' in job_title_lower:
            main_role = "Sales Manager"
        elif 'engineering manager' in job_title_lower:
            main_role = "Engineering Manager"
        elif 'software engineer' in job_title_lower:
            main_role = "Software Engineer"
        elif 'ui/ux designer' in job_title_lower or 'product designer' in job_title_lower:
            main_role = "Product Designer"
        else:
            # Fallback to role mapping
            role_initials = NamingUtils.extract_role_initials(job_title)
            role_mapping = {v: k.title() for k, v in NamingUtils.ROLE_ABBREVIATIONS.items()}
            main_role = role_mapping.get(role_initials, "Product Manager")
        
        # Extract specialization
        specialization = NamingUtils.get_specialization(job_title)
        
        # Get top software from different categories, prioritizing role-specific software
        top_software = NamingUtils.get_top_software_by_category(software_list, job_title)
        
        if top_software:
            software_str = ", ".join(top_software)
        else:
            software_str = "General Tools"
        
        # Clean up folder name to avoid path issues
        clean_specialization = specialization.replace('/', ' ').replace('\\', ' ')
        clean_software = software_str.replace('/', ' ').replace('\\', ' ')
        
        return f"{main_role} - {clean_specialization} - {clean_software}"

    @staticmethod
    def find_most_recent_cv_folder(output_path: Path, base_filename: str) -> Path:
        """Find the most recent folder containing a CV with the same base filename"""
        if not output_path.exists():
            return output_path
        
        # Remove extension and get base name
        base_name = base_filename.replace('.docx', '').replace('_CoverLetter.txt', '')
        
        most_recent_folder = None
        most_recent_time = 0
        
        # Search through all subdirectories
        for folder in output_path.iterdir():
            if folder.is_dir():
                # Look for DOCX files in this folder
                for file in folder.glob('*.docx'):
                    if base_name in file.name:
                        # Check if this file is more recent
                        file_time = file.stat().st_mtime
                        if file_time > most_recent_time:
                            most_recent_time = file_time
                            most_recent_folder = folder
        
        # Return the most recent folder, or create a new one if none found
        if most_recent_folder:
            return most_recent_folder
        else:
            return output_path
