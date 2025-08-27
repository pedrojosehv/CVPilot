"""
Naming validation utilities for CVPilot
Compares generated naming with actual job descriptions to validate accuracy
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from .logger import LoggerMixin
import re

class NamingValidator(LoggerMixin):
    """Validates naming accuracy by comparing with actual job descriptions"""
    
    def __init__(self, datapm_path: Path):
        super().__init__()
        self.datapm_path = datapm_path
        self.processed_path = datapm_path / "csv" / "src" / "csv_processed"
        self.scrapped_path = datapm_path / "csv" / "src" / "scrapped"
    
    def find_job_description(self, job_title: str, company: str) -> Optional[Dict]:
        """Find job description in DataPM processed files"""
        self.log_info(f"🔍 Searching for job: '{job_title}' at '{company}'")
        
        # Search in processed files first
        for csv_file in self.processed_path.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                if 'Job title (original)' in df.columns and 'Company' in df.columns:
                    for _, row in df.iterrows():
                        if (job_title.lower() in str(row['Job title (original)']).lower() and 
                            company.lower() in str(row['Company']).lower()):
                            return {
                                'source': 'processed',
                                'file': csv_file.name,
                                'job_title': row['Job title (original)'],
                                'company': row['Company'],
                                'skills': row.get('Skills', ''),
                                'software': row.get('Software', ''),
                                'seniority': row.get('Seniority', ''),
                                'experience': row.get('Experience years', ''),
                                'degrees': row.get('Degrees', '')
                            }
            except Exception as e:
                self.log_warning(f"Error reading {csv_file}: {e}")
        
        # Search in scrapped files for full description
        for csv_file in self.scrapped_path.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)
                if 'Job title' in df.columns and 'Company' in df.columns:
                    for _, row in df.iterrows():
                        if (job_title.lower() in str(row['Job title']).lower() and 
                            company.lower() in str(row['Company']).lower()):
                            return {
                                'source': 'scrapped',
                                'file': csv_file.name,
                                'job_title': row['Job title'],
                                'company': row['Company'],
                                'description': row.get('Description', ''),
                                'location': row.get('Location', '')
                            }
            except Exception as e:
                self.log_warning(f"Error reading {csv_file}: {e}")
        
        return None
    
    def extract_keywords_from_description(self, description: str) -> Dict[str, List[str]]:
        """Extract relevant keywords from job description"""
        if not description:
            return {}
        
        description_lower = description.lower()
        
        # Define keyword categories
        keywords = {
            'ai_ml': ['artificial intelligence', 'machine learning', 'deep learning', 'neural networks', 
                     'computer vision', 'vision artificial', 'ai', 'ml', 'tensorflow', 'pytorch', 
                     'opencv', 'scikit-learn', 'keras', 'nlp', 'natural language processing'],
            'programming': ['python', 'c++', 'java', 'javascript', 'sql', 'r', 'matlab', 'scala', 'go'],
            'tools': ['jira', 'confluence', 'figma', 'slack', 'teams', 'zoom', 'notion', 'asana', 'trello'],
            'analytics': ['google analytics', 'mixpanel', 'amplitude', 'tableau', 'power bi', 'looker'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git'],
            'methodologies': ['agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma']
        }
        
        found_keywords = {}
        for category, terms in keywords.items():
            found = []
            for term in terms:
                if term in description_lower:
                    found.append(term)
            if found:
                found_keywords[category] = found
        
        return found_keywords
    
    def validate_naming_accuracy(self, job_title: str, company: str, generated_folder: str, 
                                generated_filename: str) -> Dict:
        """Validate the accuracy of generated naming against actual job description"""
        
        self.log_info(f"🔍 Validating naming accuracy for: {job_title} at {company}")
        
        # Find job description
        job_data = self.find_job_description(job_title, company)
        if not job_data:
            return {
                'status': 'error',
                'message': f'Job description not found for {job_title} at {company}',
                'accuracy_score': 0
            }
        
        # Extract keywords from description
        description_keywords = {}
        if job_data['source'] == 'scrapped' and 'description' in job_data:
            description_keywords = self.extract_keywords_from_description(job_data['description'])
        
        # Extract software from processed data
        actual_software = []
        if job_data['source'] == 'processed' and 'software' in job_data:
            software_str = str(job_data['software'])
            if software_str and software_str != 'nan':
                actual_software = [s.strip() for s in software_str.split(';') if s.strip()]
        
        # Extract skills from processed data
        actual_skills = []
        if job_data['source'] == 'processed' and 'skills' in job_data:
            skills_str = str(job_data['skills'])
            if skills_str and skills_str != 'nan':
                actual_skills = [s.strip() for s in skills_str.split(';') if s.strip()]
        
        # Analyze generated naming
        generated_analysis = self.analyze_generated_naming(generated_folder, generated_filename)
        
        # Calculate accuracy metrics
        accuracy_metrics = self.calculate_accuracy_metrics(
            actual_software, actual_skills, description_keywords, generated_analysis
        )
        
        return {
            'status': 'success',
            'job_data': job_data,
            'description_keywords': description_keywords,
            'actual_software': actual_software,
            'actual_skills': actual_skills,
            'generated_analysis': generated_analysis,
            'accuracy_metrics': accuracy_metrics,
            'accuracy_score': accuracy_metrics['overall_score']
        }
    
    def analyze_generated_naming(self, folder_name: str, filename: str) -> Dict:
        """Analyze the generated folder name and filename"""
        
        # Extract software from folder name
        folder_software = []
        if ' - ' in folder_name:
            parts = folder_name.split(' - ')
            if len(parts) >= 3:
                software_part = parts[2]
                folder_software = [s.strip() for s in software_part.split(',') if s.strip()]
        
        # Extract category from filename
        filename_category = "Unknown"
        if '_' in filename:
            parts = filename.split('_')
            if len(parts) >= 3:
                filename_category = parts[2]  # e.g., AIML, ANAL, CODE
        
        return {
            'folder_software': folder_software,
            'filename_category': filename_category,
            'folder_name': folder_name,
            'filename': filename
        }
    
    def calculate_accuracy_metrics(self, actual_software: List[str], actual_skills: List[str], 
                                 description_keywords: Dict, generated_analysis: Dict) -> Dict:
        """Calculate accuracy metrics for naming validation"""
        
        # Software accuracy
        actual_software_lower = [s.lower() for s in actual_software]
        generated_software_lower = [s.lower() for s in generated_analysis['folder_software']]
        
        software_matches = 0
        software_total = len(actual_software_lower)
        
        for gen_sw in generated_software_lower:
            for act_sw in actual_software_lower:
                if gen_sw in act_sw or act_sw in gen_sw:
                    software_matches += 1
                    break
        
        software_accuracy = software_matches / max(software_total, 1)
        
        # Category accuracy
        category_accuracy = 0
        if generated_analysis['filename_category'] == 'AIML':
            # Check if AI/ML keywords are present
            ai_ml_keywords = description_keywords.get('ai_ml', [])
            if ai_ml_keywords:
                category_accuracy = 1.0
        elif generated_analysis['filename_category'] == 'ANAL':
            # Check if analytics keywords are present
            analytics_keywords = description_keywords.get('analytics', [])
            if analytics_keywords:
                category_accuracy = 1.0
        elif generated_analysis['filename_category'] == 'CODE':
            # Check if programming keywords are present
            programming_keywords = description_keywords.get('programming', [])
            if programming_keywords:
                category_accuracy = 1.0
        
        # Overall score (weighted average)
        overall_score = (software_accuracy * 0.7) + (category_accuracy * 0.3)
        
        return {
            'software_accuracy': software_accuracy,
            'category_accuracy': category_accuracy,
            'overall_score': overall_score,
            'software_matches': software_matches,
            'software_total': software_total
        }
    
    def generate_validation_report(self, validation_result: Dict) -> str:
        """Generate a detailed validation report"""
        
        if validation_result['status'] != 'success':
            return f"❌ Validation failed: {validation_result['message']}"
        
        job_data = validation_result['job_data']
        accuracy_metrics = validation_result['accuracy_metrics']
        actual_software = validation_result['actual_software']
        generated_analysis = validation_result['generated_analysis']
        
        report = f"""
🔍 **NOMENCLATURE VALIDATION REPORT**
{'='*50}

📋 **JOB DETAILS:**
   • Title: {job_data['job_title']}
   • Company: {job_data['company']}
   • Source: {job_data['source']} ({job_data['file']})

🎯 **GENERATED NAMING:**
   • Folder: {generated_analysis['folder_name']}
   • Filename: {generated_analysis['filename']}
   • Category: {generated_analysis['filename_category']}
   • Software: {', '.join(generated_analysis['folder_software'])}

📊 **ACTUAL JOB DATA:**
   • Software: {', '.join(actual_software) if actual_software else 'None specified'}
   • Skills: {', '.join(validation_result['actual_skills'][:5]) if validation_result['actual_skills'] else 'None specified'}

📈 **ACCURACY METRICS:**
   • Software Accuracy: {accuracy_metrics['software_accuracy']:.1%} ({accuracy_metrics['software_matches']}/{accuracy_metrics['software_total']})
   • Category Accuracy: {accuracy_metrics['category_accuracy']:.1%}
   • Overall Score: {accuracy_metrics['overall_score']:.1%}

🎯 **VALIDATION RESULT:"""
        
        if accuracy_metrics['overall_score'] >= 0.8:
            report += " ✅ EXCELLENT - Naming accurately reflects job requirements"
        elif accuracy_metrics['overall_score'] >= 0.6:
            report += " ⚠️ GOOD - Naming mostly accurate with minor discrepancies"
        elif accuracy_metrics['overall_score'] >= 0.4:
            report += " 🔶 FAIR - Naming partially accurate, room for improvement"
        else:
            report += " ❌ POOR - Naming does not reflect job requirements"
        
        return report
