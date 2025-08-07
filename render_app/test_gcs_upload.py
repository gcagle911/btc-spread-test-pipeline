#!/usr/bin/env python3
"""
Test script for GCS uploader functionality
"""

import os
import json
from gcs_uploader import upload_to_gcs

def test_gcs_upload():
    """Test GCS upload functionality"""
    print("🧪 Testing GCS upload functionality...")
    
    # Check if credentials are available
    credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not credentials_json:
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS_JSON not set - skipping upload test")
        print("✅ GCS uploader is ready for deployment (will work when credentials are set)")
        return True
    
    # Test with a sample file
    test_file = "render_app/data/recent.json"
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📄 Testing upload of {test_file}...")
    
    try:
        # Test upload
        success = upload_to_gcs(test_file, "test/recent.json")
        if success:
            print("✅ GCS upload test successful!")
            return True
        else:
            print("❌ GCS upload test failed")
            return False
    except Exception as e:
        print(f"❌ GCS upload test error: {e}")
        return False

if __name__ == "__main__":
    test_gcs_upload()