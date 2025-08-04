#!/usr/bin/env python3
"""
Startup Restore Script for BTC Logger
Automatically detects if data is missing and restores from backup
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, UTC
from enhanced_backup_system import get_backup_system, restore_data_after_crash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_data_integrity(data_folder: str = "render_app/data") -> dict:
    """Check if data files exist and are recent"""
    data_path = Path(data_folder)
    
    if not data_path.exists():
        return {
            'status': 'missing',
            'message': 'Data folder does not exist',
            'needs_restore': True
        }
    
    # Check for critical files
    csv_files = list(data_path.glob("*.csv"))
    json_files = list(data_path.glob("*.json"))
    
    if not csv_files and not json_files:
        return {
            'status': 'empty',
            'message': 'No data files found',
            'needs_restore': True
        }
    
    # Check for critical JSON files and their content
    historical_path = data_path / "historical.json"
    if historical_path.exists():
        file_size = historical_path.stat().st_size
        if file_size < 100:  # Historical file should be much larger
            return {
                'status': 'incomplete',
                'message': f'Historical file too small ({file_size} bytes) - likely empty',
                'needs_restore': True
            }
    
    # Check if files are recent (within last 2 hours)
    recent_threshold = datetime.now(UTC).timestamp() - (2 * 60 * 60)  # 2 hours ago
    recent_files = []
    
    for file_path in csv_files + json_files:
        if file_path.stat().st_mtime > recent_threshold:
            recent_files.append(file_path.name)
    
    if not recent_files:
        return {
            'status': 'stale',
            'message': f'No recent files found (checked {len(csv_files + json_files)} files)',
            'needs_restore': True,
            'file_count': len(csv_files + json_files)
        }
    
    return {
        'status': 'healthy',
        'message': f'Found {len(recent_files)} recent files',
        'needs_restore': False,
        'recent_files': recent_files,
        'total_files': len(csv_files + json_files)
    }

def attempt_restore() -> bool:
    """Attempt to restore data from available backup providers"""
    logger.info("🔄 Starting data restoration process...")
    
    backup_system = get_backup_system()
    available_providers = backup_system.get_available_providers()
    
    if not available_providers:
        logger.error("❌ No backup providers available")
        return False
    
    logger.info(f"📋 Available backup providers: {available_providers}")
    
    # Try each provider in order of preference
    provider_priority = ['gcs', 'local']  # Prefer cloud backup first
    
    for provider in provider_priority:
        if provider in available_providers:
            logger.info(f"🔄 Attempting restore from {provider}...")
            
            try:
                result = backup_system.restore_latest_backup(provider)
                
                if result.get('success'):
                    restored_files = result.get('restored_files', [])
                    logger.info(f"✅ Successfully restored {len(restored_files)} files from {provider}")
                    
                    # Log restored files
                    for file_path in restored_files:
                        logger.info(f"   📄 Restored: {file_path}")
                    
                    return True
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.warning(f"⚠️ Restore from {provider} failed: {error_msg}")
                    
            except Exception as e:
                logger.error(f"❌ Error during restore from {provider}: {e}")
    
    logger.error("❌ Failed to restore from any provider")
    return False

def setup_environment():
    """Set up environment variables and configuration"""
    # Ensure data directory exists
    data_dir = Path("render_app/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set default environment variables if not already set
    env_defaults = {
        'BACKUP_ENABLED': 'true',
        'BACKUP_INTERVAL_MINUTES': '30',
        'MAX_LOCAL_BACKUPS': '10',
        'AUTO_RESTORE_ON_STARTUP': 'true'
    }
    
    for key, value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = value
            logger.info(f"🔧 Set default environment variable: {key}={value}")

def startup_check():
    """Main startup check and restore function"""
    logger.info("🚀 Starting BTC Logger startup check...")
    
    # Setup environment
    setup_environment()
    
    # Check if auto-restore is enabled
    auto_restore = os.getenv('AUTO_RESTORE_ON_STARTUP', 'true').lower() in ['true', '1', 'yes']
    
    if not auto_restore:
        logger.info("ℹ️ Auto-restore is disabled, skipping data check")
        return True
    
    # Check data integrity
    integrity_check = check_data_integrity()
    logger.info(f"📊 Data integrity check: {integrity_check['status']} - {integrity_check['message']}")
    
    restore_attempted = False
    
    if integrity_check['needs_restore']:
        # Attempt restore
        logger.warning(f"⚠️ Data issue detected: {integrity_check['message']}")
        logger.info("🔄 Attempting to restore from backup...")
        
        if attempt_restore():
            # Verify restoration was successful
            post_restore_check = check_data_integrity()
            if not post_restore_check['needs_restore']:
                logger.info("✅ Data successfully restored from backup")
                restore_attempted = True
            else:
                logger.error("❌ Data restore verification failed")
                return False
        else:
            logger.error("❌ Failed to restore data from any backup source")
            return False
    
    # Always force a data rebuild after startup to ensure proper file generation
    # This is crucial after Render redeploys to rebuild historical.json from CSV data
    logger.info("🔄 Forcing data rebuild to ensure historical files are properly generated...")
    try:
        from process_data import process_csv_to_json
        
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        process_csv_to_json()
        logger.info("✅ Data rebuild completed successfully")
        
        # Verify the rebuild worked
        final_check = check_data_integrity()
        if final_check['needs_restore']:
            logger.warning(f"⚠️ After rebuild, data still shows issues: {final_check['message']}")
        else:
            logger.info("✅ Final data check passed - all files properly generated")
            
    except Exception as e:
        logger.error(f"❌ Error during data rebuild: {e}")
        # Don't fail startup for rebuild errors, just log them
        logger.info("⚠️ Continuing startup despite rebuild error...")
    
    return True

def create_health_check_endpoint():
    """Create a simple health check that includes backup status"""
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/health')
    def health_check():
        backup_system = get_backup_system()
        integrity_check = check_data_integrity()
        backup_status = backup_system.get_backup_status()
        
        return jsonify({
            'status': 'healthy' if not integrity_check['needs_restore'] else 'degraded',
            'data_integrity': integrity_check,
            'backup_status': backup_status,
            'timestamp': datetime.now(UTC).isoformat()
        })
    
    @app.route('/restore')
    def manual_restore():
        try:
            if attempt_restore():
                return jsonify({'success': True, 'message': 'Data restored successfully'})
            else:
                return jsonify({'success': False, 'message': 'Restore failed'}), 500
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return app

if __name__ == "__main__":
    # Run startup check
    success = startup_check()
    
    if success:
        logger.info("🎉 Startup check completed successfully")
        sys.exit(0)
    else:
        logger.error("💥 Startup check failed")
        sys.exit(1)