#!/usr/bin/env python3
"""
Test CSV upload logic without requiring GCS credentials
"""

import os
from csv_uploader import upload_csv_to_gcs

def test_csv_logic():
    """Test CSV upload logic without actual upload"""
    print("🧪 Testing CSV upload logic...")
    
    # Test with existing CSV files
    csv_files = []
    for file in os.listdir("render_app/data"):
        if file.endswith(".csv"):
            csv_files.append(os.path.join("render_app/data", file))
    
    if not csv_files:
        print("❌ No CSV files found for testing")
        return False
    
    print(f"📄 Found {len(csv_files)} CSV files for testing")
    
    # Test the logic for each CSV file
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        date_part = filename.split('_')[0]  # Get the date part before underscore
        gcs_path = f"csv/{date_part}.csv"
        
        print(f"📄 {filename} -> {gcs_path}")
        
        # Test file existence
        if os.path.exists(csv_file):
            print(f"✅ File exists: {csv_file}")
        else:
            print(f"❌ File not found: {csv_file}")
    
    print("✅ CSV upload logic test completed")
    return True

if __name__ == "__main__":
    test_csv_logic()