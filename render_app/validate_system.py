#!/usr/bin/env python3
"""
Comprehensive System Validation Script
=====================================

This script validates all aspects of the scalable JSON generation system:
1. recent.json validation
2. archive/1min/YYYY-MM-DD.json validation  
3. historical.json validation
4. Directory structure validation
5. Test simulation
"""

import json
import os
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from scalable_json_generator import generate_all_jsons, DATA_FOLDER, ARCHIVE_FOLDER
import glob

def validate_recent_json():
    """Validate recent.json file"""
    print("🔍 Validating recent.json...")
    
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    if not os.path.exists(recent_path):
        print("❌ recent.json does not exist")
        return False
    
    # Check file size
    file_size = os.path.getsize(recent_path)
    print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    if file_size > 1024 * 1024:  # 1MB
        print("❌ File size exceeds 1MB limit")
        return False
    
    # Load and validate JSON
    try:
        with open(recent_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("❌ Data is not a list")
            return False
        
        print(f"📊 Records: {len(data)}")
        
        # Check for nulls/NaNs
        for i, record in enumerate(data):
            for key, value in record.items():
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    print(f"❌ Found null/NaN at record {i}, key '{key}': {value}")
                    return False
        
        # Check time range (should be ~10 hours)
        if data:
            first_time = pd.to_datetime(data[0]['time'])
            last_time = pd.to_datetime(data[-1]['time'])
            time_diff = (last_time - first_time).total_seconds() / 3600
            
            print(f"⏰ Time range: {time_diff:.1f} hours")
            
            if time_diff > 12:  # Should be ~10 hours, allow some flexibility
                print(f"❌ Time range too large: {time_diff:.1f} hours")
                return False
        
        # Check structure
        expected_keys = ['time', 'price', 'spread_avg_L20_pct', 'ma_50', 'ma_100', 'ma_200', 
                        'ma_50_valid', 'ma_100_valid', 'ma_200_valid']
        
        if data and set(data[0].keys()) != set(expected_keys):
            print(f"❌ Unexpected keys: {set(data[0].keys())}")
            return False
        
        print("✅ recent.json validation passed")
        return True
        
    except Exception as e:
        print(f"❌ JSON validation error: {e}")
        return False

def validate_archive_files():
    """Validate archive/1min/YYYY-MM-DD.json files"""
    print("\n🔍 Validating archive files...")
    
    if not os.path.exists(ARCHIVE_FOLDER):
        print("❌ Archive directory does not exist")
        return False
    
    archive_files = glob.glob(os.path.join(ARCHIVE_FOLDER, "*.json"))
    print(f"📁 Found {len(archive_files)} archive files")
    
    for file_path in archive_files:
        filename = os.path.basename(file_path)
        print(f"\n📄 Validating {filename}...")
        
        # Check filename format
        if not filename.endswith('.json'):
            print(f"❌ Invalid filename format: {filename}")
            return False
        
        date_str = filename.replace('.json', '')
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"❌ Invalid date format in filename: {date_str}")
            return False
        
        # Load and validate JSON
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print(f"❌ Data is not a list in {filename}")
                return False
            
            print(f"📊 Records: {len(data)}")
            
            # Check for 1440 records (24 hours * 60 minutes)
            if len(data) > 1440:
                print(f"❌ Too many records: {len(data)} (should be ≤1440)")
                return False
            
            # Check for nulls/NaNs
            for i, record in enumerate(data):
                for key, value in record.items():
                    if value is None or (isinstance(value, float) and pd.isna(value)):
                        print(f"❌ Found null/NaN at record {i}, key '{key}': {value}")
                        return False
            
            # Check all records are from the same date
            if data:
                first_date = pd.to_datetime(data[0]['time']).date()
                last_date = pd.to_datetime(data[-1]['time']).date()
                
                if first_date != last_date:
                    print(f"❌ Mixed dates: {first_date} to {last_date}")
                    return False
                
                expected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if first_date != expected_date:
                    print(f"❌ Date mismatch: filename {expected_date}, data {first_date}")
                    return False
            
            print(f"✅ {filename} validation passed")
            
        except Exception as e:
            print(f"❌ JSON validation error in {filename}: {e}")
            return False
    
    return True

def validate_historical_json():
    """Validate historical.json file"""
    print("\n🔍 Validating historical.json...")
    
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    if not os.path.exists(historical_path):
        print("❌ historical.json does not exist")
        return False
    
    # Check file size
    file_size = os.path.getsize(historical_path)
    print(f"📏 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    
    if file_size > 1024 * 1024:  # 1MB
        print("❌ File size exceeds 1MB limit")
        return False
    
    # Load and validate JSON
    try:
        with open(historical_path, 'r') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print("❌ Data is not a list")
            return False
        
        print(f"📊 Records: {len(data)}")
        
        # Check for nulls/NaNs
        for i, record in enumerate(data):
            for key, value in record.items():
                if value is None or (isinstance(value, float) and pd.isna(value)):
                    print(f"❌ Found null/NaN at record {i}, key '{key}': {value}")
                    return False
        
        # Check timestamps align to hours
        if data:
            for i, record in enumerate(data):
                timestamp = pd.to_datetime(record['time'])
                if timestamp.minute != 0 or timestamp.second != 0:
                    print(f"❌ Timestamp not aligned to hour: {timestamp}")
                    return False
        
        # Check structure
        expected_keys = ['time', 'price', 'spread_avg_L20_pct', 'ma_50', 'ma_100', 'ma_200', 
                        'ma_50_valid', 'ma_100_valid', 'ma_200_valid']
        
        if data and set(data[0].keys()) != set(expected_keys):
            print(f"❌ Unexpected keys: {set(data[0].keys())}")
            return False
        
        print("✅ historical.json validation passed")
        return True
        
    except Exception as e:
        print(f"❌ JSON validation error: {e}")
        return False

def validate_directory_structure():
    """Validate directory and file structure"""
    print("\n🔍 Validating directory structure...")
    
    # Check main data directory
    if not os.path.exists(DATA_FOLDER):
        print(f"❌ Main data directory does not exist: {DATA_FOLDER}")
        return False
    
    # Check archive directory
    if not os.path.exists(ARCHIVE_FOLDER):
        print(f"❌ Archive directory does not exist: {ARCHIVE_FOLDER}")
        return False
    
    # Check required files exist
    required_files = [
        os.path.join(DATA_FOLDER, "recent.json"),
        os.path.join(DATA_FOLDER, "historical.json"),
        os.path.join(DATA_FOLDER, "index.json")
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            print(f"❌ Required file missing: {file_path}")
            return False
    
    # Check CSV files exist
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not csv_files:
        print("❌ No CSV files found")
        return False
    
    print(f"✅ Directory structure validation passed")
    print(f"📁 CSV files: {len(csv_files)}")
    print(f"📁 Archive files: {len(glob.glob(os.path.join(ARCHIVE_FOLDER, '*.json')))}")
    
    return True

def test_auto_regeneration():
    """Test that JSON files regenerate automatically"""
    print("\n🔍 Testing auto-regeneration...")
    
    # Get initial file modification times
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    
    if not os.path.exists(recent_path) or not os.path.exists(historical_path):
        print("❌ Required files don't exist for regeneration test")
        return False
    
    initial_recent_mtime = os.path.getmtime(recent_path)
    initial_historical_mtime = os.path.getmtime(historical_path)
    
    print(f"⏰ Initial recent.json mtime: {datetime.fromtimestamp(initial_recent_mtime)}")
    print(f"⏰ Initial historical.json mtime: {datetime.fromtimestamp(initial_historical_mtime)}")
    
    # Trigger regeneration
    print("🔄 Triggering JSON regeneration...")
    success = generate_all_jsons()
    
    if not success:
        print("❌ JSON generation failed")
        return False
    
    # Check if files were updated
    new_recent_mtime = os.path.getmtime(recent_path)
    new_historical_mtime = os.path.getmtime(historical_path)
    
    print(f"⏰ New recent.json mtime: {datetime.fromtimestamp(new_recent_mtime)}")
    print(f"⏰ New historical.json mtime: {datetime.fromtimestamp(new_historical_mtime)}")
    
    if new_recent_mtime > initial_recent_mtime:
        print("✅ recent.json was regenerated")
    else:
        print("❌ recent.json was not regenerated")
        return False
    
    if new_historical_mtime > initial_historical_mtime:
        print("✅ historical.json was regenerated")
    else:
        print("❌ historical.json was not regenerated")
        return False
    
    return True

def show_sample_data():
    """Show sample data from each file"""
    print("\n📊 Sample Data from Files:")
    
    # Sample from recent.json
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    if os.path.exists(recent_path):
        with open(recent_path, 'r') as f:
            data = json.load(f)
        print(f"\n📄 recent.json (first 2 records):")
        for i, record in enumerate(data[:2]):
            print(f"  Record {i}: {record}")
    
    # Sample from historical.json
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    if os.path.exists(historical_path):
        with open(historical_path, 'r') as f:
            data = json.load(f)
        print(f"\n📄 historical.json (first 2 records):")
        for i, record in enumerate(data[:2]):
            print(f"  Record {i}: {record}")
    
    # Sample from archive files
    archive_files = glob.glob(os.path.join(ARCHIVE_FOLDER, "*.json"))
    if archive_files:
        sample_file = archive_files[0]
        with open(sample_file, 'r') as f:
            data = json.load(f)
        print(f"\n📄 {os.path.basename(sample_file)} (first 2 records):")
        for i, record in enumerate(data[:2]):
            print(f"  Record {i}: {record}")

def run_all_validations():
    """Run all validation tests"""
    print("🧪 Running Comprehensive System Validation")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", validate_directory_structure),
        ("Recent JSON", validate_recent_json),
        ("Archive Files", validate_archive_files),
        ("Historical JSON", validate_historical_json),
        ("Auto-Regeneration", test_auto_regeneration)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Show sample data
    show_sample_data()
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print(f"\n🎉 ALL TESTS PASSED! System is ready for GCS integration.")
    else:
        print(f"\n⚠️ Some tests failed. Please review the issues above.")
    
    return all_passed

if __name__ == "__main__":
    run_all_validations()