"""
CV Content Analyzer - Deep Content Analysis for Template Selection
CVPilot - Analyzes actual CV content, not just metadata
"""

import re
import string
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set, Optional
from collections import Counter, defaultdict
import logging
import docx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class CVContentAnalyzer:
    """Analyzes the actual content of CV documents for better template selection"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Keywords for different categories
        self.role_keywords = {
            'PA': ['product analyst', 'data analysis', 'analytics', 'product metrics', 'kpi', 'dashboard'],
            'DA': ['data analyst', 'sql', 'python', 'tableau', 'power bi', 'data visualization'],
            'PM': ['product manager', 'roadmap', 'stakeholder', 'product strategy', 'product development'],
            'PO': ['product owner', 'agile', 'scrum', 'user stories', 'backlog', 'sprint'],
            'PJM': ['project manager', 'gantt', 'milestone', 'timeline', 'resource management'],
            'BA': ['business analyst', 'requirements', 'process', 'workflow', 'documentation']
        }

        self.skill_categories = {
            'technical': ['python', 'sql', 'java', 'javascript', 'aws', 'azure', 'docker', 'kubernetes'],
            'analytics': ['tableau', 'power bi', 'excel', 'google analytics', 'mixpanel', 'amplitude'],
            'management': ['jira', 'confluence', 'slack', 'trello', 'asana', 'notion'],
            'design': ['figma', 'sketch', 'adobe', 'photoshop', 'illustrator']
        }

        # Initialize TF-IDF vectorizer for content similarity
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )

        self.content_cache = {}  # Cache for extracted content

    def analyze_cv_content(self, cv_path: Path) -> Dict[str, Any]:
        """
        Analyze the actual content of a CV document

        Returns:
            Dict with content analysis results
        """
        if not cv_path.exists():
            return {}

        try:
            # Extract text content
            content = self._extract_cv_text(cv_path)
            if not content:
                return {}

            # Basic content metrics
            analysis = {
                'word_count': len(content.split()),
                'char_count': len(content),
                'paragraph_count': len([p for p in content.split('\n\n') if p.strip()]),
                'sections': self._identify_sections(content),
                'skills_found': self._extract_skills(content),
                'experience_years': self._estimate_experience_years(content),
                'role_keywords': self._count_role_keywords(content),
                'content_vector': self._vectorize_content(content),
                'readability_score': self._calculate_readability(content)
            }

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing CV content {cv_path}: {e}")
            return {}

    def calculate_content_similarity(self, cv1_path: Path, cv2_path: Path) -> float:
        """
        Calculate content similarity between two CVs

        Returns:
            Similarity score 0-1
        """
        content1 = self._extract_cv_text(cv1_path)
        content2 = self._extract_cv_text(cv2_path)

        if not content1 or not content2:
            return 0.0

        # Vectorize both contents
        try:
            vectors = self.vectorizer.fit_transform([content1, content2])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return float(similarity)
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {e}")
            return 0.0

    def match_content_to_job(self, cv_analysis: Dict[str, Any], job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match CV content to job requirements

        Returns:
            Dict with matching scores and insights
        """
        if not cv_analysis:
            return {'content_score': 0.0, 'insights': []}

        job_title = job_data.get('job_title_original', '').lower()
        job_skills = set(job_data.get('skills', []))
        job_software = set(job_data.get('software', []))

        content_score = 0.0
        insights = []

        # 1. Role alignment based on content keywords
        role_alignment = self._calculate_role_alignment(cv_analysis, job_title)
        content_score += role_alignment * 0.3
        if role_alignment > 0.5:
            insights.append(f"Content shows strong {self._get_best_role(cv_analysis)} alignment")

        # 2. Skills match in content
        content_skills = cv_analysis.get('skills_found', set())
        skill_overlap = len(content_skills & (job_skills | job_software))
        skill_score = min(skill_overlap / max(len(job_skills | job_software), 1), 1.0)
        content_score += skill_score * 0.4
        if skill_score > 0.3:
            insights.append(f"Content mentions {skill_overlap} relevant skills")

        # 3. Experience level alignment
        job_experience = self._estimate_job_experience_level(job_data)
        cv_experience = cv_analysis.get('experience_years', 0)
        experience_alignment = self._calculate_experience_alignment(cv_experience, job_experience)
        content_score += experience_alignment * 0.3
        if abs(cv_experience - job_experience) <= 2:
            insights.append(f"Experience level matches ({cv_experience} years)")

        return {
            'content_score': min(content_score, 1.0),
            'insights': insights,
            'detailed_scores': {
                'role_alignment': role_alignment,
                'skill_match': skill_score,
                'experience_alignment': experience_alignment
            }
        }

    def _extract_cv_text(self, cv_path: Path) -> str:
        """Extract text content from CV document"""
        if cv_path in self.content_cache:
            return self.content_cache[cv_path]

        try:
            if cv_path.suffix.lower() == '.docx':
                doc = docx.Document(str(cv_path))
                content = '\n'.join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
            else:
                # Fallback for other formats
                content = ""

            # Clean and normalize content
            content = self._clean_text(content)

            # Cache the result
            self.content_cache[cv_path] = content

            return content

        except Exception as e:
            self.logger.error(f"Error extracting text from {cv_path}: {e}")
            return ""

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove special characters but keep basic punctuation
        text = ''.join(c for c in text if c.isalnum() or c in ' .,-')

        # Normalize to lowercase for analysis
        return text.lower()

    def _identify_sections(self, content: str) -> List[str]:
        """Identify main sections in the CV"""
        sections = []
        content_lower = content.lower()

        section_keywords = {
            'experience': ['experience', 'work experience', 'professional experience'],
            'education': ['education', 'academic background', 'qualifications'],
            'skills': ['skills', 'technical skills', 'competencies'],
            'projects': ['projects', 'project experience', 'key projects'],
            'certifications': ['certifications', 'certificates', 'licenses'],
            'summary': ['summary', 'profile', 'objective', 'about']
        }

        for section, keywords in section_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                sections.append(section)

        return sections

    def _extract_skills(self, content: str) -> Set[str]:
        """Extract skills mentioned in the CV content"""
        content_lower = content.lower()
        found_skills = set()

        # Check for specific skills
        for category, skills in self.skill_categories.items():
            for skill in skills:
                if skill.lower() in content_lower:
                    found_skills.add(skill)

        return found_skills

    def _estimate_experience_years(self, content: str) -> int:
        """Estimate years of experience from CV content"""
        # Look for date ranges like "2019-2023" or "2019 - Present"
        date_patterns = [
            r'(\d{4})\s*-\s*(\d{4})',  # 2019-2023
            r'(\d{4})\s*-\s*present',   # 2019-Present
            r'(\d{4})\s*-\s*current'    # 2019-Current
        ]

        years = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    start_year = int(match[0])
                    end_year = int(match[1]) if match[1].isdigit() else datetime.now().year
                    years.append(end_year - start_year)

        # Also look for explicit mentions like "5+ years"
        year_mention_pattern = r'(\d+)\+?\s*years?'
        year_matches = re.findall(year_mention_pattern, content, re.IGNORECASE)
        for match in year_matches:
            years.append(int(match))

        return max(years) if years else 0

    def _count_role_keywords(self, content: str) -> Dict[str, int]:
        """Count role-specific keywords in content"""
        content_lower = content.lower()
        keyword_counts = {}

        for role, keywords in self.role_keywords.items():
            count = sum(1 for keyword in keywords if keyword in content_lower)
            if count > 0:
                keyword_counts[role] = count

        return keyword_counts

    def _vectorize_content(self, content: str) -> Optional[np.ndarray]:
        """Convert content to TF-IDF vector"""
        try:
            # Fit on this single document for now
            # In production, you'd fit on a corpus of documents
            vector = self.vectorizer.fit_transform([content])
            return vector.toarray()[0]
        except Exception as e:
            self.logger.error(f"Error vectorizing content: {e}")
            return None

    def _calculate_readability(self, content: str) -> float:
        """Calculate basic readability score"""
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        sentences = [s for s in sentences if s.strip()]

        if not sentences or not words:
            return 0.0

        avg_words_per_sentence = len(words) / len(sentences)
        avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)

        # Simple readability formula (lower is better readability)
        readability = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59

        # Normalize to 0-1 scale (higher is better)
        return max(0, min(1, (100 - readability) / 100))

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (simplified)"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"

        if word[0] in vowels:
            count += 1

        for i in range(1, len(word)):
            if word[i] in vowels and word[i - 1] not in vowels:
                count += 1

        if word.endswith("e"):
            count -= 1

        return max(1, count)

    def _calculate_role_alignment(self, cv_analysis: Dict[str, Any], job_title: str) -> float:
        """Calculate how well CV content aligns with job role"""
        keyword_counts = cv_analysis.get('role_keywords', {})

        if not keyword_counts:
            return 0.0

        # Find the role with highest keyword matches
        best_role = max(keyword_counts.items(), key=lambda x: x[1])

        # Simple alignment score based on keyword density
        total_keywords = sum(keyword_counts.values())
        alignment_score = best_role[1] / total_keywords if total_keywords > 0 else 0

        return alignment_score

    def _get_best_role(self, cv_analysis: Dict[str, Any]) -> str:
        """Get the best matching role from content analysis"""
        keyword_counts = cv_analysis.get('role_keywords', {})

        if not keyword_counts:
            return "unknown"

        return max(keyword_counts.items(), key=lambda x: x[1])[0]

    def _estimate_job_experience_level(self, job_data: Dict[str, Any]) -> int:
        """Estimate required experience level from job data"""
        experience_text = job_data.get('experience_years', '')

        if isinstance(experience_text, str):
            # Extract numbers from experience text
            numbers = re.findall(r'(\d+)', experience_text)
            if numbers:
                return int(numbers[0])

        return 3  # Default to 3 years if not specified

    def _calculate_experience_alignment(self, cv_years: int, job_years: int) -> float:
        """Calculate alignment between CV experience and job requirements"""
        if cv_years == 0 or job_years == 0:
            return 0.5  # Neutral if unknown

        # Perfect match
        if cv_years == job_years:
            return 1.0

        # Close match
        if abs(cv_years - job_years) <= 1:
            return 0.8

        # Reasonable match
        if abs(cv_years - job_years) <= 2:
            return 0.6

        # Too much experience
        if cv_years > job_years + 3:
            return 0.3

        # Too little experience
        if cv_years < job_years - 1:
            return 0.2

        return 0.5
