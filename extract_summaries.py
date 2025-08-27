#!/usr/bin/env python3
"""
Extract real summaries from successful CVs to use as examples
"""

import os
from pathlib import Path
from docx import Document

def extract_summaries_from_recent_cvs():
    output_dir = Path('output')
    summaries = []

    # Look for recent successful CVs
    for folder in output_dir.iterdir():
        if folder.is_dir():
            for file in folder.glob('*.docx'):
                if '2025' in str(file) and file.stat().st_size > 10000:  # Recent and substantial files
                    try:
                        doc = Document(file)
                        for para in doc.paragraphs[:10]:  # First 10 paragraphs
                            text = para.text.strip()
                            if len(text) > 50 and not any(section in text.lower() for section in ['professional experience', 'skills', 'education', 'software']):
                                summaries.append(text)
                                break
                    except Exception as e:
                        print(f"Error processing {file}: {e}")
                        pass

    return summaries[:5]  # Return top 5 summaries

if __name__ == "__main__":
    summaries = extract_summaries_from_recent_cvs()
    print("REAL SUMMARIES FROM SUCCESSFUL CVS:")
    print("=" * 50)
    for i, summary in enumerate(summaries, 1):
        print(f'{i}. "{summary}"')
        print()
