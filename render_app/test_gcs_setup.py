#!/usr/bin/env python3
"""
Test Google Cloud Storage Setup
Validates that GCS backup is configured correctly
"""

import os
import sys
from datetime import datetime

def test_environment_variables():
    """Test that required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = ['GCS_BUCKET_NAME', 'GCP_PROJECT_ID']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var} = {value}")
        else:
            print(f"  ❌ {var} (missing)")
            missing_vars.append(var)
    
    # Check authentication
    auth_methods = []
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON'):
        auth_methods.append("Environment JSON")
        print("  ✅ GOOGLE_APPLICATION_CREDENTIALS_JSON (set)")
    
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if os.path.exists(creds_path):
            auth_methods.append("Credentials file")
            print(f"  ✅ GOOGLE_APPLICATION_CREDENTIALS = {creds_path}")
        else:
            print(f"  ❌ GOOGLE_APPLICATION_CREDENTIALS file not found: {creds_path}")
    
    if not auth_methods:
        print("  ❌ No authentication method configured")
        missing_vars.append("GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_JSON")
    
    return len(missing_vars) == 0

def test_gcs_connection():
    """Test connection to Google Cloud Storage"""
    print("\n🌐 Testing Google Cloud Storage connection...")
    
    try:
        from enhanced_backup_system import GCSBackupProvider
        
        # Initialize GCS provider
        gcs = GCSBackupProvider()
        
        if not gcs.is_available():
            print("  ❌ GCS provider not available")
            return False
        
        print(f"  ✅ Connected to bucket: {gcs.bucket_name}")
        
        # Test bucket access
        try:
            # Try to list objects (this tests read permission)
            files = gcs.list_files("test/")
            print(f"  ✅ Bucket access verified (found {len(files)} test files)")
        except Exception as e:
            print(f"  ⚠️ Bucket access test failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False

def test_backup_functionality():
    """Test actual backup functionality"""
    print("\n🧪 Testing backup functionality...")
    
    try:
        from enhanced_backup_system import get_backup_system
        
        backup_system = get_backup_system()
        providers = backup_system.get_available_providers()
        
        print(f"  📦 Available providers: {', '.join(providers)}")
        
        if 'gcs' not in providers:
            print("  ❌ GCS provider not available in backup system")
            return False
        
        print("  ✅ GCS provider available in backup system")
        
        # Test creating a small test backup
        try:
            import tempfile
            import json
            
            # Create a test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                test_data = {
                    "test": True,
                    "timestamp": datetime.now().isoformat(),
                    "message": "GCS backup test"
                }
                json.dump(test_data, f)
                test_file = f.name
            
            # Try to backup the test file
            gcs_provider = backup_system.providers['gcs']
            test_path = f"test/gcs-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            
            if gcs_provider.upload_file(test_file, test_path):
                print("  ✅ Test file uploaded successfully")
                
                # Try to list and verify
                files = gcs_provider.list_files("test/")
                test_files = [f for f in files if 'gcs-test' in f['name']]
                if test_files:
                    print(f"  ✅ Test file found in bucket: {test_files[0]['name']}")
                
                # Clean up test file
                if gcs_provider.delete_file(test_path):
                    print("  ✅ Test file cleaned up")
                
                return True
            else:
                print("  ❌ Test file upload failed")
                return False
                
        except Exception as e:
            print(f"  ❌ Backup test failed: {e}")
            return False
        finally:
            # Clean up local test file
            try:
                os.unlink(test_file)
            except:
                pass
                
    except Exception as e:
        print(f"  ❌ Backup system test failed: {e}")
        return False

def show_next_steps(success):
    """Show appropriate next steps"""
    print("\n" + "="*50)
    
    if success:
        print("🎉 Google Cloud Storage is configured correctly!")
        print("\n✅ Your backups will now survive:")
        print("   • App crashes")
        print("   • Server restarts") 
        print("   • Code deployments")
        print("   • Render redeploys")
        print("\n📊 Monitor your backups:")
        print("   • Dashboard: /dashboard")
        print("   • Health: /health")
        print("   • Manual backup: curl -X POST /backup/enhanced/trigger")
    else:
        print("❌ Google Cloud Storage setup needs attention")
        print("\n🔧 Next steps:")
        print("   1. Check environment variables")
        print("   2. Verify service account permissions")
        print("   3. Test bucket access")
        print("   4. Review setup guide: GOOGLE_CLOUD_SETUP.md")

def main():
    print("="*50)
    print("🌐 Google Cloud Storage Setup Test")
    print("="*50)
    
    # Test 1: Environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment variables not configured properly")
        show_next_steps(False)
        return False
    
    # Test 2: GCS connection
    connection_ok = test_gcs_connection()
    
    if not connection_ok:
        print("\n❌ Could not connect to Google Cloud Storage")
        show_next_steps(False)
        return False
    
    # Test 3: Backup functionality
    backup_ok = test_backup_functionality()
    
    # Show results
    success = env_ok and connection_ok and backup_ok
    show_next_steps(success)
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)