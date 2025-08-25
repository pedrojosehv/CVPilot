#!/usr/bin/env python3
"""
Extract content from bullet_pool.docx for analysis
"""

import docx
from pathlib import Path

def extract_bullet_pool():
    """Extract content from bullet_pool.docx"""
    
    file_path = Path("templates/bullet_pool.docx")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    try:
        doc = docx.Document(file_path)
        content = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text.strip())
        
        print("📄 Bullet Pool Content:")
        print("=" * 50)
        for i, line in enumerate(content, 1):
            print(f"{i:2d}. {line}")
        
        return content
        
    except Exception as e:
        print(f"❌ Error reading DOCX: {e}")
        return None

if __name__ == "__main__":
    extract_bullet_pool()
