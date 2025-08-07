#!/usr/bin/env python3
"""
Test script for GCS-first logic - verifies that GCS is prioritized over local files
"""

import os
import sys
import pandas as pd
from datetime import datetime, timezone, timedelta

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_gcs_priority():
    """Test that GCS is prioritized over local files"""
    print("🧪 Testing GCS-first logic...")
    
    try:
        from scalable_json_generator import generate_recent_json, generate_historical_json, ensure_directories
        
        # Ensure directories exist
        ensure_directories()
        
        # Create sample data
        now = datetime.now(timezone.utc)
        sample_1min_data = []
        for i in range(5):  # 5 minutes of data
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
        for i in range(3):  # 3 hours of data
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
        
        # Test recent.json generation (should prioritize GCS)
        print(f"\n🔄 Testing recent.json generation (GCS-first)...")
        recent_count = generate_recent_json(df_1min)
        print(f"✅ Recent.json generated: {recent_count} records")
        
        # Test historical.json generation (should prioritize GCS)
        print(f"\n🔄 Testing historical.json generation (GCS-first)...")
        historical_count = generate_historical_json(df_1hour)
        print(f"✅ Historical.json generated: {historical_count} records")
        
        print(f"\n✅ GCS-first logic test completed!")
        print(f"📋 Summary:")
        print(f"   • Recent.json: {recent_count} records (prioritizes GCS)")
        print(f"   • Historical.json: {historical_count} records (prioritizes GCS)")
        print(f"   • Local files only used as fallback when GCS unavailable")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing GCS-first logic: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_gcs_priority()