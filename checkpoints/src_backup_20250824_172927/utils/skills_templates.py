"""
Role-specific skills templates for high-quality CV generation
Ensures consistent, professional skills across all roles
"""

# High-quality skills templates by role type
ROLE_SKILLS_TEMPLATES = {
    # AI/ML Roles
    'ai_ml': {
        'core_skills': [
            "Project Management, Agile (Scrum, Kanban), Stakeholder Management, Cross-functional Collaboration",
            "Machine Learning Project Management, Data Science Coordination, AI Development Leadership",
            "Technical Project Management, AI/ML Strategy, Innovation Leadership, Research Coordination"
        ],
        'technical_skills': [
            "Python, Azure Machine Learning, TensorFlow, PyTorch, Excel (advanced), Agile tools (Jira, Confluence, Slack)",
            "Python, Machine Learning frameworks, Data Analysis tools, Cloud platforms (AWS/Azure), Jira, Confluence",
            "Python, AI/ML frameworks, Data Engineering tools, MLOps platforms, Project Management tools"
        ]
    },
    
    # Product Management
    'product': {
        'core_skills': [
            "Product Strategy, Roadmap Planning, Stakeholder Management, Cross-functional Leadership",
            "Product Management, Agile (Scrum, Kanban), User Experience Design, Market Analysis",
            "Product Strategy, Go-to-Market Planning, Customer Development, Business Development"
        ],
        'technical_skills': [
            "Figma, Adobe Creative Suite, InVision, Miro, Slack, Jira, Confluence, Google Analytics",
            "Product Analytics tools, Design tools, A/B Testing platforms, Project Management tools",
            "Customer Research tools, Analytics platforms, Design systems, Collaboration tools"
        ]
    },
    
    # Data Science/Analytics
    'data': {
        'core_skills': [
            "Data Strategy, Analytics Leadership, Statistical Analysis, Business Intelligence",
            "Data Science Project Management, Machine Learning Coordination, Statistical Modeling",
            "Data Analytics, Business Intelligence, Statistical Analysis, Data-Driven Decision Making"
        ],
        'technical_skills': [
            "Python, R, SQL, Tableau, Power BI, Excel (advanced), Jira, Confluence",
            "Python, Machine Learning libraries, Statistical software, Data visualization tools",
            "SQL, Python, R, Business Intelligence tools, Statistical analysis software"
        ]
    },
    
    # Construction/Engineering
    'construction': {
        'core_skills': [
            "Construction Project Management, Site Coordination, Safety Management, Regulatory Compliance",
            "Engineering Project Management, Technical Coordination, Quality Control, Risk Management",
            "Infrastructure Project Management, Construction Planning, Safety Leadership, Compliance Management"
        ],
        'technical_skills': [
            "AutoCAD, Primavera, Microsoft Project, Safety software, Excel (advanced), Project Management tools",
            "CAD software, Project planning tools, Safety management systems, Quality control software",
            "Construction management software, CAD tools, Safety platforms, Project scheduling tools"
        ]
    },
    
    # Healthcare/Pharma
    'healthcare': {
        'core_skills': [
            "Clinical Project Management, Regulatory Compliance, Healthcare Operations, Patient Safety",
            "Healthcare Project Management, Clinical Trial Coordination, Regulatory Affairs, Quality Assurance",
            "Medical Device Project Management, Clinical Research, Regulatory Compliance, Healthcare Innovation"
        ],
        'technical_skills': [
            "Clinical trial management systems, Regulatory software, Healthcare databases, Excel (advanced)",
            "Clinical data management, Regulatory platforms, Healthcare analytics, Project management tools",
            "Medical device software, Clinical research platforms, Regulatory compliance tools"
        ]
    },
    
    # Finance/Banking
    'finance': {
        'core_skills': [
            "Financial Project Management, Risk Management, Compliance, Investment Analysis",
            "Financial Operations, Risk Assessment, Regulatory Compliance, Portfolio Management",
            "Banking Project Management, Financial Analysis, Risk Control, Compliance Management"
        ],
        'technical_skills': [
            "Bloomberg Terminal, Excel (advanced), Financial modeling software, Risk management platforms",
            "Financial analysis tools, Risk assessment software, Compliance platforms, Project management tools",
            "Banking systems, Financial software, Risk management tools, Compliance platforms"
        ]
    },
    
    # Manufacturing
    'manufacturing': {
        'core_skills': [
            "Manufacturing Project Management, Process Improvement, Quality Control, Supply Chain Management",
            "Production Planning, Lean Manufacturing, Six Sigma, Operational Excellence",
            "Manufacturing Operations, Process Optimization, Quality Management, Supply Chain Coordination"
        ],
        'technical_skills': [
            "ERP systems, Manufacturing software, Quality management platforms, Excel (advanced)",
            "Production planning tools, Lean software, Quality control systems, Project management tools",
            "Manufacturing execution systems, Process optimization software, Quality platforms"
        ]
    },
    
    # IT/Technology
    'it_tech': {
        'core_skills': [
            "IT Project Management, Software Development Coordination, Technical Leadership, Digital Transformation",
            "Technology Project Management, Software Development, System Integration, Technical Strategy",
            "IT Operations Management, Software Development Leadership, Technical Architecture, Digital Innovation"
        ],
        'technical_skills': [
            "Jira, Confluence, Git, AWS/Azure, Docker, Kubernetes, Excel (advanced), Project management tools",
            "Development tools, Cloud platforms, DevOps tools, Project management software",
            "IT management tools, Development platforms, Cloud services, Project coordination software"
        ]
    },
    
    # General/Default
    'general': {
        'core_skills': [
            "Project Management, Agile (Scrum, Kanban), Stakeholder Management, Cross-functional Collaboration",
            "Strategic Planning, Team Leadership, Process Improvement, Change Management",
            "Project Leadership, Strategic Execution, Team Management, Operational Excellence"
        ],
        'technical_skills': [
            "Microsoft Office Suite, Project Management tools, Excel (advanced), Collaboration platforms",
            "Business software, Project management platforms, Analytics tools, Communication tools",
            "Office productivity tools, Project coordination software, Business intelligence tools"
        ]
    }
}

def detect_role_type(job_title: str, company: str = "", skills: list = None) -> str:
    """Detect role type from job title and context"""
    job_title_lower = job_title.lower()
    company_lower = company.lower() if company else ""
    
    # AI/ML detection
    if any(keyword in job_title_lower for keyword in [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 
        'computer vision', 'natural language', 'nlp', 'data science', 'neural'
    ]):
        return 'ai_ml'
    
    # Product Management detection
    if any(keyword in job_title_lower for keyword in [
        'product manager', 'product owner', 'product lead', 'product director',
        'product strategy', 'product development'
    ]):
        return 'product'
    
    # Data Science/Analytics detection
    if any(keyword in job_title_lower for keyword in [
        'data scientist', 'data analyst', 'analytics', 'business intelligence',
        'data engineer', 'statistical', 'bi analyst'
    ]):
        return 'data'
    
    # Construction/Engineering detection
    if any(keyword in job_title_lower for keyword in [
        'construction', 'civil engineer', 'architect', 'site manager',
        'infrastructure', 'building', 'structural'
    ]):
        return 'construction'
    
    # Healthcare/Pharma detection
    if any(keyword in job_title_lower for keyword in [
        'healthcare', 'medical', 'pharmaceutical', 'clinical', 'biotech',
        'patient', 'clinical trial', 'medical device'
    ]) or any(keyword in company_lower for keyword in ['hospital', 'clinic', 'pharma', 'medical']):
        return 'healthcare'
    
    # Finance/Banking detection
    if any(keyword in job_title_lower for keyword in [
        'finance', 'financial', 'banking', 'investment', 'risk',
        'portfolio', 'trading', 'compliance'
    ]) or any(keyword in company_lower for keyword in ['bank', 'financial', 'investment']):
        return 'finance'
    
    # Manufacturing detection
    if any(keyword in job_title_lower for keyword in [
        'manufacturing', 'production', 'industrial', 'factory', 'plant',
        'operations', 'supply chain', 'logistics'
    ]):
        return 'manufacturing'
    
    # IT/Technology detection
    if any(keyword in job_title_lower for keyword in [
        'it', 'technology', 'software', 'digital', 'tech', 'systems',
        'development', 'programming', 'technical'
    ]):
        return 'it_tech'
    
    # Default to general
    return 'general'

def get_skills_template(role_type: str) -> dict:
    """Get skills template for a specific role type"""
    return ROLE_SKILLS_TEMPLATES.get(role_type, ROLE_SKILLS_TEMPLATES['general'])

def generate_high_quality_skills(job_title: str, company: str = "", skills: list = None, 
                                use_llm: bool = True) -> tuple:
    """
    Generate high-quality skills for any role
    
    Returns:
        tuple: (core_skills, technical_skills)
    """
    # Detect role type
    role_type = detect_role_type(job_title, company, skills)
    
    # Get template
    template = get_skills_template(role_type)
    
    # Select appropriate skills based on context
    import random
    
    # Choose core skills (prefer first option, but can randomize)
    core_skills = template['core_skills'][0] if template['core_skills'] else ""
    
    # Choose technical skills (prefer first option, but can randomize)
    technical_skills = template['technical_skills'][0] if template['technical_skills'] else ""
    
    return core_skills, technical_skills

def get_role_specific_skills(job_title: str, company: str = "", skills: list = None) -> str:
    """Get complete skills section for a role"""
    core_skills, technical_skills = generate_high_quality_skills(job_title, company, skills)
    
    if core_skills and technical_skills:
        return f"{core_skills}. {technical_skills}."
    elif core_skills:
        return core_skills
    elif technical_skills:
        return technical_skills
    else:
        return "Project Management, Leadership, Communication, Strategic Planning, Team Management"
