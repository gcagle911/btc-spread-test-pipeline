#!/usr/bin/env python3
"""
Manual test for CSV upload functionality
"""

import os
import sys
from datetime import datetime, timezone

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_csv_upload():
    """Test CSV upload functionality manually"""
    print("🧪 Testing CSV upload functionality...")
    
    try:
        from csv_uploader import upload_csv_to_gcs, upload_recent_csvs, upload_all_csvs
        
        # Check for CSV files
        data_folder = "render_app/data"
        csv_files = []
        
        if os.path.exists(data_folder):
            for file in os.listdir(data_folder):
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(data_folder, file))
        
        if not csv_files:
            print("❌ No CSV files found in data directory")
            return False
        
        print(f"📄 Found {len(csv_files)} CSV files:")
        for csv_file in csv_files:
            print(f"  - {os.path.basename(csv_file)}")
        
        # Test individual CSV upload
        print(f"\n🔄 Testing individual CSV upload for {os.path.basename(csv_files[0])}...")
        result = upload_csv_to_gcs(csv_files[0])
        print(f"Individual upload result: {result}")
        
        # Test recent CSV uploads
        print(f"\n🔄 Testing recent CSV uploads...")
        result = upload_recent_csvs()
        print(f"Recent uploads result: {result}")
        
        # Test all CSV uploads
        print(f"\n🔄 Testing all CSV uploads...")
        result = upload_all_csvs()
        print(f"All uploads result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing CSV upload: {e}")
        return False

if __name__ == "__main__":
    test_csv_upload()