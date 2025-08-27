#!/usr/bin/env python3
"""
CVPilot - Main Entry Point
CV Automation Tool for job-specific customization
"""

import click
import logging
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

from .ingest.job_loader import JobLoader
from .ingest.manual_loader import ManualLoader
from .matching.profile_matcher import ProfileMatcher
from .generation.content_generator import ContentGenerator
from .generation.cover_letter_generator import CoverLetterGenerator
from .validation.content_validator import ContentValidator
from .template.docx_processor import DocxProcessor
from .utils.config import Config
from .utils.logger import setup_logger

def _determine_job_category(job_data, match_result):
    """Determine job category for file organization"""
    
    # Extract key information
    job_title = job_data.job_title_original.lower() if job_data.job_title_original else ""
    skills = [skill.lower() for skill in job_data.skills] if job_data.skills else []
    software = [tool.lower() for tool in job_data.software] if job_data.software else []
    
    # Define category keywords
    categories = {
        'product_management': ['product', 'pm', 'product manager', 'product owner', 'scrum'],
        'data_analytics': ['data', 'analytics', 'analyst', 'bi', 'business intelligence', 'sql', 'tableau', 'power bi'],
        'marketing': ['marketing', 'growth', 'digital marketing', 'seo', 'sem', 'social media'],
        'sales': ['sales', 'business development', 'account', 'customer success'],
        'engineering': ['engineer', 'developer', 'programming', 'software', 'technical', 'python', 'java', 'javascript'],
        'design': ['design', 'ux', 'ui', 'user experience', 'creative', 'visual'],
        'operations': ['operations', 'project', 'process', 'strategy', 'business'],
        'finance': ['finance', 'financial', 'accounting', 'budget', 'investment']
    }
    
    # Calculate category scores
    category_scores = {}
    for category, keywords in categories.items():
        score = 0
        # Check job title
        for keyword in keywords:
            if keyword in job_title:
                score += 3  # Higher weight for title matches
        
        # Check skills
        for skill in skills:
            for keyword in keywords:
                if keyword in skill:
                    score += 1
        
        # Check software
        for tool in software:
            for keyword in keywords:
                if keyword in tool:
                    score += 1
        
        category_scores[category] = score
    
    # Find best category
    best_category = max(category_scores.items(), key=lambda x: x[1])
    
    # If no clear category, use fit score to determine
    if best_category[1] == 0:
        if match_result.fit_score > 0.5:
            return 'high_match'
        elif match_result.fit_score > 0.3:
            return 'medium_match'
        else:
            return 'low_match'
    
    return best_category[0]

console = Console()

@click.command()
@click.option('--job-id', required=True, help='Job ID to process')
@click.option('--profile-type', default='product_management', help='Profile type to use')
@click.option('--template-path', help='Path to CV template')
@click.option('--output-dir', default='./output', help='Output directory')
@click.option('--dry-run', is_flag=True, help='Run in dry-run mode')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--cv-only', is_flag=True, help='Generate only CV')
@click.option('--cover-letter-only', is_flag=True, help='Generate only cover letter')
@click.option('--both', is_flag=True, default=True, help='Generate both CV and cover letter (default)')
@click.option('--sequential', is_flag=True, default=True, help='Generate CV and cover letter sequentially (default)')
def main(job_id, profile_type, template_path, output_dir, dry_run, verbose, cv_only, cover_letter_only, both, sequential):
    """
    CVPilot - Generate customized CV based on job description
    """
    # Setup logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logger = setup_logger(log_level)
    
    # Load configuration
    config = Config()
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    console.print(f"[bold blue]CVPilot[/bold blue] - Processing job ID: {job_id}")
    console.print(f"Profile type: {profile_type}")
    console.print(f"Dry run: {dry_run}")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            # Step 1: Ingest job data
            task1 = progress.add_task("Loading job data...", total=None)
            
            # Try manual loader first (for PowerBI exports)
            manual_loader = ManualLoader(config.manual_exports_path)
            job_data = manual_loader.load_job(job_id)
            
            # If not found in manual exports, try DataPM loader
            if not job_data:
                job_loader = JobLoader(config.data_path)
                job_data = job_loader.load_job(job_id)
            
            progress.update(task1, completed=True)
            
            if not job_data:
                console.print(f"[red]Error: Job ID {job_id} not found[/red]")
                return 1
            
            # Step 2: Match profile
            task2 = progress.add_task("Matching profile...", total=None)
            matcher = ProfileMatcher(config.profiles_path)
            match_result = matcher.match_job_to_profile(job_data, profile_type)
            progress.update(task2, completed=True)
            
            # Step 3: Generate content
            task3 = progress.add_task("Generating content...", total=None)
            generator = ContentGenerator(
                config.llm_config, 
                str(config.datapm_path),
                str(config.templates_path)
            )
            
            # Use multi-template processor by default
            if hasattr(generator, 'multi_template_processor') and generator.multi_template_processor:
                console.print("[green]✅ Using multi-template processing (pool of CVs)...[/green]")
                replacements = generator.generate_optimized_replacements(job_data, match_result, template_path or config.default_template_path)
            else:
                console.print("[yellow]⚠️ Multi-template processor not available, falling back to standard generation...[/yellow]")
                replacements = generator.generate_replacements(job_data, match_result)
            
            progress.update(task3, completed=True)
            
            # Step 4: Validate content
            task4 = progress.add_task("Validating content...", total=None)
            validator = ContentValidator()
            validation_result = validator.validate_replacements(replacements)
            progress.update(task4, completed=True)
            
            if not validation_result.is_valid:
                console.print(f"[red]Validation failed: {validation_result.errors}[/red]")
                return 1
            
            # Determine what to generate based on flags
            generate_cv = cv_only or both
            generate_cover_letter = cover_letter_only or both
            
            # Configure sequential execution by default
            if sequential and generate_cv and generate_cover_letter:
                console.print("[blue]🔄 Sequential execution enabled: CV first, then Cover Letter[/blue]")
            
            output_files = []
            
            # Step 5: Generate CV if requested
            if generate_cv:
                task5 = progress.add_task("Processing CV template...", total=None)
                processor = DocxProcessor()
                
                # Use default template if not specified
                if not template_path:
                    template_path = config.default_template_path
                
                # Determine job category for organization
                job_category = _determine_job_category(job_data, match_result)
                
                # Process template
                if dry_run:
                    output_file = processor.generate_dry_run(template_path, replacements, output_path)
                    console.print(f"[yellow]CV dry run completed. Output: {output_file}[/yellow]")
                else:
                    output_file = processor.process_template(template_path, replacements, output_path, job_category)
                    console.print(f"[green]CV generated successfully: {output_file}[/green]")
                    console.print(f"[blue]Category: {job_category}[/blue]")
                
                output_files.append(output_file)
                progress.update(task5, completed=True)
            
            # Step 5b: Generate Cover Letter if requested
            if generate_cover_letter:
                task5b = progress.add_task("Generating cover letter...", total=None)
                
                # Initialize cover letter generator
                cover_letter_gen = CoverLetterGenerator(config.llm_config, str(config.datapm_path))
                
                # Extract CV content for cover letter generation (ensure all are strings)
                cv_content = {
                    'profile_summary': str(replacements.profile_summary.content),
                    'skill_list': ', '.join(replacements.skill_list.content) if isinstance(replacements.skill_list.content, list) else str(replacements.skill_list.content),
                    'software_list': ', '.join(replacements.software_list.content) if isinstance(replacements.software_list.content, list) else str(replacements.software_list.content)
                }
                
                # Generate cover letter
                cover_letter_content = cover_letter_gen.generate_cover_letter(job_data, match_result, cv_content)
                
                # Determine output path for cover letter
                if generate_cv and not dry_run:
                    # Use the same folder as CV
                    cv_folder = output_files[0].parent
                else:
                    # Find the most recent folder with a CV that has the same base filename
                    cv_folder = NamingUtils.find_most_recent_cv_folder(output_path, cover_letter_filename)
                    if cv_folder == output_path:
                        # If no existing CV folder found, create a new category-based folder
                        job_category = _determine_job_category(job_data, match_result)
                        cv_folder = output_path / job_category
                        cv_folder.mkdir(exist_ok=True)
                
                # Generate cover letter filename
                from .utils.naming_utils import NamingUtils
                cover_letter_filename = NamingUtils.generate_filename(
                    job_data.job_title_original, 
                    job_data.software, 
                    job_data.company, 
                    "cover_letter"
                )
                cover_letter_file = cv_folder / cover_letter_filename
                
                # Save cover letter
                with open(cover_letter_file, 'w', encoding='utf-8') as f:
                    f.write(cover_letter_content)
                
                console.print(f"[green]Cover letter generated successfully: {cover_letter_file}[/green]")
                output_files.append(cover_letter_file)
                progress.update(task5b, completed=True)
            
            # Step 6: Calculate final fit score comparison (only if CV was generated)
            if generate_cv:
                task6 = progress.add_task("Calculating fit score improvement...", total=None)
                final_fit_analysis = matcher.calculate_final_fit_score(job_data, profile_type, replacements)
                progress.update(task6, completed=True)
            else:
                # For cover letter only, use initial match result
                final_fit_analysis = {
                    'initial_fit_score': match_result.fit_score,
                    'final_fit_score': match_result.fit_score,
                    'improvement': 0.0
                }
            
            # Log results
            logger.info(f"Job {job_id} processed successfully")
            logger.info(f"Initial fit score: {match_result.fit_score:.3f}")
            logger.info(f"Final fit score: {final_fit_analysis['final_fit_score']:.3f}")
            logger.info(f"Improvement: {final_fit_analysis['improvement']:.3f}")
            for output_file in output_files:
                logger.info(f"Output file: {output_file}")
            
            # Extract naming information for display
            from .utils.naming_utils import NamingUtils
            role_initials = NamingUtils.extract_role_initials(job_data.job_title_original)
            software_category = NamingUtils.extract_software_category(job_data.software)
            business_model = NamingUtils.extract_business_model(job_data.job_title_original, job_data.company)
            folder_name = NamingUtils.generate_folder_name(job_data.job_title_original, job_data.software)
        
        # Display summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Job ID: {job_id}")
        console.print(f"  Company: {job_data.company}")
        console.print(f"  Position: {job_data.job_title_original}")
        console.print(f"  Initial Fit Score: {match_result.fit_score:.3f}")
        console.print(f"  Final Fit Score: {final_fit_analysis['final_fit_score']:.3f}")
        console.print(f"  Improvement: {final_fit_analysis['improvement']:.3f}")
        for output_file in output_files:
            console.print(f"  Output: {output_file}")
        
        # Display naming information
        console.print("\n[bold]File Organization:[/bold]")
        if generate_cv:
            console.print(f"  CV Filename: PedroHerrera_{role_initials}_{software_category}_{business_model}_2025.docx")
        if generate_cover_letter:
            console.print(f"  Cover Letter Filename: PedroHerrera_{role_initials}_{software_category}_{business_model}_2025_CoverLetter.txt")
        console.print(f"  Folder: {folder_name}")
        console.print(f"  Role Initials: {role_initials}")
        console.print(f"  Software Category: {software_category}")
        console.print(f"  Business Model: {business_model}")
        
        # Display detailed improvement analysis
        console.print("\n[bold]Fit Score Analysis:[/bold]")
        if 'skill_improvement' in final_fit_analysis:
            console.print(f"  Skills Improvement: {final_fit_analysis['skill_improvement']:+d} skills")
        if 'software_improvement' in final_fit_analysis:
            console.print(f"  Software Improvement: {final_fit_analysis['software_improvement']:+d} tools")
        if final_fit_analysis.get('new_skills_added'):
            console.print(f"  New Skills Added: {', '.join(final_fit_analysis['new_skills_added'][:5])}")
        if final_fit_analysis.get('new_software_added'):
            console.print(f"  New Software Added: {', '.join(final_fit_analysis['new_software_added'][:3])}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1

if __name__ == "__main__":
    main()
