"""
Google Cloud Storage Backup Module for BTC Historical Data
Automatically backs up all generated data files to Google Cloud Storage
"""

import os
import json
import glob
from datetime import datetime, UTC
from google.cloud import storage
from google.oauth2 import service_account
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GCSBackup:
    def __init__(self, bucket_name=None, service_account_path=None, project_id=None):
        """
        Initialize GCS backup client
        
        Args:
            bucket_name: GCS bucket name (or set GCS_BUCKET_NAME env var)
            service_account_path: Path to service account JSON (or set GOOGLE_APPLICATION_CREDENTIALS env var)
            project_id: GCP project ID (or set GCP_PROJECT_ID env var)
        """
        # Get configuration from environment variables or parameters
        self.bucket_name = bucket_name or os.getenv('GCS_BUCKET_NAME')
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID')
        
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable or bucket_name parameter is required")
        
        # Initialize GCS client
        try:
            if service_account_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                # Use service account authentication
                creds_path = service_account_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                credentials = service_account.Credentials.from_service_account_file(creds_path)
                self.client = storage.Client(credentials=credentials, project=self.project_id)
            else:
                # Use default authentication (for Google Cloud environments)
                self.client = storage.Client(project=self.project_id)
            
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"✅ GCS client initialized for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize GCS client: {e}")
            raise
    
    def upload_file(self, local_path, gcs_path=None, metadata=None):
        """
        Upload a single file to GCS
        
        Args:
            local_path: Local file path
            gcs_path: GCS destination path (defaults to filename with timestamp prefix)
            metadata: Optional metadata dict to attach to the blob
        """
        try:
            if not os.path.exists(local_path):
                logger.warning(f"⚠️ File not found: {local_path}")
                return False
            
            # Generate GCS path if not provided
            if not gcs_path:
                timestamp = datetime.now(UTC).strftime("%Y-%m-%d")
                filename = os.path.basename(local_path)
                gcs_path = f"btc-data/{timestamp}/{filename}"
            
            # Create blob and upload
            blob = self.bucket.blob(gcs_path)
            
            # Add metadata
            if metadata:
                blob.metadata = metadata
            
            # Add standard metadata
            blob.metadata = blob.metadata or {}
            blob.metadata.update({
                'upload_timestamp': datetime.now(UTC).isoformat(),
                'source': 'btc-historical-logger',
                'file_size': str(os.path.getsize(local_path))
            })
            
            blob.upload_from_filename(local_path)
            logger.info(f"✅ Uploaded: {local_path} → gs://{self.bucket_name}/{gcs_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Upload failed for {local_path}: {e}")
            return False
    
    def backup_data_folder(self, data_folder="render_app/data", file_patterns=None):
        """
        Backup entire data folder to GCS
        
        Args:
            data_folder: Local data folder path
            file_patterns: List of file patterns to backup (default: all files)
        """
        if file_patterns is None:
            file_patterns = ["*.csv", "*.json"]
        
        uploaded_files = []
        failed_files = []
        
        logger.info(f"🔄 Starting backup of data folder: {data_folder}")
        
        for pattern in file_patterns:
            files = glob.glob(os.path.join(data_folder, pattern))
            
            for file_path in files:
                # Create organized GCS path structure
                filename = os.path.basename(file_path)
                file_ext = os.path.splitext(filename)[1].lstrip('.')
                timestamp = datetime.now(UTC).strftime("%Y-%m-%d/%H")
                
                gcs_path = f"btc-data/{timestamp}/{file_ext}/{filename}"
                
                # Add file-specific metadata
                metadata = {
                    'file_type': file_ext,
                    'original_path': file_path
                }
                
                if self.upload_file(file_path, gcs_path, metadata):
                    uploaded_files.append(file_path)
                else:
                    failed_files.append(file_path)
        
        # Create backup summary
        summary = {
            'backup_timestamp': datetime.now(UTC).isoformat(),
            'total_files': len(uploaded_files) + len(failed_files),
            'successful_uploads': len(uploaded_files),
            'failed_uploads': len(failed_files),
            'uploaded_files': uploaded_files,
            'failed_files': failed_files
        }
        
        # Upload backup summary
        summary_path = f"btc-data/{datetime.now(UTC).strftime('%Y-%m-%d/%H')}/backup-summary.json"
        self._upload_json_data(summary, summary_path)
        
        logger.info(f"📊 Backup complete: {len(uploaded_files)} successful, {len(failed_files)} failed")
        return summary
    
    def _upload_json_data(self, data, gcs_path):
        """Helper method to upload JSON data directly to GCS"""
        try:
            blob = self.bucket.blob(gcs_path)
            blob.metadata = {
                'upload_timestamp': datetime.now(UTC).isoformat(),
                'content_type': 'application/json'
            }
            blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
            logger.info(f"✅ Uploaded JSON data → gs://{self.bucket_name}/{gcs_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to upload JSON data to {gcs_path}: {e}")
            return False
    
    def backup_specific_files(self, file_list):
        """
        Backup specific files to GCS
        
        Args:
            file_list: List of file paths to backup
        """
        results = []
        for file_path in file_list:
            success = self.upload_file(file_path)
            results.append({'file': file_path, 'success': success})
        return results
    
    def list_backups(self, prefix="btc-data/"):
        """List all backup files in GCS bucket"""
        try:
            blobs = self.client.list_blobs(self.bucket, prefix=prefix)
            backup_files = []
            
            for blob in blobs:
                backup_files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'metadata': blob.metadata
                })
            
            logger.info(f"📋 Found {len(backup_files)} backup files")
            return backup_files
            
        except Exception as e:
            logger.error(f"❌ Failed to list backups: {e}")
            return []
    
    def download_backup(self, gcs_path, local_path):
        """Download a backup file from GCS"""
        try:
            blob = self.bucket.blob(gcs_path)
            blob.download_to_filename(local_path)
            logger.info(f"✅ Downloaded: gs://{self.bucket_name}/{gcs_path} → {local_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return False


# Global backup instance
_gcs_backup = None

def get_gcs_backup():
    """Get or create GCS backup instance"""
    global _gcs_backup
    if _gcs_backup is None:
        try:
            _gcs_backup = GCSBackup()
        except Exception as e:
            logger.error(f"❌ Could not initialize GCS backup: {e}")
            _gcs_backup = None
    return _gcs_backup

def auto_backup_data():
    """Automatically backup all data files - called from main application"""
    backup = get_gcs_backup()
    if backup:
        return backup.backup_data_folder()
    else:
        logger.warning("⚠️ GCS backup not available - check configuration")
        return None

def backup_file(file_path):
    """Backup a single file - convenience function"""
    backup = get_gcs_backup()
    if backup:
        return backup.upload_file(file_path)
    return False