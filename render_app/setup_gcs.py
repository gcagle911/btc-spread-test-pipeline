#!/usr/bin/env python3
"""
Google Cloud Storage Setup Script for BTC Historical Data Backup
This script helps you configure GCS backup for your BTC logger application.
"""

import os
import json
import sys
from google.cloud import storage
from google.oauth2 import service_account

def print_header():
    print("=" * 60)
    print("🌟 BTC Logger - Google Cloud Storage Setup 🌟")
    print("=" * 60)
    print()

def check_gcp_cli():
    """Check if gcloud CLI is installed"""
    try:
        import subprocess
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Google Cloud CLI is installed")
            return True
        else:
            print("❌ Google Cloud CLI not found")
            return False
    except FileNotFoundError:
        print("❌ Google Cloud CLI not found")
        return False

def setup_service_account():
    """Guide user through service account setup"""
    print("\n📋 Service Account Setup")
    print("-" * 30)
    print("To use Google Cloud Storage backup, you need a service account.")
    print("Follow these steps:")
    print()
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Select or create a project")
    print("3. Go to IAM & Admin > Service Accounts")
    print("4. Click 'Create Service Account'")
    print("5. Give it a name like 'btc-logger-backup'")
    print("6. Grant it 'Storage Admin' role")
    print("7. Create and download the JSON key file")
    print()
    
    key_path = input("Enter the path to your service account JSON key file: ").strip()
    
    if not os.path.exists(key_path):
        print(f"❌ File not found: {key_path}")
        return None
    
    try:
        with open(key_path, 'r') as f:
            key_data = json.load(f)
        
        # Validate the key file
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in key_data:
                print(f"❌ Invalid service account key file (missing {field})")
                return None
        
        print("✅ Service account key file is valid")
        return key_path, key_data['project_id']
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON file")
        return None
    except Exception as e:
        print(f"❌ Error reading key file: {e}")
        return None

def setup_bucket(project_id, key_path):
    """Setup GCS bucket"""
    print("\n🪣 Bucket Setup")
    print("-" * 15)
    
    # Initialize GCS client
    try:
        credentials = service_account.Credentials.from_service_account_file(key_path)
        client = storage.Client(credentials=credentials, project=project_id)
        print("✅ Connected to Google Cloud Storage")
    except Exception as e:
        print(f"❌ Failed to connect to GCS: {e}")
        return None
    
    # Get bucket name
    bucket_name = input("Enter a bucket name (must be globally unique): ").strip().lower()
    
    # Validate bucket name
    if not bucket_name:
        print("❌ Bucket name cannot be empty")
        return None
    
    # Check if bucket exists
    try:
        bucket = client.bucket(bucket_name)
        if bucket.exists():
            print(f"✅ Bucket '{bucket_name}' already exists and is accessible")
            return bucket_name
        else:
            # Try to create bucket
            create = input(f"Bucket '{bucket_name}' doesn't exist. Create it? (y/n): ").strip().lower()
            if create in ['y', 'yes']:
                try:
                    # Create bucket in US region (you can change this)
                    bucket = client.create_bucket(bucket_name, location='US')
                    print(f"✅ Created bucket '{bucket_name}'")
                    return bucket_name
                except Exception as e:
                    print(f"❌ Failed to create bucket: {e}")
                    print("   Try a different name or create the bucket manually in GCP Console")
                    return None
            else:
                print("❌ Bucket creation cancelled")
                return None
    
    except Exception as e:
        print(f"❌ Error checking bucket: {e}")
        return None

def create_env_file(project_id, bucket_name, key_path):
    """Create environment configuration file"""
    print("\n⚙️ Environment Configuration")
    print("-" * 30)
    
    # Move key file to a standard location if needed
    project_root = os.path.dirname(os.path.abspath(__file__))
    key_filename = "gcs-service-account.json"
    target_key_path = os.path.join(project_root, key_filename)
    
    # Copy key file if it's not already in the project directory
    if os.path.abspath(key_path) != os.path.abspath(target_key_path):
        try:
            import shutil
            shutil.copy2(key_path, target_key_path)
            print(f"✅ Copied service account key to: {target_key_path}")
        except Exception as e:
            print(f"⚠️ Could not copy key file: {e}")
            print(f"   Using original path: {key_path}")
            target_key_path = key_path
    
    # Create .env file
    env_content = f"""# Google Cloud Storage Backup Configuration
# Generated by setup_gcs.py

# Required: Your GCS bucket name
GCS_BUCKET_NAME={bucket_name}

# Required: Path to service account JSON key file
GOOGLE_APPLICATION_CREDENTIALS={target_key_path}

# Optional: GCP Project ID (usually auto-detected from service account)
GCP_PROJECT_ID={project_id}

# Optional: Enable/disable backup (default: true)
GCS_BACKUP_ENABLED=true

# Optional: Backup interval in minutes (default: 30)
BACKUP_INTERVAL_MINUTES=30
"""
    
    env_file_path = os.path.join(project_root, '.env')
    
    try:
        with open(env_file_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created environment file: {env_file_path}")
        print()
        print("🔒 Security Note:")
        print("   - Add '.env' and '*.json' to your .gitignore file")
        print("   - Never commit service account keys to version control")
        
        return env_file_path
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return None

def test_backup():
    """Test the backup configuration"""
    print("\n🧪 Testing Backup Configuration")
    print("-" * 35)
    
    try:
        # Load environment
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
        
        # Import and test backup module
        from gcs_backup import GCSBackup
        
        backup = GCSBackup()
        print(f"✅ GCS client initialized successfully")
        print(f"   Bucket: {backup.bucket_name}")
        print(f"   Project: {backup.project_id}")
        
        # Test upload a small test file
        test_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_backup.txt')
        with open(test_file_path, 'w') as f:
            f.write(f"Test backup file created at {os.environ.get('TZ', 'UTC')}")
        
        success = backup.upload_file(test_file_path, 'test/backup-test.txt')
        
        # Clean up test file
        os.remove(test_file_path)
        
        if success:
            print("✅ Test backup upload successful!")
            print("   Your backup system is ready to use.")
            return True
        else:
            print("❌ Test backup upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Backup test failed: {e}")
        return False

def main():
    """Main setup function"""
    print_header()
    
    # Check prerequisites
    if not check_gcp_cli():
        print("⚠️ Google Cloud CLI is recommended but not required")
        print("   You can still use service account authentication")
        print()
    
    # Setup service account
    sa_result = setup_service_account()
    if not sa_result:
        print("❌ Setup cancelled")
        return
    
    key_path, project_id = sa_result
    
    # Setup bucket
    bucket_name = setup_bucket(project_id, key_path)
    if not bucket_name:
        print("❌ Setup cancelled")
        return
    
    # Create environment configuration
    env_file = create_env_file(project_id, bucket_name, key_path)
    if not env_file:
        print("❌ Setup cancelled")
        return
    
    # Test the configuration
    if test_backup():
        print("\n🎉 Setup Complete!")
        print("-" * 20)
        print("Your BTC logger is now configured to automatically backup data to Google Cloud Storage.")
        print()
        print("📈 How to use:")
        print("   1. Start your logger: python3 logger.py")
        print("   2. Check backup status: curl http://localhost:10000/backup/status")
        print("   3. Manual backup: curl -X POST http://localhost:10000/backup")
        print("   4. List backups: curl http://localhost:10000/backup/list")
        print()
        print("🔧 Configuration files created:")
        print(f"   - Environment: {env_file}")
        print(f"   - Service key: {key_path}")
        print()
        print("Happy trading! 📊")
    else:
        print("\n❌ Setup completed with errors")
        print("   Please check the configuration and try running the test again")

if __name__ == "__main__":
    main()