"""
CV Monitor - Tracks changes in CV files and syncs with role database
CVPilot - Monitors output folder for new/modified CVs and updates database
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from .logger import LoggerMixin
from .role_content_manager import RoleContentManager


@dataclass
class CVFileInfo:
    """Information about a CV file"""
    file_path: str
    file_name: str
    role_detected: str
    file_hash: str
    file_size: int
    modified_time: str
    created_time: str
    last_synced: Optional[str] = None
    sync_status: str = "pending"  # pending, synced, error


class CVMonitor(LoggerMixin):
    """Monitors CV files and syncs with role database"""

    def __init__(self, output_dir: str = "./output", role_manager: RoleContentManager = None):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.role_manager = role_manager or RoleContentManager()
        
        # Tracking file
        self.tracking_file = Path("data/cv_tracking.json")
        self.tracking_file.parent.mkdir(exist_ok=True)
        
        # Load existing tracking data
        self.tracked_files = self._load_tracking_data()
        
        self.logger.info(f"✅ CVMonitor initialized - tracking {len(self.tracked_files)} files")

    def _load_tracking_data(self) -> Dict[str, CVFileInfo]:
        """Load existing CV tracking data"""
        if not self.tracking_file.exists():
            return {}
        
        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dict to CVFileInfo objects
            tracked = {}
            for file_path, file_data in data.items():
                tracked[file_path] = CVFileInfo(**file_data)
            
            return tracked
        except Exception as e:
            self.logger.error(f"❌ Error loading tracking data: {e}")
            return {}

    def _save_tracking_data(self):
        """Save CV tracking data"""
        try:
            # Convert CVFileInfo objects to dict
            data = {}
            for file_path, file_info in self.tracked_files.items():
                data[file_path] = asdict(file_info)
            
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving tracking data: {e}")

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"❌ Error calculating hash for {file_path}: {e}")
            return ""

    def _detect_role_from_path(self, file_path: Path) -> str:
        """Detect role from file path and name"""
        path_str = str(file_path).lower()
        file_name = file_path.name.lower()
        
        # Check folder name first
        if 'product manager' in path_str or 'pm' in path_str:
            return 'Product Manager'
        elif 'product analyst' in path_str or 'pa' in path_str:
            return 'Product Analyst'
        elif 'business analyst' in path_str or 'ba' in path_str:
            return 'Business Analyst'
        elif 'data analyst' in path_str or 'da' in path_str:
            return 'Data Analyst'
        elif 'project manager' in path_str or 'pjm' in path_str:
            return 'Project Manager'
        elif 'product owner' in path_str or 'po' in path_str:
            return 'Product Owner'
        
        # Check file name patterns
        if '_pm_' in file_name:
            return 'Product Manager'
        elif '_pa_' in file_name:
            return 'Product Analyst'
        elif '_ba_' in file_name:
            return 'Business Analyst'
        elif '_da_' in file_name:
            return 'Data Analyst'
        elif '_pjm_' in file_name:
            return 'Project Manager'
        elif '_po_' in file_name:
            return 'Product Owner'
        
        return 'Unknown'

    def scan_for_changes(self) -> Tuple[List[CVFileInfo], List[CVFileInfo], List[str]]:
        """
        Scan output directory for CV changes
        
        Returns:
            Tuple of (new_files, modified_files, deleted_files)
        """
        self.logger.info("🔍 Scanning for CV changes...")
        
        new_files = []
        modified_files = []
        deleted_files = []
        current_files = set()
        
        # Scan all DOCX files in output directory
        for cv_file in self.output_dir.rglob("*.docx"):
            if cv_file.name.startswith("~$"):  # Skip temp files
                continue
            
            file_path = str(cv_file.relative_to(self.output_dir))
            current_files.add(file_path)
            
            # Get file stats
            stat = cv_file.stat()
            file_hash = self._calculate_file_hash(cv_file)
            modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()
            
            # Check if file is new or modified
            if file_path not in self.tracked_files:
                # New file
                role = self._detect_role_from_path(cv_file)
                new_file_info = CVFileInfo(
                    file_path=file_path,
                    file_name=cv_file.name,
                    role_detected=role,
                    file_hash=file_hash,
                    file_size=stat.st_size,
                    modified_time=modified_time,
                    created_time=created_time
                )
                new_files.append(new_file_info)
                self.tracked_files[file_path] = new_file_info
                
            else:
                # Check if modified
                tracked_info = self.tracked_files[file_path]
                if tracked_info.file_hash != file_hash:
                    # File modified
                    tracked_info.file_hash = file_hash
                    tracked_info.file_size = stat.st_size
                    tracked_info.modified_time = modified_time
                    tracked_info.sync_status = "pending"
                    modified_files.append(tracked_info)
        
        # Check for deleted files
        tracked_paths = set(self.tracked_files.keys())
        deleted_files = list(tracked_paths - current_files)
        
        # Remove deleted files from tracking
        for deleted_path in deleted_files:
            del self.tracked_files[deleted_path]
        
        self.logger.info(f"📊 Scan results: {len(new_files)} new, {len(modified_files)} modified, {len(deleted_files)} deleted")
        
        return new_files, modified_files, deleted_files

    def sync_with_database(self, files_to_sync: List[CVFileInfo]) -> Dict[str, Any]:
        """
        Sync CV files with role database
        
        Returns:
            Sync results summary
        """
        self.logger.info(f"🔄 Syncing {len(files_to_sync)} files with database...")
        
        sync_results = {
            'synced': 0,
            'errors': 0,
            'roles_updated': set(),
            'details': []
        }
        
        for file_info in files_to_sync:
            try:
                # Extract content from CV file
                full_path = self.output_dir / file_info.file_path
                content = self._extract_cv_content(full_path)
                
                if content:
                    # Add to role database
                    self.role_manager.add_cv_content(
                        role_name=file_info.role_detected,
                        summary=content.get('summary'),
                        bullet_points=content.get('bullets'),
                        skills=content.get('skills'),
                        software=content.get('software'),
                        achievements=content.get('achievements')
                    )
                    
                    # Update sync status
                    file_info.sync_status = "synced"
                    file_info.last_synced = datetime.now().isoformat()
                    
                    sync_results['synced'] += 1
                    sync_results['roles_updated'].add(file_info.role_detected)
                    sync_results['details'].append(f"✅ {file_info.file_name} → {file_info.role_detected}")
                    
                else:
                    file_info.sync_status = "error"
                    sync_results['errors'] += 1
                    sync_results['details'].append(f"❌ {file_info.file_name} → Content extraction failed")
                    
            except Exception as e:
                file_info.sync_status = "error"
                sync_results['errors'] += 1
                sync_results['details'].append(f"❌ {file_info.file_name} → {str(e)}")
                self.logger.error(f"❌ Error syncing {file_info.file_name}: {e}")
        
        # Save updated tracking data
        self._save_tracking_data()
        
        self.logger.info(f"✅ Sync completed: {sync_results['synced']} synced, {sync_results['errors']} errors")
        
        return sync_results

    def _extract_cv_content(self, cv_path: Path) -> Optional[Dict[str, Any]]:
        """Extract content from CV file"""
        try:
            from docx import Document
            
            doc = Document(cv_path)
            content = {
                'summary': '',
                'bullets': [],
                'skills': [],
                'software': [],
                'achievements': []
            }
            
            current_section = None
            
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if not text:
                    continue
                
                text_lower = text.lower()
                
                # Detect sections
                if any(keyword in text_lower for keyword in ['professional summary', 'profile summary', 'summary']):
                    current_section = 'summary'
                    continue
                elif any(keyword in text_lower for keyword in ['experience', 'work experience']):
                    current_section = 'experience'
                    continue
                elif any(keyword in text_lower for keyword in ['skills', 'technical skills']):
                    current_section = 'skills'
                    continue
                elif any(keyword in text_lower for keyword in ['software', 'tools']):
                    current_section = 'software'
                    continue
                
                # Extract content based on section
                if current_section == 'summary' and len(text) > 50:
                    content['summary'] = text
                elif current_section == 'experience' and text.startswith('•'):
                    content['bullets'].append(text)
                    content['achievements'].append(text)
                elif current_section == 'skills':
                    # Split skills by comma or semicolon
                    skills = [skill.strip() for skill in text.replace(';', ',').split(',')]
                    content['skills'].extend([s for s in skills if s])
                elif current_section == 'software':
                    # Split software by comma or semicolon  
                    software = [tool.strip() for tool in text.replace(';', ',').split(',')]
                    content['software'].extend([s for s in software if s])
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting content from {cv_path}: {e}")
            return None

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get summary of monitoring status"""
        total_files = len(self.tracked_files)
        synced_files = sum(1 for f in self.tracked_files.values() if f.sync_status == "synced")
        pending_files = sum(1 for f in self.tracked_files.values() if f.sync_status == "pending")
        error_files = sum(1 for f in self.tracked_files.values() if f.sync_status == "error")
        
        roles_count = {}
        for file_info in self.tracked_files.values():
            role = file_info.role_detected
            roles_count[role] = roles_count.get(role, 0) + 1
        
        return {
            'total_files': total_files,
            'synced_files': synced_files,
            'pending_files': pending_files,
            'error_files': error_files,
            'roles_distribution': roles_count,
            'last_scan': datetime.now().isoformat()
        }

    def force_full_sync(self) -> Dict[str, Any]:
        """Force full synchronization of all CV files"""
        self.logger.info("🔄 Starting full synchronization...")
        
        # Scan for all changes
        new_files, modified_files, deleted_files = self.scan_for_changes()
        
        # Mark all files as pending sync
        for file_info in self.tracked_files.values():
            file_info.sync_status = "pending"
        
        # Sync all files
        all_files = list(self.tracked_files.values())
        sync_results = self.sync_with_database(all_files)
        
        return sync_results

