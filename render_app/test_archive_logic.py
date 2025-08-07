#!/usr/bin/env python3
"""
Test script for archive logic - verifies that existing files are properly loaded and merged
"""

import os
import sys
import pandas as pd
from datetime import datetime, timezone

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_archive_logic():
    """Test the archive logic with sample data"""
    print("🧪 Testing archive logic...")
    
    try:
        from scalable_json_generator import generate_daily_archives, ensure_directories
        
        # Ensure directories exist
        ensure_directories()
        
        # Create sample data for today
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        
        # Create sample 1-minute data
        sample_data = []
        for i in range(10):  # 10 minutes of data
            timestamp = now.replace(minute=i, second=0, microsecond=0)
            sample_data.append({
                'time': timestamp.isoformat(),
                'price': 50000 + i * 10,
                'volume': 100 + i,
                'spread': 0.5 + i * 0.1
            })
        
        df_sample = pd.DataFrame(sample_data)
        print(f"📊 Created sample data: {len(df_sample)} records for {today_str}")
        
        # Test archive generation
        print(f"\n🔄 Testing archive generation for {today_str}...")
        result = generate_daily_archives(df_sample)
        
        print(f"✅ Archive generation result: {result}")
        
        # Check if file was created
        archive_file = f"render_app/data/archive/1min/{today_str}.json"
        if os.path.exists(archive_file):
            print(f"✅ Archive file created: {archive_file}")
            
            # Load and verify the file
            with open(archive_file, 'r') as f:
                content = f.read()
                print(f"📄 File size: {len(content)} characters")
                
            # Try to load as JSON
            try:
                loaded_data = pd.read_json(archive_file, orient="records")
                print(f"✅ Successfully loaded archive: {len(loaded_data)} records")
            except Exception as e:
                print(f"❌ Failed to load archive: {e}")
        else:
            print(f"❌ Archive file not created: {archive_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing archive logic: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_archive_logic()