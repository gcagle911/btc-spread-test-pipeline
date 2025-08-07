#!/usr/bin/env python3
"""
Scalable JSON Generation System for BTC Data
============================================

This module generates three types of JSON files:
1. recent.json - Rolling 8-12 hours of 1-minute data
2. archive/1min/YYYY-MM-DD.json - Daily 1-minute candles (1440 per file)
3. historical.json - Long-term 1-hour candles

All files are saved locally first, ready for GCS upload later.
"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta, timezone
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_FOLDER = "render_app/data"
ARCHIVE_FOLDER = os.path.join(DATA_FOLDER, "archive", "1min")
RECENT_HOURS = 10  # 10 hours of recent data (configurable 8-12)

def ensure_directories():
    """Ensure all required directories exist"""
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    logger.info(f"✅ Directories ensured: {DATA_FOLDER}, {ARCHIVE_FOLDER}")

def load_all_csv_data():
    """Load and combine all CSV files into a single chronological dataset"""
    logger.info(f"🔍 Loading CSV files from: {DATA_FOLDER}")
    
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not csv_files:
        logger.warning("❌ No CSV files found")
        return None
    
    logger.info(f"📁 Found {len(csv_files)} CSV files")
    
    all_dfs = []
    for csv_file in sorted(csv_files):
        try:
            df = pd.read_csv(csv_file, parse_dates=["timestamp"])
            if not df.empty:
                all_dfs.append(df)
                logger.info(f"✅ Loaded: {os.path.basename(csv_file)} ({len(df)} rows)")
        except Exception as e:
            logger.error(f"❌ Error loading {csv_file}: {e}")
    
    if not all_dfs:
        logger.error("❌ No valid data found")
        return None
    
    # Combine all data and sort chronologically
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df = combined_df.sort_values("timestamp")
    combined_df = combined_df.drop_duplicates(subset=["timestamp"], keep="last")
    
    logger.info(f"✅ Combined dataset: {len(combined_df)} total rows")
    return combined_df

def resample_to_1min(df):
    """Resample data to 1-minute intervals"""
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
    
    # Calculate moving averages
    df_1min["ma_50"] = df_1min["spread_avg_L20_pct"].rolling(window=50, min_periods=1).mean()
    df_1min["ma_100"] = df_1min["spread_avg_L20_pct"].rolling(window=100, min_periods=1).mean()
    df_1min["ma_200"] = df_1min["spread_avg_L20_pct"].rolling(window=200, min_periods=1).mean()
    
    # Add data quality indicators
    df_1min["ma_50_valid"] = df_1min["spread_avg_L20_pct"].rolling(window=50).count() >= 50
    df_1min["ma_100_valid"] = df_1min["spread_avg_L20_pct"].rolling(window=100).count() >= 100
    df_1min["ma_200_valid"] = df_1min["spread_avg_L20_pct"].rolling(window=200).count() >= 200
    
    df_1min.reset_index(inplace=True)
    df_1min.rename(columns={"timestamp": "time"}, inplace=True)
    
    logger.info(f"📊 Resampled to {len(df_1min)} 1-minute intervals")
    return df_1min

def resample_to_1hour(df):
    """Resample data to 1-hour intervals for historical data"""
    if df is None or df.empty:
        return None
    
    # Set timestamp as index for resampling
    df_indexed = df.set_index("timestamp")
    df_indexed.index = pd.to_datetime(df_indexed.index)
    
    # Resample to 1-hour intervals
    df_1hour = df_indexed.resample("1h").agg({
        "price": "last",
        "spread_avg_L20_pct": "mean"
    }).dropna()
    
    # Calculate moving averages
    df_1hour["ma_50"] = df_1hour["spread_avg_L20_pct"].rolling(window=50, min_periods=1).mean()
    df_1hour["ma_100"] = df_1hour["spread_avg_L20_pct"].rolling(window=100, min_periods=1).mean()
    df_1hour["ma_200"] = df_1hour["spread_avg_L20_pct"].rolling(window=200, min_periods=1).mean()
    
    # Add data quality indicators
    df_1hour["ma_50_valid"] = df_1hour["spread_avg_L20_pct"].rolling(window=50).count() >= 50
    df_1hour["ma_100_valid"] = df_1hour["spread_avg_L20_pct"].rolling(window=100).count() >= 100
    df_1hour["ma_200_valid"] = df_1hour["spread_avg_L20_pct"].rolling(window=200).count() >= 200
    
    df_1hour.reset_index(inplace=True)
    df_1hour.rename(columns={"timestamp": "time"}, inplace=True)
    
    logger.info(f"📊 Resampled to {len(df_1hour)} 1-hour intervals")
    return df_1hour

def generate_recent_json(df_1min):
    """Generate recent.json with last 8-12 hours of 1-minute data"""
    if df_1min is None or df_1min.empty:
        logger.warning("⚠️ No data available for recent.json")
        return 0
    
    # Get last RECENT_HOURS hours
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=RECENT_HOURS)
    
    # Filter for recent data - ensure timezone awareness
    df_1min_copy = df_1min.copy()
    df_1min_copy['time_dt'] = pd.to_datetime(df_1min_copy['time']).dt.tz_localize(None)
    recent_data = df_1min_copy[df_1min_copy['time_dt'] >= cutoff.replace(tzinfo=None)].copy()
    recent_data = recent_data.drop(columns=['time_dt'])
    
    if recent_data.empty:
        logger.warning(f"⚠️ No data in last {RECENT_HOURS} hours, using all available data")
        recent_data = df_1min.copy()
    
    # Save recent.json
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    recent_data.to_json(recent_path, orient="records", date_format="iso")
    
    logger.info(f"⚡ Generated recent.json: {len(recent_data)} records (last {RECENT_HOURS} hours)")
    return len(recent_data)

def generate_daily_archives(df_1min):
    """Generate daily archive files in archive/1min/YYYY-MM-DD.json format"""
    if df_1min is None or df_1min.empty:
        logger.warning("⚠️ No data available for daily archives")
        return []
    
    # Group by date
    df_1min['date'] = pd.to_datetime(df_1min['time']).dt.date
    daily_files = []
    
    for date, day_data in df_1min.groupby('date'):
        # Clean up the data
        day_data_clean = day_data.drop(columns=['date']).copy()
        
        # Create filename
        date_str = date.strftime("%Y-%m-%d")
        filename = f"{date_str}.json"
        file_path = os.path.join(ARCHIVE_FOLDER, filename)
        
        # Save daily archive
        day_data_clean.to_json(file_path, orient="records", date_format="iso")
        daily_files.append(filename)
        
        logger.info(f"📅 Generated daily archive: {filename} ({len(day_data_clean)} records)")
    
    logger.info(f"✅ Generated {len(daily_files)} daily archive files")
    return daily_files

def generate_historical_json(df_1hour):
    """Generate historical.json with 1-hour candles for long-term history"""
    if df_1hour is None or df_1hour.empty:
        logger.warning("⚠️ No data available for historical.json")
        return 0
    
    # Save historical.json
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    df_1hour.to_json(historical_path, orient="records", date_format="iso")
    
    logger.info(f"📚 Generated historical.json: {len(df_1hour)} records (1-hour candles)")
    return len(df_1hour)

def generate_index_json(recent_count, historical_count, daily_files):
    """Generate index.json with metadata about all generated files"""
    index_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": {
            "recent": {
                "file": "recent.json",
                "description": f"Last {RECENT_HOURS} hours of 1-minute data",
                "records": recent_count,
                "update_frequency": "every_minute"
            },
            "historical": {
                "file": "historical.json", 
                "description": "Complete dataset with 1-hour candles",
                "records": historical_count,
                "update_frequency": "hourly"
            },
            "daily_archives": {
                "folder": "archive/1min/",
                "description": "Daily 1-minute candle archives",
                "files": daily_files,
                "format": "YYYY-MM-DD.json"
            }
        },
        "file_structure": {
            "recent.json": f"Last {RECENT_HOURS} hours of 1-minute data",
            "historical.json": "Complete dataset with 1-hour candles", 
            "archive/1min/YYYY-MM-DD.json": "Daily 1-minute candle archives"
        }
    }
    
    # Save index.json
    index_path = os.path.join(DATA_FOLDER, "index.json")
    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    logger.info(f"📋 Generated index.json with {len(daily_files)} daily archives")
    return index_data

def generate_all_jsons():
    """Main function to generate all JSON files"""
    logger.info("🚀 Starting scalable JSON generation...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load all CSV data
    df_raw = load_all_csv_data()
    if df_raw is None:
        logger.error("❌ No data to process")
        return False
    
    # Resample to 1-minute intervals
    df_1min = resample_to_1min(df_raw)
    if df_1min is None:
        logger.error("❌ Failed to resample to 1-minute intervals")
        return False
    
    # Resample to 1-hour intervals for historical data
    df_1hour = resample_to_1hour(df_raw)
    if df_1hour is None:
        logger.error("❌ Failed to resample to 1-hour intervals")
        return False
    
    # Generate all JSON files
    recent_count = generate_recent_json(df_1min)
    daily_files = generate_daily_archives(df_1min)
    historical_count = generate_historical_json(df_1hour)
    index_data = generate_index_json(recent_count, historical_count, daily_files)
    
    logger.info("✅ Scalable JSON generation completed!")
    logger.info(f"📊 Summary:")
    logger.info(f"   • recent.json: {recent_count} records")
    logger.info(f"   • historical.json: {historical_count} records") 
    logger.info(f"   • Daily archives: {len(daily_files)} files")
    
    return True

if __name__ == "__main__":
    generate_all_jsons()