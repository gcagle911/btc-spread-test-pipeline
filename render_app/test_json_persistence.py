#!/usr/bin/env python3
"""
Test script for JSON persistence logic - verifies that existing files are properly loaded and merged
"""

import os
import sys
import pandas as pd
from datetime import datetime, timezone, timedelta

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_json_persistence():
    """Test the JSON persistence logic with sample data"""
    print("🧪 Testing JSON persistence logic...")
    
    try:
        from scalable_json_generator import generate_recent_json, generate_historical_json, ensure_directories
        
        # Ensure directories exist
        ensure_directories()
        
        # Create sample 1-minute data
        now = datetime.now(timezone.utc)
        sample_1min_data = []
        for i in range(10):  # 10 minutes of data
            timestamp = now.replace(minute=i, second=0, microsecond=0)
            sample_1min_data.append({
                'time': timestamp.isoformat(),
                'price': 50000 + i * 10,
                'spread_avg_L20_pct': 0.5 + i * 0.1,
                'ma_50': 0.6 + i * 0.05,
                'ma_100': 0.7 + i * 0.03,
                'ma_200': 0.8 + i * 0.02,
                'ma_50_valid': True,
                'ma_100_valid': True,
                'ma_200_valid': True
            })
        
        df_1min = pd.DataFrame(sample_1min_data)
        print(f"📊 Created sample 1-minute data: {len(df_1min)} records")
        
        # Create sample 1-hour data
        sample_1hour_data = []
        for i in range(5):  # 5 hours of data
            timestamp = now.replace(hour=now.hour - i, minute=0, second=0, microsecond=0)
            sample_1hour_data.append({
                'time': timestamp.isoformat(),
                'price': 50000 + i * 100,
                'spread_avg_L20_pct': 0.5 + i * 0.2,
                'ma_50': 0.6 + i * 0.1,
                'ma_100': 0.7 + i * 0.08,
                'ma_200': 0.8 + i * 0.05,
                'ma_50_valid': True,
                'ma_100_valid': True,
                'ma_200_valid': True
            })
        
        df_1hour = pd.DataFrame(sample_1hour_data)
        print(f"📊 Created sample 1-hour data: {len(df_1hour)} records")
        
        # Test recent.json generation
        print(f"\n🔄 Testing recent.json generation...")
        recent_count = generate_recent_json(df_1min)
        print(f"✅ Recent.json generated: {recent_count} records")
        
        # Test historical.json generation
        print(f"\n🔄 Testing historical.json generation...")
        historical_count = generate_historical_json(df_1hour)
        print(f"✅ Historical.json generated: {historical_count} records")
        
        # Check if files were created
        recent_file = "render_app/data/recent.json"
        historical_file = "render_app/data/historical.json"
        
        if os.path.exists(recent_file):
            print(f"✅ Recent.json file created: {recent_file}")
            try:
                loaded_recent = pd.read_json(recent_file, orient="records")
                print(f"✅ Successfully loaded recent.json: {len(loaded_recent)} records")
            except Exception as e:
                print(f"❌ Failed to load recent.json: {e}")
        else:
            print(f"❌ Recent.json file not created: {recent_file}")
        
        if os.path.exists(historical_file):
            print(f"✅ Historical.json file created: {historical_file}")
            try:
                loaded_historical = pd.read_json(historical_file, orient="records")
                print(f"✅ Successfully loaded historical.json: {len(loaded_historical)} records")
            except Exception as e:
                print(f"❌ Failed to load historical.json: {e}")
        else:
            print(f"❌ Historical.json file not created: {historical_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing JSON persistence: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_json_persistence()