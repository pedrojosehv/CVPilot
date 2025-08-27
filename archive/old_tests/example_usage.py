#!/usr/bin/env python3
"""
Example usage of CVPilot
"""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config import Config
from utils.logger import setup_logger
from utils.models import JobData, ProfileType
from ingest.job_loader import JobLoader
from matching.profile_matcher import ProfileMatcher
from generation.content_generator import ContentGenerator
from validation.content_validator import ContentValidator
from template.docx_processor import DocxProcessor

def create_sample_job_data():
    """Create sample job data for demonstration"""
    return JobData(
        job_id="sample_001",
        job_title_original="Senior Product Manager",
        job_title_short="Product Manager",
        company="TechCorp",
        country="Spain",
        state="Madrid",
        city="Madrid",
        schedule_type="full-time",
        experience_years="5+",
        seniority="senior",
        skills=[
            "Product Strategy", "Product Development", "Product Roadmapping",
            "Feature Prioritization", "Market Research", "Competitive Analysis",
            "Product Analytics", "Stakeholder Management", "Cross-functional Collaboration",
            "Communication", "Problem Solving", "Analytical Thinking"
        ],
        degrees=["Bachelor's Degree", "Master's Degree"],
        software=[
            "Jira", "Confluence", "Figma", "Google Analytics", "Mixpanel",
            "Tableau", "Slack", "Microsoft Teams", "Miro", "Trello"
        ]
    )

def main():
    """Main example function"""
    print("🚀 CVPilot Example Usage")
    print("=" * 50)
    
    # Setup
    logger = setup_logger()
    config = Config()
    
    # Create sample job data
    job_data = create_sample_job_data()
    print(f"📋 Sample job: {job_data.job_title_original} at {job_data.company}")
    
    try:
        # Step 1: Match profile
        print("\n🔍 Step 1: Matching profile...")
        matcher = ProfileMatcher(config.profiles_path)
        match_result = matcher.match_job_to_profile(job_data, "product_management")
        print(f"✓ Fit score: {match_result.fit_score:.2f}")
        print(f"✓ Matched skills: {len(match_result.matched_skills)}")
        print(f"✓ Missing skills: {len(match_result.missing_skills)}")
        
        # Step 2: Generate content (without LLM for demo)
        print("\n✍️  Step 2: Generating content...")
        print("⚠️  Note: LLM generation requires API keys. Using fallback content.")
        
        # Create sample replacements
        from utils.models import Replacements, ReplacementBlock
        from datetime import datetime
        
        replacements = Replacements(
            profile_summary=ReplacementBlock(
                placeholder="ProfileSummary",
                content="Experienced Product Manager with 5+ years in SaaS and B2B environments. Proven track record of delivering successful products through data-driven decision making and cross-functional collaboration.",
                confidence=0.8,
                metadata={"word_count": 25}
            ),
            top_bullets=[
                ReplacementBlock(
                    placeholder="TopBullet",
                    content="Led product strategy and roadmap development for SaaS platform, resulting in 25% increase in user engagement and 40% improvement in conversion rates",
                    confidence=0.9,
                    metadata={"length": 120}
                ),
                ReplacementBlock(
                    placeholder="TopBullet",
                    content="Managed cross-functional teams of 8+ members across engineering, design, and marketing to deliver products on time and within budget",
                    confidence=0.85,
                    metadata={"length": 110}
                ),
                ReplacementBlock(
                    placeholder="TopBullet",
                    content="Conducted comprehensive market research and competitive analysis to identify new product opportunities, driving 15% revenue growth",
                    confidence=0.8,
                    metadata={"length": 105}
                ),
                ReplacementBlock(
                    placeholder="TopBullet",
                    content="Implemented data-driven product analytics and A/B testing frameworks, improving conversion rates by 15% and reducing churn by 20%",
                    confidence=0.85,
                    metadata={"length": 115}
                )
            ],
            skill_list=ReplacementBlock(
                placeholder="SkillList",
                content="Product Strategy, Product Development, Roadmapping, Feature Prioritization, Market Research, Competitive Analysis, Product Analytics, Stakeholder Management, Cross-functional Collaboration, Communication, Problem Solving, Analytical Thinking, Business Acumen, Strategic Thinking",
                confidence=0.9,
                metadata={"skill_count": 15, "matched_count": 12}
            ),
            software_list=ReplacementBlock(
                placeholder="SoftwareList",
                content="Jira, Confluence, Figma, Google Analytics, Mixpanel, Tableau, Slack, Microsoft Teams, Miro, Trello",
                confidence=0.9,
                metadata={"software_count": 10, "matched_count": 10}
            ),
            objective_title=ReplacementBlock(
                placeholder="ObjectiveTitle",
                content="Senior Product Manager",
                confidence=0.95,
                metadata={"length": 20}
            ),
            ats_recommendations=ReplacementBlock(
                placeholder="ATSRecommendations",
                content="Optimize keywords: Product Strategy, SaaS, B2B, Data Analytics. Include quantifiable achievements and industry-specific terminology for better ATS scanning.",
                confidence=0.8,
                metadata={"word_count": 20}
            ),
            job_id=job_data.job_id,
            company=job_data.company,
            position=job_data.job_title_original,
            generated_at=datetime.now().isoformat()
        )
        
        # Step 3: Validate content
        print("\n✅ Step 3: Validating content...")
        validator = ContentValidator()
        validation_result = validator.validate_replacements(replacements)
        print(f"✓ Validation passed: {validation_result.is_valid}")
        print(f"✓ Confidence score: {validation_result.confidence_score:.2f}")
        if validation_result.warnings:
            print(f"⚠️  Warnings: {len(validation_result.warnings)}")
        
        # Step 4: Process template
        print("\n📄 Step 4: Processing template...")
        processor = DocxProcessor()
        
        # Validate template first
        template_validation = processor.validate_template(config.default_template_path)
        if template_validation["is_valid"]:
            print("✓ Template validation passed")
            print(f"✓ Found placeholders: {len(template_validation['placeholders_found'])}")
        else:
            print("⚠️  Template validation issues:")
            for error in template_validation["errors"]:
                print(f"  - {error}")
        
        # Generate dry-run preview
        output_path = Path("output")
        output_path.mkdir(exist_ok=True)
        
        preview_file = processor.generate_dry_run(
            config.default_template_path, 
            replacements, 
            output_path
        )
        print(f"✓ Dry-run preview generated: {preview_file}")
        
        # Show preview content
        print("\n📋 Content Preview:")
        print("-" * 30)
        with open(preview_file, 'r', encoding='utf-8') as f:
            preview_content = f.read()
            # Show first 500 characters
            print(preview_content[:500] + "..." if len(preview_content) > 500 else preview_content)
        
        print("\n✅ Example completed successfully!")
        print("\nTo generate actual CV with LLM:")
        print("1. Add your API keys to .env file")
        print("2. Run: python -m src.main --job-id sample_001 --profile-type product_management")
        
    except Exception as e:
        logger.error(f"Example failed: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
