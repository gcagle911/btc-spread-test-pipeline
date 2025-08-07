#!/usr/bin/env python3
"""
Test script for scalable JSON generation system
"""

import json
import os
from scalable_json_generator import generate_all_jsons, DATA_FOLDER, ARCHIVE_FOLDER

def test_json_generation():
    """Test the scalable JSON generation system"""
    print("🧪 Testing scalable JSON generation system...")
    
    # Generate all JSONs
    success = generate_all_jsons()
    if not success:
        print("❌ JSON generation failed")
        return False
    
    # Check if files exist
    required_files = [
        "recent.json",
        "historical.json", 
        "index.json"
    ]
    
    print("\n📁 Checking generated files:")
    for file in required_files:
        file_path = os.path.join(DATA_FOLDER, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file}: {size} bytes")
        else:
            print(f"❌ {file}: Missing")
            return False
    
    # Check archive directory
    if os.path.exists(ARCHIVE_FOLDER):
        archive_files = os.listdir(ARCHIVE_FOLDER)
        print(f"✅ archive/1min/: {len(archive_files)} files")
        for file in archive_files:
            file_path = os.path.join(ARCHIVE_FOLDER, file)
            size = os.path.getsize(file_path)
            print(f"   📄 {file}: {size} bytes")
    else:
        print("❌ archive/1min/: Missing directory")
        return False
    
    # Validate JSON structure
    print("\n🔍 Validating JSON structure:")
    
    # Check recent.json
    try:
        with open(os.path.join(DATA_FOLDER, "recent.json"), 'r') as f:
            recent_data = json.load(f)
        print(f"✅ recent.json: {len(recent_data)} records")
        if recent_data:
            print(f"   📊 Sample record keys: {list(recent_data[0].keys())}")
    except Exception as e:
        print(f"❌ recent.json validation failed: {e}")
        return False
    
    # Check historical.json
    try:
        with open(os.path.join(DATA_FOLDER, "historical.json"), 'r') as f:
            historical_data = json.load(f)
        print(f"✅ historical.json: {len(historical_data)} records")
        if historical_data:
            print(f"   📊 Sample record keys: {list(historical_data[0].keys())}")
    except Exception as e:
        print(f"❌ historical.json validation failed: {e}")
        return False
    
    # Check index.json
    try:
        with open(os.path.join(DATA_FOLDER, "index.json"), 'r') as f:
            index_data = json.load(f)
        print(f"✅ index.json: Valid structure")
        print(f"   📊 Generated at: {index_data.get('generated_at', 'N/A')}")
        print(f"   📊 Recent records: {index_data.get('data_sources', {}).get('recent', {}).get('records', 'N/A')}")
        print(f"   📊 Historical records: {index_data.get('data_sources', {}).get('historical', {}).get('records', 'N/A')}")
    except Exception as e:
        print(f"❌ index.json validation failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Scalable JSON generation system is working correctly.")
    return True

if __name__ == "__main__":
    test_json_generation()