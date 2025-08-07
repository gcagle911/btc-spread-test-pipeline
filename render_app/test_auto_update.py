#!/usr/bin/env python3
"""
Quick test to verify 60-second auto-regeneration
"""

import time
import os
from datetime import datetime
from scalable_json_generator import generate_all_jsons, DATA_FOLDER

def test_60_second_updates():
    """Test that JSON files update every 60 seconds"""
    print("🔄 Testing 60-second auto-regeneration...")
    
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    
    # Get initial modification time
    initial_mtime = os.path.getmtime(recent_path)
    print(f"⏰ Initial mtime: {datetime.fromtimestamp(initial_mtime)}")
    
    # Wait a moment and trigger update
    print("⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    # Trigger regeneration
    print("🔄 Triggering JSON regeneration...")
    generate_all_jsons()
    
    # Check if updated
    new_mtime = os.path.getmtime(recent_path)
    print(f"⏰ New mtime: {datetime.fromtimestamp(new_mtime)}")
    
    if new_mtime > initial_mtime:
        print("✅ Auto-regeneration working correctly!")
        return True
    else:
        print("❌ Auto-regeneration failed")
        return False

if __name__ == "__main__":
    test_60_second_updates()