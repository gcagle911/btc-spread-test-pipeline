#!/usr/bin/env python3
"""
Manual CSV upload script for testing
"""

import os
import sys
from datetime import datetime, timezone

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def manual_csv_upload():
    """Manually upload all existing CSV files to GCS"""
    print("🚀 Manual CSV upload to GCS...")
    
    try:
        from csv_uploader import upload_all_csvs
        
        # Upload all CSV files
        result = upload_all_csvs()
        
        print(f"📊 Upload Summary:")
        print(f"  - Total files: {result['total']}")
        print(f"  - Uploaded: {result['uploaded']}")
        print(f"  - Failed: {result['failed']}")
        
        if result['uploaded'] > 0:
            print("✅ CSV files uploaded successfully!")
        else:
            print("❌ No CSV files were uploaded (check GCS credentials)")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during manual CSV upload: {e}")
        return None

if __name__ == "__main__":
    manual_csv_upload()