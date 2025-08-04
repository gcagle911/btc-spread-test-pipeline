#!/usr/bin/env python3
"""
Remove old data files that are interfering with current data processing
"""

import requests

def clean_old_data():
    """Remove old July CSV files that are contaminating the data processing"""
    base_url = "https://btc-spread-test-pipeline.onrender.com"
    
    print("🧹 Cleaning old data files...")
    
    # The issue is that old July CSV files (2025-07-06.csv, 2025-07-14_16.csv) 
    # are being processed along with current August data, causing the JSON 
    # to show old timestamps instead of current data.
    
    # We need to remove these via the backup system or data processing
    # Since we can't directly delete files, let's trigger a current data rebuild
    
    # First, let's see what recent.json looks like
    try:
        response = requests.get(f"{base_url}/recent.json")
        recent_data = response.json()
        print(f"📊 Recent.json has {len(recent_data)} records")
        if recent_data:
            first_time = recent_data[0]['time']
            last_time = recent_data[-1]['time']
            print(f"📅 Time range: {first_time} to {last_time}")
            
    except Exception as e:
        print(f"❌ Error reading recent.json: {e}")
    
    print("💡 The old CSV files need to be removed from the server to fix the data processing")
    print("💡 The system is processing ALL CSV files together, including old July data")

if __name__ == "__main__":
    clean_old_data()