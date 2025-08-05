# BTC Data Processing - Enhanced with Historical Data Management
# Updated: 2025-07-10 - Fixed timestamp checking and added comprehensive debugging
# This version includes hybrid data loading (recent.json + historical.json)

import pandas as pd
import os
import json
from datetime import datetime, timedelta, timezone
import glob

DATA_FOLDER = "render_app/data"

def load_all_historical_data():
    """Load and combine all available CSV files into a chronological dataset"""
    print(f"🔍 Looking for CSV files in: {DATA_FOLDER}")
    
    # Load ALL available CSV files for historical processing
    all_csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    
    if not all_csv_files:
        print("❌ No CSV files found at all")
        print(f"🔍 Directory exists: {os.path.exists(DATA_FOLDER)}")
        if os.path.exists(DATA_FOLDER):
            all_files = os.listdir(DATA_FOLDER)
            print(f"🔍 All files in directory: {all_files}")
        return None
    
    # Sort files by modification time to get the most recent first
    csv_files = sorted(all_csv_files, key=os.path.getmtime, reverse=True)
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    for csv_file in csv_files:
        file_size = os.path.getsize(csv_file) if os.path.exists(csv_file) else 0
        mod_time = datetime.fromtimestamp(os.path.getmtime(csv_file))
        print(f"   📄 {os.path.basename(csv_file)} ({file_size} bytes, modified: {mod_time})")
    
    all_dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, parse_dates=["timestamp"])
            if not df.empty:
                all_dfs.append(df)
                # Show date range for each file
                min_time = df['timestamp'].min()
                max_time = df['timestamp'].max()
                print(f"✅ Loaded: {os.path.basename(csv_file)} ({len(df)} rows, {min_time} to {max_time})")
            else:
                print(f"⚠️ Empty file: {os.path.basename(csv_file)}")
        except Exception as e:
            print(f"❌ Error loading {csv_file}: {e}")
    
    if not all_dfs:
        print("❌ No valid data found")
        return None
    
    # Combine all data and sort chronologically
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df = combined_df.sort_values("timestamp")
    combined_df = combined_df.drop_duplicates(subset=["timestamp"], keep="last")
    
    # Show overall date range
    min_time = combined_df['timestamp'].min()
    max_time = combined_df['timestamp'].max()
    print(f"✅ Combined dataset: {len(combined_df)} total rows ({min_time} to {max_time})")
    return combined_df

def resample_and_calculate_mas(df):
    """Resample to 1-minute intervals and calculate MAs with full historical context"""
    if df is None or df.empty:
        return None
    
    # Set timestamp as index for resampling
    df_indexed = df.set_index("timestamp")
    df_indexed.index = pd.to_datetime(df_indexed.index)
    
    # Resample to 1-minute intervals
    df_1min = df_indexed.resample("1min").agg({
        "price": "last",
        "spread_avg_L20_pct": "mean"
    }).dropna()
    
    print(f"📊 Resampled to {len(df_1min)} 1-minute intervals")
    
    # Calculate moving averages with full historical context
    df_1min["ma_50"] = df_1min["spread_avg_L20_pct"].rolling(window=50, min_periods=1).mean()
    df_1min["ma_100"] = df_1min["spread_avg_L20_pct"].rolling(window=100, min_periods=1).mean()
    df_1min["ma_200"] = df_1min["spread_avg_L20_pct"].rolling(window=200, min_periods=1).mean()
    
    # Add data quality indicators
    df_1min["ma_50_valid"] = df_1min["spread_avg_L20_pct"].rolling(window=50).count() >= 50
    df_1min["ma_100_valid"] = df_1min["spread_avg_L20_pct"].rolling(window=100).count() >= 100
    df_1min["ma_200_valid"] = df_1min["spread_avg_L20_pct"].rolling(window=200).count() >= 200
    
    df_1min.reset_index(inplace=True)
    df_1min.rename(columns={"timestamp": "time"}, inplace=True)
    
    return df_1min

def save_recent_data(df_full):
    """Save recent data for fast chart loading"""
    if df_full is None or df_full.empty:
        return
    
    # For test data, include all available data as "recent"
    # In production, this would filter for last 24 hours
    df_full['time_dt'] = pd.to_datetime(df_full['time'])
    
    # Get the most recent data (last 24 hours or all available if less)
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)
    
    recent_data = df_full[df_full['time_dt'] >= cutoff].copy()
    
    # If no recent data (like in test scenarios), use all available data
    if recent_data.empty:
        print("⚠️ No data in last 24h, using all available data for recent.json")
        recent_data = df_full.copy()
    
    recent_data = recent_data.drop(columns=['time_dt'])
    
    # Convert all timestamps to strings for JSON serialization
    records = recent_data.to_dict('records')
    for record in records:
        for key, value in record.items():
            if hasattr(value, 'isoformat'):
                record[key] = value.isoformat()
    
    # Save recent data (fast loading for charts)
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    with open(recent_path, 'w') as f:
        json.dump(records, f, separators=(',', ':'))
    
    print(f"⚡ Saved recent.json: {len(records)} records")
    return len(records)

def should_update_historical():
    """Check if historical.json needs updating (every hour)"""
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    
    if not os.path.exists(historical_path):
        print("🔄 Historical file doesn't exist, creating...")
        return True  # Create if doesn't exist
    
    # Check if file is older than 1 hour
    try:
        file_time = datetime.fromtimestamp(os.path.getmtime(historical_path))
        now = datetime.utcnow()
        age_hours = (now - file_time).total_seconds() / 3600
        
        print(f"📅 Historical file age: {age_hours:.1f} hours (threshold: 1.0)")
        
        should_update = age_hours >= 1.0  # Changed from > to >= to fix deadlock
        if should_update:
            print("⏰ File is old enough, will update historical data")
        else:
            print(f"⏸️ File is recent ({age_hours:.1f}h old), skipping update")
            
        return should_update
        
    except Exception as e:
        print(f"⚠️ Error checking file timestamp: {e}, forcing update")
        return True  # Force update if timestamp check fails

def should_rotate_historical():
    """Check if we should archive older data (weekly rotation)"""
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    
    if not os.path.exists(historical_path):
        return False  # Can't rotate if file doesn't exist
    
    try:
        file_time = datetime.fromtimestamp(os.path.getmtime(historical_path))
        now = datetime.utcnow()
        
        # Rotate weekly to manage file size while preserving data
        # This keeps historical.json at a reasonable size (~10MB for 30 days)
        days_old = (now - file_time).days
        
        should_rotate = days_old >= 7  # Weekly rotation
        
        if should_rotate:
            print(f"📅 Historical file is {days_old} days old - archiving old data (weekly rotation)!")
        
        return should_rotate
        
    except Exception as e:
        print(f"⚠️ Error checking rotation date: {e}")
        return False

def rotate_historical_file():
    """Rotate historical.json to a daily archive and start fresh"""
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    
    if not os.path.exists(historical_path):
        print("ℹ️ No historical.json to rotate")
        return
    
    try:
        # Get the file's date
        file_time = datetime.fromtimestamp(os.path.getmtime(historical_path))
        archive_date = file_time.strftime("%Y-%m-%d")
        
        # Create archive filename
        archive_path = os.path.join(DATA_FOLDER, f"historical_{archive_date}.json")
        
        # Move current historical to archive (if archive doesn't already exist)
        if not os.path.exists(archive_path):
            os.rename(historical_path, archive_path)
            print(f"📦 Archived historical.json → historical_{archive_date}.json")
        else:
            # Archive already exists, just remove current
            os.remove(historical_path)
            print(f"🗑️ Removed old historical.json (archive historical_{archive_date}.json already exists)")
            
    except Exception as e:
        print(f"⚠️ Error rotating historical file: {e}")

def save_historical_data(df_full):
    """Save optimized historical dataset (chart-friendly with smart rotation)"""
    if df_full is None or df_full.empty:
        return
    
    # Archive old data first if needed (weekly rotation)
    if should_rotate_historical():
        rotate_historical_file()
    
    now = datetime.utcnow()
    
    # Strategy: Keep last 30 days in historical.json for good chart context
    # This balances file size (~10MB) with useful historical perspective
    cutoff_time = now - timedelta(days=30)
    
    # Convert time column to datetime if it's a string
    if df_full['time'].dtype == 'object':
        df_full['time'] = pd.to_datetime(df_full['time'])
    
    # Filter to last 30 days for historical.json
    df_chart_optimized = df_full[df_full['time'] >= cutoff_time].copy()
    
    if df_chart_optimized.empty:
        print(f"ℹ️ No data in last 30 days, using all available data")
        df_chart_optimized = df_full.copy()
    
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    
    try:
        # Save as JSON with proper formatting
        records = df_chart_optimized.to_dict('records')
        
        # Convert all timestamps to strings for JSON serialization
        for record in records:
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        
        # Add metadata for charts
        metadata = {
            "generated_at": now.isoformat(),
            "data_range_days": 30,
            "total_records": len(records),
            "data_type": "1-minute OHLC with moving averages",
            "update_frequency": "hourly, optimized for charts",
            "first_timestamp": records[0]['time'] if records else None,
            "last_timestamp": records[-1]['time'] if records else None,
            "description": "30-day historical data optimized for chart performance"
        }
        
        # Save the data
        with open(historical_path, 'w') as f:
            json.dump(records, f, separators=(',', ':'))  # Compact format
        
        print(f"✅ Historical data saved: {len(records)} records (30-day window)")
        print(f"📊 Data range: {metadata['first_timestamp']} to {metadata['last_timestamp']}")
        
        # Also save metadata separately
        metadata_path = os.path.join(DATA_FOLDER, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return len(records)
        
    except Exception as e:
        print(f"❌ Error saving historical data: {e}")
        return 0

def save_compressed_longterm_data(df_full):
    """Create a compressed long-term dataset for extended chart views"""
    if df_full is None or df_full.empty:
        return 0
    
    # Convert time column to datetime if it's a string
    if df_full['time'].dtype == 'object':
        df_full['time'] = pd.to_datetime(df_full['time'])
    
    # Create a copy and set time as index for resampling
    df_longterm = df_full.copy()
    df_longterm.set_index('time', inplace=True)
    
    # Resample to hourly data (60x compression from 1-minute data)
    # This dramatically reduces file size while preserving trends
    df_hourly = df_longterm.resample('1h').agg({
        'price': 'last',  # Last price in the hour
        'spread_avg_L20_pct': 'mean',  # Average spread
        'ma_50': 'last',
        'ma_100': 'last', 
        'ma_200': 'last',
        'ma_50_valid': 'last',
        'ma_100_valid': 'last',
        'ma_200_valid': 'last'
    }).dropna()
    
    # Reset index to get time back as a column
    df_hourly.reset_index(inplace=True)
    df_hourly.rename(columns={'time': 'time'}, inplace=True)
    
    # Add time_dt for compatibility
    df_hourly['time_dt'] = df_hourly['time']
    
    longterm_path = os.path.join(DATA_FOLDER, "longterm.json")
    
    try:
        # Save as JSON with proper formatting
        records = df_hourly.to_dict('records')
        
        # Convert all timestamps to strings for JSON serialization
        for record in records:
            for key, value in record.items():
                if hasattr(value, 'isoformat'):
                    record[key] = value.isoformat()
        
        # Add metadata
        now = datetime.utcnow()
        metadata = {
            "generated_at": now.isoformat(),
            "data_resolution": "1 hour",
            "compression_ratio": "60:1 from 1-minute data",
            "total_records": len(records),
            "data_type": "Hourly OHLC with moving averages",
            "update_frequency": "hourly, optimized for long-term charts",
            "first_timestamp": records[0]['time'] if records else None,
            "last_timestamp": records[-1]['time'] if records else None,
            "description": "Compressed historical data for long-term chart performance"
        }
        
        # Save the compressed data
        with open(longterm_path, 'w') as f:
            json.dump(records, f, separators=(',', ':'))  # Compact format
        
        compression_ratio = len(df_full) / len(records) if records else 0
        print(f"📈 Long-term data saved: {len(records)} hourly records ({compression_ratio:.1f}x compression)")
        print(f"🗂️ Date range: {metadata['first_timestamp']} to {metadata['last_timestamp']}")
        
        return len(records)
        
    except Exception as e:
        print(f"❌ Error saving long-term data: {e}")
        return 0

def save_daily_jsons(df_full):
    """Create individual daily JSON files for compatibility"""
    if df_full is None or df_full.empty:
        return []
    
    df_full["date"] = pd.to_datetime(df_full["time"]).dt.date
    daily_files = []
    
    for date, day_data in df_full.groupby("date"):
        day_data_clean = day_data.drop(columns=["date"])
        
        output_file = f"output_{date}.json"
        output_path = os.path.join(DATA_FOLDER, output_file)
        
        # Always update daily files if we have data for that date
        day_data_clean.to_json(output_path, orient="records", date_format="iso")
        daily_files.append(output_file)
        print(f"📅 Updated daily file: {output_file} ({len(day_data_clean)} records)")
    
    return daily_files

def save_index_json(daily_files, recent_count, historical_count, longterm_count=0):
    """Create index file with information about all data sources"""
    index_data = {
        "data_sources": {
            "recent": {
                "file": "recent.json",
                "description": "Last 24 hours (fast loading)",
                "records": recent_count,
                "update_frequency": "every_second"
            },
            "historical": {
                "file": "historical.json", 
                "description": "30-day dataset (chart optimized)",
                "records": historical_count,
                "update_frequency": "hourly"
            },
            "longterm": {
                "file": "longterm.json",
                "description": "Compressed hourly data (long-term trends)",
                "records": longterm_count,
                "update_frequency": "hourly",
                "compression": "60:1 from minute data"
            }
        },
        "daily_files": sorted(daily_files),
        "recommended_usage": {
            "fast_chart_startup": "Load /recent.json first",
            "medium_term_view": "Load /historical.json for 30-day data",
            "long_term_trends": "Load /longterm.json for compact historical view",
            "hybrid_approach": "Load recent first, then historical/longterm as needed"
        },
        "last_updated": datetime.utcnow().isoformat()
    }
    
    index_path = os.path.join(DATA_FOLDER, "index.json")
    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"📋 Saved index.json")

def process_csv_to_json():
    """
    Main function: Hybrid data processing system
    - recent.json: Updated every second (last 24h)
    - historical.json: Updated hourly (complete dataset)
    """
    print("🚀 Starting hybrid data processing...")
    
    # Step 1: Load all historical data
    df_combined = load_all_historical_data()
    if df_combined is None:
        return
    
    # Step 2: Resample and calculate MAs with full context
    df_processed = resample_and_calculate_mas(df_combined)
    if df_processed is None:
        return
    
    # Step 3: Always save recent data (fast for charts)
    recent_count = save_recent_data(df_processed)
    
    # Step 4: Always update historical data if we have new CSV data
    historical_count = len(df_processed)
    
    # Check if we have newer CSV data than the last historical update
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    should_force_update = False
    
    if os.path.exists(historical_path):
        # Get the newest CSV file timestamp
        csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
        if csv_files:
            newest_csv_time = max(os.path.getmtime(f) for f in csv_files)
            historical_time = os.path.getmtime(historical_path)
            
            if newest_csv_time > historical_time:
                print("🔄 Found newer CSV data, forcing historical update")
                should_force_update = True
    
    if should_update_historical() or should_force_update:
        print("⏰ Updating historical data")
        historical_count = save_historical_data(df_processed)
        
        # Also create compressed long-term data
        longterm_count = save_compressed_longterm_data(df_processed)
        
        # Also update daily files when historical updates
        daily_files = save_daily_jsons(df_processed)
    else:
        print("⏸️ Skipping historical update (updated within last hour)")
        daily_files = []
        longterm_count = 0
    
    # Step 5: Update index
    save_index_json(daily_files, recent_count, historical_count, longterm_count)
    
    print("✅ Hybrid processing complete!")
    print(f"⚡ Recent data: {recent_count} records (updated every second)")
    print(f"📚 Historical data: {historical_count} records (30-day window, updated hourly)")
    print(f"📈 Long-term data: {longterm_count} records (compressed hourly, all available data)")
    print("🔄 Charts can use:")
    print("   - /recent.json for fast startup (24 hours)")
    print("   - /historical.json for medium-term data (30 days)")
    print("   - /longterm.json for long-term trends (hourly data, compact)")
    print("   - /historical-combined for maximum range (all archived data)")

# Legacy function for compatibility
def process_today_only():
    """Legacy function that only processes today's data (for compatibility)"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    files = sorted(
        f for f in os.listdir(DATA_FOLDER)
        if f.startswith(today) and f.endswith(".csv")
    )
    
    if not files:
        print(f"❌ No CSVs found for {today}")
        return
    
    latest_file = files[-1]
    csv_path = os.path.join(DATA_FOLDER, latest_file)
    print(f"📄 Processing today only: {csv_path}")
    
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    if df.empty:
        return
    
    df.set_index("timestamp", inplace=True)
    df_1min = df.resample("1min").agg({
        "price": "last",
        "spread_avg_L20_pct": "mean"
    }).dropna()
    
    df_1min["ma_50"] = df_1min["spread_avg_L20_pct"].rolling(window=50).mean()
    df_1min["ma_100"] = df_1min["spread_avg_L20_pct"].rolling(window=100).mean()
    df_1min["ma_200"] = df_1min["spread_avg_L20_pct"].rolling(window=200).mean()
    
    df_1min.reset_index(inplace=True)
    df_1min.rename(columns={"timestamp": "time"}, inplace=True)
    
    output_path = os.path.join(DATA_FOLDER, f"output_{today}.json")
    df_1min.to_json(output_path, orient="records", date_format="iso")
    print(f"✅ Saved today's data: {output_path}")

if __name__ == "__main__":
    process_csv_to_json()
