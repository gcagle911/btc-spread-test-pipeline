"""
Enhanced Backup System for BTC Historical Data
Supports multiple backup providers with automatic restore capabilities
"""

import os
import json
import time
import shutil
import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import threading
import asyncio
import zipfile
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackupProvider(ABC):
    """Abstract base class for backup providers"""
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str, metadata: Dict = None) -> bool:
        pass
    
    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "") -> List[Dict]:
        pass
    
    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass

class LocalBackupProvider(BackupProvider):
    """Local filesystem backup provider"""
    
    def __init__(self, backup_dir: str = None):
        # Use environment variable or default locations
        if backup_dir is None:
            backup_dir = os.getenv('LOCAL_BACKUP_DIR')
            if not backup_dir:
                # For Render, use the app directory which persists during app lifetime
                if os.getenv('RENDER_SERVICE_NAME'):  # Render environment
                    backup_dir = "./backup_data"  # Relative to app directory
                else:
                    backup_dir = os.path.expanduser("~/btc_backup")  # Local development
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Local backup initialized: {self.backup_dir}")
    
    def upload_file(self, local_path: str, remote_path: str, metadata: Dict = None) -> bool:
        try:
            dest_path = self.backup_dir / remote_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest_path)
            
            # Store metadata
            if metadata:
                metadata_path = dest_path.with_suffix(dest_path.suffix + '.meta')
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f)
            
            logger.info(f"✅ Local backup: {local_path} → {dest_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Local backup failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        try:
            source_path = self.backup_dir / remote_path
            if not source_path.exists():
                logger.error(f"❌ File not found: {source_path}")
                return False
            
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, local_path)
            logger.info(f"✅ Local restore: {source_path} → {local_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Local restore failed: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict]:
        try:
            files = []
            search_path = self.backup_dir / prefix if prefix else self.backup_dir
            
            if search_path.is_dir():
                for file_path in search_path.rglob("*"):
                    if file_path.is_file() and not file_path.suffix == '.meta':
                        rel_path = file_path.relative_to(self.backup_dir)
                        stat = file_path.stat()
                        files.append({
                            'name': str(rel_path),
                            'size': stat.st_size,
                            'created': datetime.fromtimestamp(stat.st_ctime, UTC).isoformat(),
                            'modified': datetime.fromtimestamp(stat.st_mtime, UTC).isoformat()
                        })
            
            return files
        except Exception as e:
            logger.error(f"❌ Failed to list local files: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        try:
            file_path = self.backup_dir / remote_path
            if file_path.exists():
                file_path.unlink()
                # Also remove metadata if exists
                meta_path = file_path.with_suffix(file_path.suffix + '.meta')
                if meta_path.exists():
                    meta_path.unlink()
                logger.info(f"✅ Deleted local backup: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete local file: {e}")
            return False
    
    def is_available(self) -> bool:
        return self.backup_dir.exists() and os.access(self.backup_dir, os.W_OK)

class GCSBackupProvider(BackupProvider):
    """Google Cloud Storage backup provider"""
    
    def __init__(self, bucket_name: str = None, service_account_path: str = None, project_id: str = None):
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME')
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        self.client = None
        self.bucket = None
        
        if not self.bucket_name:
            logger.warning("⚠️ GCS bucket name not provided")
            return
        
        try:
            from google.cloud import storage
            from google.oauth2 import service_account
            
            # Try different authentication methods
            credentials = None
            
            # Method 1: JSON string in environment variable (Render-friendly)
            creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
            if creds_json:
                import json
                try:
                    creds_dict = json.loads(creds_json)
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                    logger.info("✅ Using Google Cloud credentials from environment variable")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
            
            # Method 2: Service account file path
            elif service_account_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                creds_path = service_account_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if os.path.exists(creds_path):
                    credentials = service_account.Credentials.from_service_account_file(creds_path)
                    logger.info(f"✅ Using Google Cloud credentials from file: {creds_path}")
                else:
                    logger.warning(f"⚠️ Credentials file not found: {creds_path}")
            
            # Initialize client
            if credentials:
                self.client = storage.Client(credentials=credentials, project=self.project_id)
            else:
                # Method 3: Default authentication (for Google Cloud environments)
                self.client = storage.Client(project=self.project_id)
                logger.info("✅ Using default Google Cloud authentication")
            
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"✅ GCS backup initialized: {self.bucket_name}")
            
        except Exception as e:
            logger.warning(f"⚠️ GCS backup unavailable: {e}")
            self.client = None
    
    def upload_file(self, local_path: str, remote_path: str, metadata: Dict = None) -> bool:
        if not self.client:
            return False
        
        try:
            blob = self.bucket.blob(remote_path)
            if metadata:
                blob.metadata = metadata
            blob.upload_from_filename(local_path)
            logger.info(f"✅ GCS backup: {local_path} → gs://{self.bucket_name}/{remote_path}")
            return True
        except Exception as e:
            logger.error(f"❌ GCS backup failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self.client:
            return False
        
        try:
            blob = self.bucket.blob(remote_path)
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(local_path)
            logger.info(f"✅ GCS restore: gs://{self.bucket_name}/{remote_path} → {local_path}")
            return True
        except Exception as e:
            logger.error(f"❌ GCS restore failed: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict]:
        if not self.client:
            return []
        
        try:
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            files = []
            for blob in blobs:
                files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'modified': blob.updated.isoformat() if blob.updated else None,
                    'metadata': blob.metadata
                })
            return files
        except Exception as e:
            logger.error(f"❌ Failed to list GCS files: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        if not self.client:
            return False
        
        try:
            blob = self.bucket.blob(remote_path)
            blob.delete()
            logger.info(f"✅ Deleted GCS file: gs://{self.bucket_name}/{remote_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete GCS file: {e}")
            return False
    
    def is_available(self) -> bool:
        return self.client is not None

class EnhancedBackupSystem:
    """Enhanced backup system with multiple providers and automatic restore"""
    
    def __init__(self, data_folder: str = "render_app/data"):
        self.data_folder = Path(data_folder)
        self.data_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize backup providers
        self.providers = {
            'local': LocalBackupProvider(),
            'gcs': GCSBackupProvider()
        }
        
        # Backup configuration
        self.backup_enabled = os.getenv('BACKUP_ENABLED', 'true').lower() in ['true', '1', 'yes']
        self.backup_interval = int(os.getenv('BACKUP_INTERVAL_MINUTES', '30'))
        self.critical_files = ['*.csv', '*.json']
        self.max_local_backups = int(os.getenv('MAX_LOCAL_BACKUPS', '10'))
        
        # Backup state
        self.last_backup_time = None
        self.backup_running = False
        self.backup_stats = {
            'total_backups': 0,
            'successful_backups': 0,
            'failed_backups': 0,
            'last_backup_size': 0
        }
        
        logger.info("✅ Enhanced backup system initialized")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available backup providers"""
        return [name for name, provider in self.providers.items() if provider.is_available()]
    
    def backup_all_data(self, providers: List[str] = None) -> Dict[str, Any]:
        """Backup all data files to specified providers"""
        if self.backup_running:
            logger.warning("⚠️ Backup already in progress")
            return {'error': 'Backup already in progress'}
        
        self.backup_running = True
        available_providers = self.get_available_providers()
        
        if providers:
            providers = [p for p in providers if p in available_providers]
        else:
            providers = available_providers
        
        if not providers:
            logger.error("❌ No backup providers available")
            self.backup_running = False
            return {'error': 'No backup providers available'}
        
        try:
            timestamp = datetime.now(UTC).strftime("%Y-%m-%d/%H-%M")
            results = {}
            total_size = 0
            
            logger.info(f"🔄 Starting backup to providers: {providers}")
            
            # Find all files to backup
            files_to_backup = []
            for pattern in self.critical_files:
                files_to_backup.extend(self.data_folder.glob(pattern))
            
            if not files_to_backup:
                logger.warning("⚠️ No files found to backup")
                self.backup_running = False
                return {'warning': 'No files found to backup'}
            
            # Backup to each provider
            for provider_name in providers:
                provider = self.providers[provider_name]
                provider_results = {
                    'uploaded_files': [],
                    'failed_files': [],
                    'total_size': 0
                }
                
                for file_path in files_to_backup:
                    if not file_path.is_file():
                        continue
                    
                    file_size = file_path.stat().st_size
                    remote_path = f"btc-data/{timestamp}/{file_path.name}"
                    
                    metadata = {
                        'backup_timestamp': datetime.now(UTC).isoformat(),
                        'source': 'enhanced-backup-system',
                        'file_size': str(file_size),
                        'provider': provider_name
                    }
                    
                    if provider.upload_file(str(file_path), remote_path, metadata):
                        provider_results['uploaded_files'].append(str(file_path))
                        provider_results['total_size'] += file_size
                        total_size += file_size
                    else:
                        provider_results['failed_files'].append(str(file_path))
                
                results[provider_name] = provider_results
            
            # Update stats
            self.backup_stats['total_backups'] += 1
            if any(len(r['uploaded_files']) > 0 for r in results.values()):
                self.backup_stats['successful_backups'] += 1
            else:
                self.backup_stats['failed_backups'] += 1
            
            self.backup_stats['last_backup_size'] = total_size
            self.last_backup_time = datetime.now(UTC)
            
            # Create backup summary
            summary = {
                'backup_timestamp': self.last_backup_time.isoformat(),
                'providers': providers,
                'results': results,
                'total_files': len(files_to_backup),
                'total_size': total_size,
                'success': any(len(r['uploaded_files']) > 0 for r in results.values())
            }
            
            # Save backup summary to each provider
            summary_path = f"btc-data/{timestamp}/backup-summary.json"
            for provider_name in providers:
                provider = self.providers[provider_name]
                summary_file = f"/tmp/backup-summary-{timestamp.replace('/', '-')}.json"
                with open(summary_file, 'w') as f:
                    json.dump(summary, f, indent=2)
                provider.upload_file(summary_file, summary_path)
                os.remove(summary_file)
            
            logger.info(f"✅ Backup completed: {total_size} bytes across {len(providers)} providers")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            self.backup_stats['failed_backups'] += 1
            return {'error': str(e)}
        finally:
            self.backup_running = False
    
    def restore_latest_backup(self, provider_name: str = None, target_folder: str = None) -> Dict[str, Any]:
        """Restore latest backup from specified provider"""
        available_providers = self.get_available_providers()
        
        if provider_name and provider_name not in available_providers:
            return {'error': f'Provider {provider_name} not available'}
        
        if not provider_name:
            # Use first available provider
            if not available_providers:
                return {'error': 'No backup providers available'}
            provider_name = available_providers[0]
        
        provider = self.providers[provider_name]
        target_path = Path(target_folder) if target_folder else self.data_folder
        
        try:
            # List all backup files
            backup_files = provider.list_files("btc-data/")
            if not backup_files:
                return {'error': 'No backup files found'}
            
            # Find the most recent backup
            backup_files.sort(key=lambda x: x.get('created', ''), reverse=True)
            latest_date = None
            
            for file_info in backup_files:
                if 'btc-data/' in file_info['name']:
                    # Extract date from path
                    path_parts = file_info['name'].split('/')
                    if len(path_parts) >= 3:
                        date_part = f"{path_parts[1]}/{path_parts[2]}"
                        if latest_date != date_part:
                            latest_date = date_part
                            break
            
            if not latest_date:
                return {'error': 'No valid backup found'}
            
            # Restore files from latest backup
            restored_files = []
            failed_files = []
            
            logger.info(f"🔄 Restoring backup from {latest_date} using {provider_name}")
            
            for file_info in backup_files:
                if latest_date in file_info['name'] and not file_info['name'].endswith('backup-summary.json'):
                    filename = Path(file_info['name']).name
                    local_path = target_path / filename
                    
                    if provider.download_file(file_info['name'], str(local_path)):
                        restored_files.append(str(local_path))
                    else:
                        failed_files.append(file_info['name'])
            
            result = {
                'provider': provider_name,
                'backup_date': latest_date,
                'restored_files': restored_files,
                'failed_files': failed_files,
                'success': len(restored_files) > 0
            }
            
            if restored_files:
                logger.info(f"✅ Restored {len(restored_files)} files from {provider_name}")
            else:
                logger.error(f"❌ No files restored from {provider_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return {'error': str(e)}
    
    def check_and_backup_if_needed(self):
        """Check if backup is needed and perform it"""
        if not self.backup_enabled or self.backup_running:
            return
        
        current_time = datetime.now(UTC)
        
        # Check if enough time has passed
        if self.last_backup_time is None:
            should_backup = True
        else:
            time_diff = (current_time - self.last_backup_time).total_seconds() / 60
            should_backup = time_diff >= self.backup_interval
        
        if should_backup:
            logger.info("⏰ Automatic backup triggered")
            result = self.backup_all_data()
            return result
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get current backup system status"""
        return {
            'backup_enabled': self.backup_enabled,
            'backup_interval_minutes': self.backup_interval,
            'last_backup_time': self.last_backup_time.isoformat() if self.last_backup_time else None,
            'backup_running': self.backup_running,
            'available_providers': self.get_available_providers(),
            'data_folder': str(self.data_folder),
            'stats': self.backup_stats
        }
    
    def cleanup_old_backups(self, provider_name: str, keep_count: int = None):
        """Clean up old backups, keeping only the most recent ones"""
        if keep_count is None:
            keep_count = self.max_local_backups
        
        if provider_name not in self.providers:
            return {'error': f'Provider {provider_name} not found'}
        
        provider = self.providers[provider_name]
        
        try:
            # Get all backup files
            backup_files = provider.list_files("btc-data/")
            
            # Group by date/time
            backup_groups = {}
            for file_info in backup_files:
                path_parts = file_info['name'].split('/')
                if len(path_parts) >= 3:
                    group_key = f"{path_parts[1]}/{path_parts[2]}"
                    if group_key not in backup_groups:
                        backup_groups[group_key] = []
                    backup_groups[group_key].append(file_info)
            
            # Sort groups by date and remove old ones
            sorted_groups = sorted(backup_groups.keys(), reverse=True)
            groups_to_delete = sorted_groups[keep_count:]
            
            deleted_files = []
            for group in groups_to_delete:
                for file_info in backup_groups[group]:
                    if provider.delete_file(file_info['name']):
                        deleted_files.append(file_info['name'])
            
            return {
                'provider': provider_name,
                'deleted_files': deleted_files,
                'remaining_backups': len(sorted_groups) - len(groups_to_delete)
            }
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            return {'error': str(e)}

# Global backup system instance
_backup_system = None

def get_backup_system() -> EnhancedBackupSystem:
    """Get or create backup system instance"""
    global _backup_system
    if _backup_system is None:
        _backup_system = EnhancedBackupSystem()
    return _backup_system

def auto_backup_enhanced():
    """Enhanced automatic backup function"""
    backup_system = get_backup_system()
    return backup_system.check_and_backup_if_needed()

def restore_data_after_crash():
    """Automatically restore data after a crash"""
    backup_system = get_backup_system()
    available_providers = backup_system.get_available_providers()
    
    if not available_providers:
        logger.error("❌ No backup providers available for restore")
        return False
    
    # Try each provider until successful
    for provider in available_providers:
        logger.info(f"🔄 Attempting restore from {provider}")
        result = backup_system.restore_latest_backup(provider)
        if result.get('success'):
            logger.info(f"✅ Successfully restored from {provider}")
            return True
    
    logger.error("❌ Failed to restore from any provider")
    return False