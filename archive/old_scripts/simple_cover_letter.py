#!/usr/bin/env python3
"""
Simple standalone cover letter generator
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.generation.cover_letter_generator import CoverLetterGenerator
from src.utils.config import Config
from src.ingest.manual_loader import ManualLoader
from src.matching.profile_matcher import ProfileMatcher
from src.utils.naming_utils import NamingUtils

def generate_cover_letter_only(job_id: str):
    """Generate only a cover letter for a job"""
    
    print(f"Generating cover letter for Job ID: {job_id}")
    
    # Initialize components
    config = Config()
    loader = ManualLoader(config.manual_exports_path)
    matcher = ProfileMatcher(config.profiles_path)
    
    # Load job data
    job_data = loader.load_job(job_id)
    print(f"Job: {job_data.job_title_original} at {job_data.company}")
    
    # Match profile (just for basic info)
    match_result = matcher.match_job_to_profile(job_data, "product_management")
    print(f"Fit score: {match_result.fit_score:.3f}")
    
    # Create simple CV content (using template info instead of generating)
    cv_content = {
        'profile_summary': "Product Manager with 5+ years of experience driving revenue growth and operational excellence in SaaS environments. Expertise in product strategy, data analytics, and cross-functional team leadership.",
        'skill_list': "Product Strategy, Data Analytics, Cross-functional Leadership, A/B Testing, User Research, Agile Methodologies",
        'software_list': "Google Analytics, Mixpanel, Tableau, Figma, Jira, SQL, Python"
    }
    
    # Generate cover letter
    cover_letter_gen = CoverLetterGenerator(config.llm_config, str(config.datapm_path))
    
    try:
        cover_letter_content = cover_letter_gen.generate_cover_letter(job_data, match_result, cv_content)
        
        # Generate filename
        cover_letter_filename = NamingUtils.generate_filename(
            job_data.job_title_original,
            job_data.software,
            job_data.company,
            "cover_letter"
        )
        
        # Find the most recent CV folder or create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Find the most recent folder with a CV that has the same base filename
        cv_folder = NamingUtils.find_most_recent_cv_folder(output_dir, cover_letter_filename)
        
        # Save cover letter
        output_file = cv_folder / cover_letter_filename
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cover_letter_content)
        
        print(f"\n✅ Cover letter generated successfully!")
        print(f"📁 File: {output_file}")
        print(f"📊 Length: {len(cover_letter_content)} characters")
        
        print("\n" + "="*50)
        print("COVER LETTER PREVIEW:")
        print("="*50)
        print(cover_letter_content)
        print("="*50)
        
    except Exception as e:
        print(f"❌ Error generating cover letter: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_cover_letter_only("10")
