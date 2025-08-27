#!/usr/bin/env python3
"""
Test script for naming validation
Validates the accuracy of generated naming against actual job descriptions
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.naming_validator import NamingValidator
from rich.console import Console
from rich.panel import Panel

def main():
    console = Console()
    
    # Test data for Job ID 84 (Updated with improved system results)
    job_title = "Project Manager de Visión artificial e inteligencia artificial"
    company = "AINIA"
    generated_folder = "Project Manager - AI ML - Python, Confluence, Jira"
    generated_filename = "PedroHerrera_PJM_AIML_SaaS_2025.docx"
    
    console.print(Panel.fit(
        f"[bold blue]🔍 NAMING VALIDATION TEST[/bold blue]\n"
        f"Job: {job_title}\n"
        f"Company: {company}",
        title="CVPilot Naming Validator"
    ))
    
    # Initialize validator
    datapm_path = Path("D:/Work Work/Upwork/DataPM")
    validator = NamingValidator(datapm_path)
    
    # Validate naming accuracy
    console.print("\n[bold yellow]Validating naming accuracy...[/bold yellow]")
    
    validation_result = validator.validate_naming_accuracy(
        job_title, company, generated_folder, generated_filename
    )
    
    # Generate and display report
    report = validator.generate_validation_report(validation_result)
    
    console.print(Panel(
        report,
        title="[bold green]Validation Report[/bold green]",
        border_style="green"
    ))
    
    # Additional analysis
    if validation_result['status'] == 'success':
        console.print("\n[bold cyan]📊 DETAILED ANALYSIS:[/bold cyan]")
        
        # Show actual vs generated software
        actual_software = validation_result['actual_software']
        generated_software = validation_result['generated_analysis']['folder_software']
        
        console.print(f"\n[bold]Actual Software (from DataPM):[/bold]")
        for sw in actual_software:
            console.print(f"  • {sw}")
        
        console.print(f"\n[bold]Generated Software (in folder name):[/bold]")
        for sw in generated_software:
            console.print(f"  • {sw}")
        
        # Show keyword analysis
        keywords = validation_result['description_keywords']
        if keywords:
            console.print(f"\n[bold]Keywords Found in Description:[/bold]")
            for category, terms in keywords.items():
                console.print(f"  • {category.upper()}: {', '.join(terms)}")
        
        # Show accuracy breakdown
        metrics = validation_result['accuracy_metrics']
        console.print(f"\n[bold]Accuracy Breakdown:[/bold]")
        console.print(f"  • Software Accuracy: {metrics['software_accuracy']:.1%}")
        console.print(f"  • Category Accuracy: {metrics['category_accuracy']:.1%}")
        console.print(f"  • Overall Score: {metrics['overall_score']:.1%}")

if __name__ == "__main__":
    main()
