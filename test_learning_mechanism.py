#!/usr/bin/env python3
"""
Test Learning Mechanism - Evaluate Business Operations title detection
CVPilot - Test if the system correctly learns from updated CV titles
"""

from pathlib import Path
from src.utils.user_profile_manager import UserProfileManager
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def test_learning_mechanism():
    """Test if the learning mechanism correctly detects Business Operations titles"""

    console.print("[bold blue]🧠 TESTING LEARNING MECHANISM[/bold blue]")
    console.print("[bold yellow]Evaluating Business Operations title detection[/bold yellow]")
    console.print("=" * 60)

    # Step 1: Clear existing profile to force fresh extraction
    console.print("\n[cyan]1. Clearing existing profile...[/cyan]")
    profile_file = Path("./data/user_profiles/user_profile.json")
    if profile_file.exists():
        profile_file.unlink()
        console.print("   ✅ Cleared existing profile")
    else:
        console.print("   ℹ️ No existing profile found")

    # Step 2: Initialize fresh profile manager
    console.print("\n[cyan]2. Initializing fresh profile manager...[/cyan]")
    profile_manager = UserProfileManager()

    # Step 3: Extract from updated template
    console.print("\n[cyan]3. Extracting from updated template (Business Operations)...[/cyan]")
    template_path = Path("templates/PedroHerrera_PA_SaaS_B2B_Remote_2025.docx")
    if template_path.exists():
        profile_manager.extract_from_cv_template(str(template_path))
        console.print("   ✅ Template processed successfully")
    else:
        console.print("   ❌ Template not found!")
        return

    # Step 4: Analyze extracted profile
    console.print("\n[cyan]4. Analyzing extracted profile...[/cyan]")
    profile_summary = profile_manager.get_profile_summary()

    # Check if Business Operations titles were detected
    console.print("\n[bold green]🔍 DETECTION RESULTS:[/bold green]")

    # Test 1: Check if name was extracted
    user_name = profile_summary['contact'].get('name', 'Not detected')
    console.print(f"   • User Name: {user_name}")

    # Test 2: Check work experience extraction
    work_exp = profile_summary.get('work_experience', [])
    console.print(f"   • Work Experience Entries: {len(work_exp)}")

    # Test 3: Look for Business Operations in any extracted text
    business_ops_found = False
    business_ops_positions = []

    if work_exp:
        for exp in work_exp:
            position = exp.get('position', '').lower()
            if 'business operations' in position:
                business_ops_found = True
                business_ops_positions.append(exp)

    # Additional check: Search in raw extracted data
    if not business_ops_found:
        # Check if the extraction captured any Business Operations text
        profile_dict = profile_manager.profile.dict()
        for exp in profile_dict.get('work_experience', []):
            position = exp.get('position', '').lower()
            if 'business operations' in position:
                business_ops_found = True
                business_ops_positions.append(exp)

    # Test 4: Evaluate learning mechanism success
    console.print("\n[bold green]📊 LEARNING MECHANISM EVALUATION:[/bold green]")

    if business_ops_found:
        console.print("   ✅ SUCCESS: Business Operations titles detected!")
        for pos in business_ops_positions:
            console.print(f"      • Position: {pos['position']}")
            console.print(f"      • Company: {pos['company']}")
            console.print(f"      • Dates: {pos['start_date']} - {pos.get('end_date', 'Present')}")
    else:
        console.print("   ❌ ISSUE: Business Operations titles NOT detected")

        # Debug information
        console.print("\n[cyan]🔧 DEBUG INFORMATION:[/cyan]")
        if work_exp:
            console.print("   • Extracted positions:")
            for exp in work_exp[:5]:  # Show first 5
                console.print(f"      - {exp.get('position', 'Unknown')} at {exp.get('company', 'Unknown')}")
        else:
            console.print("   • No work experience extracted")

    # Test 5: Skills extraction
    skills_count = len(profile_summary['top_skills'])
    console.print(f"   • Skills Extracted: {skills_count}")

    # Test 6: Experience calculation
    exp_years = profile_summary['experience_years']
    console.print(f"   • Calculated Experience: {exp_years} years")

    # Step 5: Save and verify persistence
    console.print("\n[cyan]5. Testing persistence...[/cyan]")
    profile_manager.save_profile()
    console.print("   ✅ Profile saved")

    # Reload and verify
    fresh_manager = UserProfileManager()
    fresh_summary = fresh_manager.get_profile_summary()
    fresh_name = fresh_summary['contact'].get('name', 'Not detected')
    console.print(f"   • Persistence Test: {fresh_name} (should match above)")

    # Step 6: Final evaluation
    console.print("\n[bold green]🎯 FINAL EVALUATION:[/bold green]")

    success_criteria = {
        "Business Operations Detected": business_ops_found,
        "Skills Extracted": skills_count > 0,
        "Profile Persistent": fresh_name != 'Not detected',
        "Experience Calculated": exp_years > 0
    }

    all_passed = all(success_criteria.values())

    table = Table(title="Learning Mechanism Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")

    for test, passed in success_criteria.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        details = ""
        if test == "Business Operations Detected" and passed:
            details = f"{len(business_ops_positions)} positions found"
        elif test == "Skills Extracted":
            details = f"{skills_count} skills"
        elif test == "Experience Calculated":
            details = f"{exp_years} years"

        table.add_row(test, status, details)

    console.print(table)

    if all_passed:
        console.print("\n[bold green]🎉 LEARNING MECHANISM: EXCELLENT![/bold green]")
        console.print("   The system successfully detected and learned from the Business Operations titles!")
    else:
        console.print("\n[bold yellow]⚠️ LEARNING MECHANISM: NEEDS IMPROVEMENT[/bold yellow]")
        failed_tests = [test for test, passed in success_criteria.items() if not passed]
        console.print(f"   Failed tests: {', '.join(failed_tests)}")

    console.print("\n[bold blue]📋 SUMMARY:[/bold blue]")
    console.print(f"   • Business Operations titles: {'✅ Detected' if business_ops_found else '❌ Not detected'}")
    console.print(f"   • Skills extracted: {skills_count}")
    console.print(f"   • Experience calculated: {exp_years} years")
    console.print(f"   • Profile persistence: {'✅ Working' if fresh_name != 'Not detected' else '❌ Failed'}")

if __name__ == "__main__":
    test_learning_mechanism()
