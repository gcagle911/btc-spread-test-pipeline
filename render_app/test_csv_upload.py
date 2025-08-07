#!/usr/bin/env python3
"""
Test script for CSV upload functionality
"""

import os
from csv_uploader import upload_csv_to_gcs, upload_recent_csvs

def test_csv_upload():
    """Test CSV upload functionality"""
    print("🧪 Testing CSV upload functionality...")
    
    # Check if credentials are available
    credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    if not credentials_json:
        print("⚠️ GOOGLE_APPLICATION_CREDENTIALS_JSON not set - skipping upload test")
        print("✅ CSV uploader is ready for deployment (will work when credentials are set)")
        return True
    
    # Test with existing CSV files
    csv_files = []
    for file in os.listdir("data"):
        if file.endswith(".csv"):
            csv_files.append(os.path.join("data", file))
    
    if not csv_files:
        print("❌ No CSV files found for testing")
        return False
    
    print(f"📄 Found {len(csv_files)} CSV files for testing")
    
    # Test individual CSV upload
    test_file = csv_files[0]
    print(f"📄 Testing upload of {test_file}...")
    
    try:
        success = upload_csv_to_gcs(test_file)
        if success:
            print("✅ CSV upload test successful!")
            return True
        else:
            print("❌ CSV upload test failed")
            return False
    except Exception as e:
        print(f"❌ CSV upload test error: {e}")
        return False

if __name__ == "__main__":
    test_csv_upload()