#!/usr/bin/env python3
"""
Analyze Project Manager skills from scraped jobs data
Extract and categorize skills to enrich our skills schema
"""

import pandas as pd
import re
from collections import Counter
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import LoggerMixin

class PMSkillsAnalyzer(LoggerMixin):
    """Analyze Project Manager skills from scraped job data"""
    
    def __init__(self):
        super().__init__()
        self.skills_patterns = {
            'project_management': [
                'project management', 'gestión de proyectos', 'project manager', 'project planning',
                'project execution', 'project monitoring', 'project control', 'project coordination',
                'project leadership', 'project governance', 'project lifecycle', 'project delivery'
            ],
            'methodologies': [
                'agile', 'scrum', 'kanban', 'waterfall', 'lean', 'six sigma', 'pmi', 'prince2',
                'ipma', 'pmp', 'sprint planning', 'backlog', 'retrospective', 'ceremonies',
                'methodology', 'framework', 'best practices'
            ],
            'leadership': [
                'leadership', 'liderazgo', 'team management', 'team leadership', 'team coordination',
                'cross-functional', 'multidisciplinary', 'stakeholder management', 'stakeholder engagement',
                'mentoring', 'coaching', 'team building', 'conflict resolution', 'decision making'
            ],
            'communication': [
                'communication', 'comunicación', 'presentation', 'reporting', 'documentation',
                'technical writing', 'client communication', 'stakeholder communication',
                'negotiation', 'facilitation', 'meeting management', 'presentation skills'
            ],
            'technical': [
                'technical', 'engineering', 'software development', 'it', 'technology',
                'programming', 'coding', 'development', 'architecture', 'system design',
                'technical analysis', 'technical documentation', 'technical coordination'
            ],
            'analytical': [
                'analytical', 'analysis', 'data analysis', 'problem solving', 'critical thinking',
                'strategic thinking', 'risk management', 'risk assessment', 'quality management',
                'process improvement', 'optimization', 'efficiency', 'performance analysis'
            ],
            'business': [
                'business', 'commercial', 'financial', 'budget', 'cost management', 'resource management',
                'business strategy', 'business development', 'market analysis', 'competitive analysis',
                'business intelligence', 'kpis', 'metrics', 'roi', 'business case'
            ],
            'tools': [
                'jira', 'confluence', 'microsoft project', 'ms project', 'primavera', 'autocad',
                'sharepoint', 'slack', 'teams', 'zoom', 'notion', 'asana', 'trello', 'monday.com',
                'excel', 'powerpoint', 'word', 'office', 'erp', 'crm', 'bi tools', 'dashboard'
            ],
            'industry_specific': [
                'construction', 'manufacturing', 'logistics', 'supply chain', 'retail', 'ecommerce',
                'healthcare', 'pharmaceutical', 'automotive', 'aerospace', 'energy', 'telecommunications',
                'banking', 'finance', 'insurance', 'real estate', 'hospitality', 'tourism'
            ],
            'soft_skills': [
                'organization', 'planning', 'time management', 'prioritization', 'multitasking',
                'attention to detail', 'proactive', 'self-motivated', 'autonomous', 'flexible',
                'adaptable', 'resilient', 'collaborative', 'team player', 'customer oriented',
                'results oriented', 'goal oriented', 'achievement oriented'
            ]
        }
    
    def load_scraped_data(self, file_path: str) -> pd.DataFrame:
        """Load scraped job data"""
        try:
            df = pd.read_csv(file_path)
            self.log_info(f"Loaded {len(df)} jobs from {file_path}")
            return df
        except Exception as e:
            self.log_error(f"Error loading {file_path}: {e}")
            return pd.DataFrame()
    
    def extract_skills_from_description(self, description: str) -> dict:
        """Extract skills from job description"""
        if not description or pd.isna(description):
            return {}
        
        description_lower = description.lower()
        extracted_skills = {}
        
        for category, patterns in self.skills_patterns.items():
            found_skills = []
            for pattern in patterns:
                if pattern in description_lower:
                    found_skills.append(pattern)
            if found_skills:
                extracted_skills[category] = found_skills
        
        return extracted_skills
    
    def analyze_pm_skills(self, file_path: str) -> dict:
        """Analyze Project Manager skills from scraped data"""
        df = self.load_scraped_data(file_path)
        if df.empty:
            return {}
        
        # Filter for Project Manager roles
        pm_jobs = df[df['title'].str.contains('project manager|gestor|jefe de proyecto', case=False, na=False)]
        self.log_info(f"Found {len(pm_jobs)} Project Manager jobs")
        
        all_skills = {}
        skill_counts = Counter()
        
        for _, job in pm_jobs.iterrows():
            skills = self.extract_skills_from_description(job.get('description', ''))
            
            # Aggregate skills by category
            for category, skill_list in skills.items():
                if category not in all_skills:
                    all_skills[category] = []
                all_skills[category].extend(skill_list)
                skill_counts.update(skill_list)
        
        return {
            'skills_by_category': all_skills,
            'skill_frequency': dict(skill_counts.most_common()),
            'total_jobs_analyzed': len(pm_jobs)
        }
    
    def generate_skills_report(self, analysis_result: dict) -> str:
        """Generate a comprehensive skills analysis report"""
        if not analysis_result:
            return "No analysis results available"
        
        report = f"""
🔍 **PROJECT MANAGER SKILLS ANALYSIS REPORT**
{'='*60}

📊 **ANALYSIS SUMMARY:**
   • Total Project Manager jobs analyzed: {analysis_result['total_jobs_analyzed']}
   • Skills categories identified: {len(analysis_result['skills_by_category'])}
   • Unique skills found: {len(analysis_result['skill_frequency'])}

📈 **SKILLS BY CATEGORY:**
"""
        
        for category, skills in analysis_result['skills_by_category'].items():
            unique_skills = list(set(skills))
            report += f"\n🎯 **{category.upper().replace('_', ' ')}** ({len(unique_skills)} skills):\n"
            for skill in unique_skills[:10]:  # Show top 10 per category
                count = skills.count(skill)
                report += f"   • {skill} ({count} mentions)\n"
        
        report += f"\n🏆 **TOP 20 MOST FREQUENT SKILLS:**\n"
        for skill, count in list(analysis_result['skill_frequency'].items())[:20]:
            report += f"   • {skill}: {count} mentions\n"
        
        return report
    
    def suggest_schema_improvements(self, analysis_result: dict) -> str:
        """Suggest improvements to the skills schema based on analysis"""
        if not analysis_result:
            return "No analysis results available"
        
        suggestions = f"""
💡 **SCHEMA IMPROVEMENT SUGGESTIONS**
{'='*50}

🎯 **HIGH-PRIORITY SKILLS TO ADD:**
"""
        
        # Get top skills that might be missing from current schema
        top_skills = list(analysis_result['skill_frequency'].items())[:15]
        
        for skill, count in top_skills:
            if count >= 3:  # Skills mentioned 3+ times
                suggestions += f"   • {skill} ({count} mentions)\n"
        
        suggestions += f"""
📋 **CATEGORY EXPANSIONS:**
"""
        
        for category, skills in analysis_result['skills_by_category'].items():
            if len(skills) >= 5:  # Categories with 5+ skills
                suggestions += f"   • {category}: Expand with {len(skills)} identified skills\n"
        
        return suggestions

def main():
    analyzer = PMSkillsAnalyzer()
    
    # Analyze the scraped file
    file_path = "D:/Work Work/Upwork/DataPM/csv/src/scrapped/20250822_102751_linkedin_jobs.csv"
    
    print("🔍 Analyzing Project Manager skills from scraped data...")
    analysis_result = analyzer.analyze_pm_skills(file_path)
    
    if analysis_result:
        # Generate and display report
        report = analyzer.generate_skills_report(analysis_result)
        print(report)
        
        # Generate suggestions
        suggestions = analyzer.suggest_schema_improvements(analysis_result)
        print(suggestions)
        
        # Save detailed results
        output_file = "pm_skills_analysis.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
            f.write("\n" + suggestions)
        
        print(f"\n📄 Detailed analysis saved to: {output_file}")
    else:
        print("❌ No analysis results generated")

if __name__ == "__main__":
    main()
