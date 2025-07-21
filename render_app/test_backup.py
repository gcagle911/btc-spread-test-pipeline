#!/usr/bin/env python3
"""
Test script for Google Cloud Storage backup functionality
Run this to verify your backup configuration is working correctly.
"""

import os
import sys
import json
from datetime import datetime

def test_backup_configuration():
    """Test if backup is properly configured"""
    print("🧪 Testing GCS Backup Configuration")
    print("=" * 40)
    
    # Check environment variables
    required_vars = ['GCS_BUCKET_NAME']
    optional_vars = ['GOOGLE_APPLICATION_CREDENTIALS', 'GCP_PROJECT_ID']
    
    print("\n📋 Environment Variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set (REQUIRED)")
            return False
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: Not set (optional)")
    
    return True

def test_gcs_connection():
    """Test connection to Google Cloud Storage"""
    print("\n🔗 Testing GCS Connection:")
    
    try:
        from gcs_backup import GCSBackup
        backup = GCSBackup()
        print(f"✅ Connected to bucket: {backup.bucket_name}")
        print(f"✅ Project ID: {backup.project_id}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_file_upload():
    """Test uploading a file"""
    print("\n📤 Testing File Upload:")
    
    # Create a test file
    test_file = "test_backup_file.txt"
    test_content = f"Test backup file created at {datetime.now()}"
    
    try:
        with open(test_file, 'w') as f:
            f.write(test_content)
        print(f"✅ Created test file: {test_file}")
        
        # Upload the file
        from gcs_backup import backup_file
        success = backup_file(test_file)
        
        if success:
            print(f"✅ Successfully uploaded {test_file} to GCS")
        else:
            print(f"❌ Failed to upload {test_file}")
            return False
        
        # Clean up
        os.remove(test_file)
        print(f"✅ Cleaned up test file")
        
        return True
        
    except Exception as e:
        print(f"❌ Upload test failed: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

def test_data_backup():
    """Test backing up data folder"""
    print("\n📁 Testing Data Folder Backup:")
    
    try:
        from gcs_backup import auto_backup_data
        result = auto_backup_data()
        
        if result:
            print(f"✅ Backup completed successfully")
            print(f"   Files uploaded: {result['successful_uploads']}")
            print(f"   Files failed: {result['failed_uploads']}")
            return True
        else:
            print(f"❌ Backup failed or no data to backup")
            return False
            
    except Exception as e:
        print(f"❌ Data backup test failed: {e}")
        return False

def test_backup_listing():
    """Test listing backups"""
    print("\n📋 Testing Backup Listing:")
    
    try:
        from gcs_backup import get_gcs_backup
        backup = get_gcs_backup()
        
        if backup:
            backups = backup.list_backups()
            print(f"✅ Found {len(backups)} backup files")
            
            # Show latest 3 backups
            if backups:
                print("   Latest backups:")
                for backup_file in sorted(backups, key=lambda x: x.get('created', ''), reverse=True)[:3]:
                    name = backup_file['name']
                    size = backup_file.get('size', 0)
                    created = backup_file.get('created', 'Unknown')
                    print(f"   📄 {name} ({size} bytes, {created})")
            
            return True
        else:
            print(f"❌ Could not list backups")
            return False
            
    except Exception as e:
        print(f"❌ Backup listing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 BTC Logger - GCS Backup Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration Check", test_backup_configuration),
        ("GCS Connection", test_gcs_connection),
        ("File Upload", test_file_upload),
        ("Data Backup", test_data_backup),
        ("Backup Listing", test_backup_listing)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
        
        print()  # Add spacing between tests
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 25)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Your backup system is ready to use.")
        print("\nNext steps:")
        print("1. Start your logger: python3 logger.py")
        print("2. Check backup status: curl http://localhost:10000/backup/status")
    else:
        print("\n⚠️ Some tests failed. Please check your configuration.")
        print("\nTroubleshooting:")
        print("1. Make sure you've run: python3 setup_gcs.py")
        print("2. Check your .env file has the correct values")
        print("3. Verify your service account has proper permissions")

if __name__ == "__main__":
    main()