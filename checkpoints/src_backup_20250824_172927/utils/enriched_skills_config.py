"""
Enriched skills configuration for CVPilot
Based on analysis of Project Manager job descriptions
"""

# Enriched skills based on PM analysis
ENRICHED_PM_SKILLS = {
    'project_management': [
        # Core PM skills (high frequency)
        'project management', 'gestión de proyectos', 'project planning', 'project execution',
        'project coordination', 'project delivery', 'project governance', 'project lifecycle',
        'project monitoring', 'project control', 'project leadership', 'project oversight',
        
        # Advanced PM skills
        'project portfolio management', 'program management', 'project risk management',
        'project quality management', 'project scope management', 'project time management',
        'project cost management', 'project stakeholder management', 'project communication management',
        'project procurement management', 'project integration management', 'project human resource management'
    ],
    
    'methodologies': [
        # Agile methodologies (high frequency)
        'agile', 'scrum', 'kanban', 'sprint planning', 'backlog management', 'retrospective',
        'daily standup', 'sprint review', 'sprint retrospective', 'agile ceremonies',
        
        # Traditional methodologies
        'waterfall', 'prince2', 'pmi', 'pmp', 'ipma', 'lean', 'six sigma', 'lean six sigma',
        
        # Hybrid and modern approaches
        'scaled agile', 'safe', 'less', 'nexus', 'crystal', 'xp', 'fdd', 'dsdm',
        'methodology', 'framework', 'best practices', 'process improvement'
    ],
    
    'leadership': [
        # Leadership skills (high frequency)
        'leadership', 'liderazgo', 'team leadership', 'team management', 'team coordination',
        'cross-functional leadership', 'multidisciplinary leadership', 'stakeholder leadership',
        
        # Team management
        'team building', 'team development', 'team motivation', 'team performance',
        'conflict resolution', 'decision making', 'mentoring', 'coaching', 'people management',
        
        # Stakeholder management
        'stakeholder management', 'stakeholder engagement', 'stakeholder communication',
        'stakeholder alignment', 'stakeholder influence', 'relationship management',
        
        # Strategic leadership
        'strategic thinking', 'strategic planning', 'vision setting', 'goal setting',
        'change management', 'transformation leadership', 'executive communication'
    ],
    
    'communication': [
        # Communication skills (high frequency)
        'communication', 'comunicación', 'presentation', 'reporting', 'documentation',
        'technical writing', 'business writing', 'client communication', 'stakeholder communication',
        
        # Advanced communication
        'negotiation', 'facilitation', 'meeting management', 'presentation skills',
        'public speaking', 'interpersonal communication', 'cross-cultural communication',
        'written communication', 'verbal communication', 'non-verbal communication',
        
        # Business communication
        'executive reporting', 'status reporting', 'progress reporting', 'risk reporting',
        'project reporting', 'stakeholder reporting', 'board communication', 'client presentations'
    ],
    
    'technical': [
        # Technical skills (high frequency)
        'technical', 'engineering', 'it', 'technology', 'software development', 'development',
        'technical analysis', 'technical documentation', 'technical coordination',
        
        # Software development
        'programming', 'coding', 'software architecture', 'system design', 'technical design',
        'technical specifications', 'technical requirements', 'technical implementation',
        
        # IT and systems
        'it project management', 'software project management', 'system integration',
        'technical project management', 'technology management', 'digital transformation',
        'technical leadership', 'technical strategy', 'technical planning'
    ],
    
    'analytical': [
        # Analytical skills
        'analytical', 'analysis', 'data analysis', 'problem solving', 'critical thinking',
        'strategic thinking', 'risk management', 'risk assessment', 'quality management',
        'process improvement', 'optimization', 'efficiency', 'performance analysis',
        
        # Advanced analytics
        'business analysis', 'requirements analysis', 'gap analysis', 'root cause analysis',
        'impact analysis', 'feasibility analysis', 'cost-benefit analysis', 'swot analysis',
        'data-driven decision making', 'metrics analysis', 'kpi analysis', 'performance metrics'
    ],
    
    'business': [
        # Business skills (high frequency)
        'business', 'commercial', 'financial', 'budget', 'cost management', 'resource management',
        'business strategy', 'business development', 'market analysis', 'competitive analysis',
        'business intelligence', 'kpis', 'metrics', 'roi', 'business case',
        
        # Financial management
        'budget management', 'cost control', 'financial planning', 'financial analysis',
        'resource allocation', 'financial reporting', 'cost estimation', 'budget forecasting',
        
        # Strategic business
        'business planning', 'business operations', 'business process', 'business transformation',
        'market research', 'competitive intelligence', 'business modeling', 'business optimization'
    ],
    
    'tools': [
        # Project management tools (high frequency)
        'jira', 'confluence', 'microsoft project', 'ms project', 'primavera', 'autocad',
        'sharepoint', 'slack', 'teams', 'zoom', 'notion', 'asana', 'trello', 'monday.com',
        'excel', 'powerpoint', 'word', 'office', 'erp', 'crm', 'bi tools', 'dashboard',
        
        # Advanced tools
        'azure devops', 'git', 'github', 'bitbucket', 'jenkins', 'docker', 'kubernetes',
        'aws', 'azure', 'gcp', 'salesforce', 'hubspot', 'tableau', 'power bi', 'looker',
        'mixpanel', 'amplitude', 'google analytics', 'hotjar', 'fullstory', 'optimizely'
    ],
    
    'industry_specific': [
        # Industry domains
        'construction', 'manufacturing', 'logistics', 'supply chain', 'retail', 'ecommerce',
        'healthcare', 'pharmaceutical', 'automotive', 'aerospace', 'energy', 'telecommunications',
        'banking', 'finance', 'insurance', 'real estate', 'hospitality', 'tourism',
        'education', 'government', 'non-profit', 'consulting', 'technology', 'media',
        'entertainment', 'gaming', 'sports', 'fashion', 'food', 'beverage'
    ],
    
    'soft_skills': [
        # Soft skills (high frequency)
        'organization', 'planning', 'time management', 'prioritization', 'multitasking',
        'attention to detail', 'proactive', 'self-motivated', 'autonomous', 'flexible',
        'adaptable', 'resilient', 'collaborative', 'team player', 'customer oriented',
        'results oriented', 'goal oriented', 'achievement oriented',
        
        # Advanced soft skills
        'emotional intelligence', 'empathy', 'active listening', 'patience', 'perseverance',
        'creativity', 'innovation', 'problem solving', 'critical thinking', 'analytical thinking',
        'strategic thinking', 'systems thinking', 'design thinking', 'lean thinking',
        'continuous learning', 'adaptability', 'flexibility', 'resilience', 'stress management'
    ]
}

# Skills priority mapping based on frequency analysis
SKILLS_PRIORITY = {
    'high_priority': [
        'project management', 'gestión de proyectos', 'it', 'communication', 'comunicación',
        'leadership', 'liderazgo', 'agile', 'scrum', 'excel', 'jira', 'confluence',
        'stakeholder management', 'team management', 'planning', 'time management'
    ],
    
    'medium_priority': [
        'project planning', 'project execution', 'kanban', 'pmp', 'prince2', 'engineering',
        'development', 'technology', 'business', 'analytical', 'problem solving',
        'flexible', 'organization', 'prioritization', 'office', 'erp'
    ],
    
    'low_priority': [
        'waterfall', 'lean', 'six sigma', 'technical writing', 'presentation',
        'negotiation', 'facilitation', 'meeting management', 'multitasking',
        'attention to detail', 'proactive', 'self-motivated', 'autonomous'
    ]
}

# Skills by seniority level
SKILLS_BY_SENIORITY = {
    'junior': [
        'project coordination', 'planning', 'organization', 'time management',
        'excel', 'office', 'communication', 'team player', 'learning', 'adaptable'
    ],
    
    'mid': [
        'project management', 'gestión de proyectos', 'agile', 'scrum', 'jira',
        'stakeholder management', 'team management', 'analytical', 'problem solving',
        'leadership', 'liderazgo', 'flexible', 'prioritization'
    ],
    
    'senior': [
        'project leadership', 'strategic thinking', 'stakeholder leadership',
        'change management', 'mentoring', 'coaching', 'business strategy',
        'risk management', 'quality management', 'process improvement'
    ],
    
    'manager': [
        'program management', 'portfolio management', 'executive communication',
        'strategic planning', 'business development', 'transformation leadership',
        'team development', 'performance management', 'resource allocation'
    ]
}

# Skills by industry specialization
SKILLS_BY_INDUSTRY = {
    'it_technology': [
        'software development', 'it project management', 'technical leadership',
        'system integration', 'digital transformation', 'agile', 'scrum', 'jira',
        'confluence', 'git', 'aws', 'azure', 'docker', 'kubernetes'
    ],
    
    'construction_engineering': [
        'construction management', 'engineering project management', 'autocad',
        'primavera', 'construction planning', 'site management', 'quality control',
        'safety management', 'regulatory compliance'
    ],
    
    'manufacturing': [
        'manufacturing project management', 'lean', 'six sigma', 'process improvement',
        'quality management', 'supply chain', 'logistics', 'erp', 'production planning',
        'inventory management'
    ],
    
    'healthcare_pharma': [
        'healthcare project management', 'regulatory compliance', 'fda compliance',
        'clinical trials', 'medical device', 'pharmaceutical', 'quality assurance',
        'risk management', 'documentation'
    ],
    
    'finance_banking': [
        'financial project management', 'budget management', 'cost control',
        'financial analysis', 'compliance', 'risk management', 'regulatory reporting',
        'business intelligence', 'kpis', 'metrics'
    ]
}

def get_skills_by_category(category: str) -> list:
    """Get skills for a specific category"""
    return ENRICHED_PM_SKILLS.get(category, [])

def get_priority_skills(priority: str) -> list:
    """Get skills by priority level"""
    return SKILLS_PRIORITY.get(priority, [])

def get_skills_by_seniority(seniority: str) -> list:
    """Get skills appropriate for seniority level"""
    return SKILLS_BY_SENIORITY.get(seniority, [])

def get_skills_by_industry(industry: str) -> list:
    """Get skills specific to industry"""
    return SKILLS_BY_INDUSTRY.get(industry, [])

def get_all_skills() -> list:
    """Get all skills from all categories"""
    all_skills = []
    for category_skills in ENRICHED_PM_SKILLS.values():
        all_skills.extend(category_skills)
    return list(set(all_skills))  # Remove duplicates

def get_skills_for_role(job_title: str, seniority: str = None, industry: str = None) -> list:
    """Get relevant skills for a specific role"""
    skills = []
    
    # Add base PM skills
    skills.extend(get_priority_skills('high_priority'))
    
    # Add seniority-specific skills
    if seniority:
        skills.extend(get_skills_by_seniority(seniority))
    
    # Add industry-specific skills
    if industry:
        skills.extend(get_skills_by_industry(industry))
    
    # Add role-specific skills based on job title
    job_title_lower = job_title.lower()
    
    if 'technical' in job_title_lower or 'it' in job_title_lower:
        skills.extend(get_skills_by_industry('it_technology'))
    
    if 'construction' in job_title_lower or 'engineering' in job_title_lower:
        skills.extend(get_skills_by_industry('construction_engineering'))
    
    if 'manufacturing' in job_title_lower or 'production' in job_title_lower:
        skills.extend(get_skills_by_industry('manufacturing'))
    
    if 'healthcare' in job_title_lower or 'medical' in job_title_lower:
        skills.extend(get_skills_by_industry('healthcare_pharma'))
    
    if 'finance' in job_title_lower or 'banking' in job_title_lower:
        skills.extend(get_skills_by_industry('finance_banking'))
    
    return list(set(skills))  # Remove duplicates
