#!/usr/bin/env python3
"""
Scalable JSON Generation System for BTC Data
============================================

This module generates three types of JSON files from NEW incoming data:
1. recent.json - Rolling 8-12 hours of 1-minute data
2. archive/1min/YYYY-MM-DD.json - Daily 1-minute candles (1440 per file)
3. historical.json - Long-term 1-hour candles

All files are saved locally first, then uploaded to Google Cloud Storage.
"""

import pandas as pd
import os
import json
from datetime import datetime, timedelta, timezone
import glob
import logging
import numpy as np

# Import GCS uploader
try:
    from gcs_uploader import upload_to_gcs
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logging.warning("⚠️ GCS uploader not available - files will only be saved locally")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DATA_FOLDER = "render_app/data"
ARCHIVE_FOLDER = os.path.join(DATA_FOLDER, "archive", "1min")
RECENT_HOURS = 48  # 48 hours (2 days) of recent data

def write_json_records(dataframe, destination_path):
    """Write a pandas DataFrame to a JSON file as an array of records with strict JSON compliance.

    Replaces any NaN/Infinity values with null to avoid invalid JSON tokens that some viewers cannot render.
    """
    try:
        # Replace NaN/Inf with None to ensure valid JSON (no NaN, Infinity, -Infinity tokens)
        sanitized_df = dataframe.replace({np.nan: None, np.inf: None, -np.inf: None})
        records = sanitized_df.to_dict(orient="records")
        with open(destination_path, "w", encoding="utf-8") as output_file:
            json.dump(records, output_file, ensure_ascii=False, allow_nan=False)
    except Exception as exc:
        logger.error(f"❌ Failed to write JSON to {destination_path}: {exc}")
        raise

def ensure_directories():
    """Ensure all required directories exist"""
    os.makedirs(DATA_FOLDER, exist_ok=True)
    os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
    logger.info(f"✅ Directories ensured: {DATA_FOLDER}, {ARCHIVE_FOLDER}")

def load_recent_csv_data(hours_back=24):
    """Load only recent CSV files (last 24 hours by default)"""
    logger.info(f"🔍 Loading recent CSV files from: {DATA_FOLDER}")
    
    # Get current time and calculate cutoff
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours_back)
    
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not csv_files:
        logger.warning("❌ No CSV files found")
        return None
    
    # Filter for recent files only
    recent_files = []
    for csv_file in sorted(csv_files):
        try:
            # Check file modification time
            file_mtime = datetime.fromtimestamp(os.path.getmtime(csv_file), tz=timezone.utc)
            if file_mtime >= cutoff:
                recent_files.append(csv_file)
                logger.info(f"✅ Recent file: {os.path.basename(csv_file)} (modified: {file_mtime})")
            else:
                logger.info(f"⏭️ Skipping old file: {os.path.basename(csv_file)} (modified: {file_mtime})")
        except Exception as e:
            logger.error(f"❌ Error checking {csv_file}: {e}")
    
    if not recent_files:
        logger.warning("❌ No recent CSV files found")
        return None
    
    logger.info(f"📁 Found {len(recent_files)} recent CSV files")
    
    all_dfs = []
    for csv_file in recent_files:
        try:
            df = pd.read_csv(csv_file, parse_dates=["timestamp"])
            if not df.empty:
                # Filter for recent data within the file - ensure timezone awareness
                df['timestamp_dt'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)
                recent_data = df[df['timestamp_dt'] >= cutoff.replace(tzinfo=None)].copy()
                if not recent_data.empty:
                    recent_data = recent_data.drop(columns=['timestamp_dt'])
                    all_dfs.append(recent_data)
                    logger.info(f"✅ Loaded recent data: {os.path.basename(csv_file)} ({len(recent_data)} rows)")
        except Exception as e:
            logger.error(f"❌ Error loading {csv_file}: {e}")
    
    if not all_dfs:
        logger.error("❌ No valid recent data found")
        return None
    
    # Combine all data and sort chronologically
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df = combined_df.sort_values("timestamp")
    combined_df = combined_df.drop_duplicates(subset=["timestamp"], keep="last")
    
    logger.info(f"✅ Combined recent dataset: {len(combined_df)} total rows")
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

def resample_to_10min(df):
    """Resample data to 10-minute intervals for historical data"""
    if df is None or df.empty:
        return None
    
    # Set timestamp as index for resampling
    df_indexed = df.set_index("timestamp")
    df_indexed.index = pd.to_datetime(df_indexed.index)
    
    # Resample to 10-minute intervals
    df_10min = df_indexed.resample("10min").agg({
        "price": "last",
        "spread_avg_L20_pct": "mean"
    }).dropna()
    
    # Calculate moving averages
    df_10min["ma_50"] = df_10min["spread_avg_L20_pct"].rolling(window=50, min_periods=1).mean()
    df_10min["ma_100"] = df_10min["spread_avg_L20_pct"].rolling(window=100, min_periods=1).mean()
    df_10min["ma_200"] = df_10min["spread_avg_L20_pct"].rolling(window=200, min_periods=1).mean()
    
    # Add data quality indicators
    df_10min["ma_50_valid"] = df_10min["spread_avg_L20_pct"].rolling(window=50).count() >= 50
    df_10min["ma_100_valid"] = df_10min["spread_avg_L20_pct"].rolling(window=100).count() >= 100
    df_10min["ma_200_valid"] = df_10min["spread_avg_L20_pct"].rolling(window=200).count() >= 200
    
    df_10min.reset_index(inplace=True)
    df_10min.rename(columns={"timestamp": "time"}, inplace=True)
    
    logger.info(f"📊 Resampled to {len(df_10min)} 10-minute intervals")
    return df_10min

def generate_recent_json(df_1min):
    """Generate recent.json with last 2 days of 1-minute data"""
    if df_1min is None or df_1min.empty:
        logger.warning("⚠️ No data available for recent.json")
        return 0
    
    # Import download function
    try:
        from gcs_uploader import download_from_gcs
    except ImportError:
        logger.warning("⚠️ GCS download not available - will create new recent.json")
        download_from_gcs = None
    
    # Constants for recent.json
    RECENT_JSON_LIMIT = 2880  # Keep last 2,880 entries (2 days of 1-minute data)
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    gcs_path = "recent.json"
    
    # Check if recent.json exists in GCS first (prioritize live data)
    existing_data = None
    
    # Try to download from GCS first (live data)
    if download_from_gcs and GCS_AVAILABLE:
        try:
            logger.info("📄 Downloading existing recent.json from GCS (live data)")
            if download_from_gcs(gcs_path, recent_path):
                existing_data = pd.read_json(recent_path, orient="records")
                logger.info(f"✅ Downloaded and loaded {len(existing_data)} existing records from GCS recent.json")
            else:
                logger.info("ℹ️ No existing recent.json found in GCS")
                existing_data = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to download recent.json from GCS: {e}")
            existing_data = None
    
    # Only check local file if GCS is not available or download failed
    if existing_data is None and os.path.exists(recent_path):
        try:
            logger.info("📄 Loading existing local recent.json (fallback)")
            existing_data = pd.read_json(recent_path, orient="records")
            logger.info(f"✅ Loaded {len(existing_data)} existing records from local recent.json")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load local recent.json: {e}")
            existing_data = None
    
    # Get new data for recent.json (last RECENT_HOURS hours)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=RECENT_HOURS)
    
    # Filter for recent data - ensure timezone awareness
    df_1min_copy = df_1min.copy()
    df_1min_copy['time_dt'] = pd.to_datetime(df_1min_copy['time']).dt.tz_localize(None)
    new_data = df_1min_copy[df_1min_copy['time_dt'] >= cutoff.replace(tzinfo=None)].copy()
    new_data = new_data.drop(columns=['time_dt'])
    
    if new_data.empty:
        logger.warning(f"⚠️ No data in last {RECENT_HOURS} hours, using all available data")
        new_data = df_1min.copy()
    
    # Combine existing and new data
    if existing_data is not None and not existing_data.empty:
        # Convert timestamps to datetime for proper merging - handle both timezone-aware and naive
        try:
            # Try parsing with timezone handling first
            existing_data['time_dt'] = pd.to_datetime(existing_data['time'], errors='coerce')
            # Remove timezone info if present
            existing_data['time_dt'] = existing_data['time_dt'].dt.tz_localize(None)
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse existing timestamps: {e}")
            # Fallback: try without timezone handling
            existing_data['time_dt'] = pd.to_datetime(existing_data['time'], errors='coerce')
        
        new_data['time_dt'] = pd.to_datetime(new_data['time']).dt.tz_localize(None)
        
        # Remove any rows with invalid timestamps
        existing_data = existing_data.dropna(subset=['time_dt'])
        new_data = new_data.dropna(subset=['time_dt'])
        
        if not existing_data.empty and not new_data.empty:
            # Remove duplicates based on timestamp
            combined_data = pd.concat([existing_data, new_data], ignore_index=True)
            combined_data = combined_data.drop_duplicates(subset=['time_dt'], keep='last')
            
            # Sort by timestamp
            combined_data = combined_data.sort_values('time_dt')
            
            # Remove temporary time_dt column
            combined_data = combined_data.drop(columns=['time_dt'])
            
            logger.info(f"🔄 Merged {len(existing_data)} existing + {len(new_data)} new = {len(combined_data)} total records for recent.json")
        else:
            combined_data = new_data.drop(columns=['time_dt']) if not new_data.empty else existing_data.drop(columns=['time_dt'])
            logger.info(f"🔄 Used available data: {len(combined_data)} records for recent.json")
    else:
        combined_data = new_data
        logger.info(f"🆕 Creating new recent.json with {len(combined_data)} records")
    
    # Trim to keep only the last RECENT_JSON_LIMIT entries
    if len(combined_data) > RECENT_JSON_LIMIT:
        combined_data = combined_data.tail(RECENT_JSON_LIMIT)
        logger.info(f"✂️ Trimmed recent.json to last {RECENT_JSON_LIMIT} entries")
    
    # Save recent.json locally with strict JSON (no NaN/Inf)
    write_json_records(combined_data, recent_path)
    
    logger.info(f"⚡ Generated recent.json: {len(combined_data)} records (last {RECENT_HOURS} hours, max {RECENT_JSON_LIMIT} entries)")
    
    # Upload to GCS
    if GCS_AVAILABLE:
        try:
            if upload_to_gcs(recent_path, gcs_path, content_type="application/json"):
                logger.info("✅ Uploaded recent.json to GCS")
            else:
                logger.warning("⚠️ Failed to upload recent.json to GCS")
        except Exception as e:
            logger.error(f"❌ GCS upload error for recent.json: {e}")
    
    return len(combined_data)

def generate_daily_archives(df_1min):
    """Generate daily archive files in archive/1min/YYYY-MM-DD.json format"""
    if df_1min is None or df_1min.empty:
        logger.warning("⚠️ No data available for daily archives")
        return []
    
    # Import download function
    try:
        from gcs_uploader import download_from_gcs
    except ImportError:
        logger.warning("⚠️ GCS download not available - will create new archive files")
        download_from_gcs = None
    
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
        gcs_path = f"archive/1min/{filename}"
        
        # Check if file exists in GCS first (prioritize live data)
        existing_data = None
        
        # Try to download from GCS first (live data)
        if download_from_gcs and GCS_AVAILABLE:
            try:
                logger.info(f"📄 Downloading existing archive from GCS: {filename} (live data)")
                if download_from_gcs(gcs_path, file_path):
                    existing_data = pd.read_json(file_path, orient="records")
                    logger.info(f"✅ Downloaded and loaded {len(existing_data)} existing records from GCS {filename}")
                else:
                    logger.info(f"ℹ️ No existing archive found in GCS: {filename}")
                    existing_data = None
            except Exception as e:
                logger.warning(f"⚠️ Failed to download {filename} from GCS: {e}")
                existing_data = None
        
        # Only check local file if GCS is not available or download failed
        if existing_data is None and os.path.exists(file_path):
            try:
                logger.info(f"📄 Loading existing local archive: {filename} (fallback)")
                existing_data = pd.read_json(file_path, orient="records")
                logger.info(f"✅ Loaded {len(existing_data)} existing records from local {filename}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load local {filename}: {e}")
                existing_data = None
        
        # Combine existing and new data
        if existing_data is not None and not existing_data.empty:
            # Convert timestamps to datetime for proper merging - handle both timezone-aware and naive
            try:
                # Try parsing with timezone handling first
                existing_data['time_dt'] = pd.to_datetime(existing_data['time'], errors='coerce')
                # Remove timezone info if present
                existing_data['time_dt'] = existing_data['time_dt'].dt.tz_localize(None)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse existing timestamps: {e}")
                # Fallback: try without timezone handling
                existing_data['time_dt'] = pd.to_datetime(existing_data['time'], errors='coerce')
            
            day_data_clean['time_dt'] = pd.to_datetime(day_data_clean['time']).dt.tz_localize(None)
            
            # Remove any rows with invalid timestamps
            existing_data = existing_data.dropna(subset=['time_dt'])
            day_data_clean = day_data_clean.dropna(subset=['time_dt'])
            
            if not existing_data.empty and not day_data_clean.empty:
                # Remove duplicates based on timestamp
                combined_data = pd.concat([existing_data, day_data_clean], ignore_index=True)
                combined_data = combined_data.drop_duplicates(subset=['time_dt'], keep='last')
                
                # Sort by timestamp
                combined_data = combined_data.sort_values('time_dt')
                
                # Remove temporary time_dt column
                combined_data = combined_data.drop(columns=['time_dt'])
                
                logger.info(f"🔄 Merged {len(existing_data)} existing + {len(day_data_clean)} new = {len(combined_data)} total records for {filename}")
            else:
                combined_data = day_data_clean.drop(columns=['time_dt']) if not day_data_clean.empty else existing_data.drop(columns=['time_dt'])
                logger.info(f"🔄 Used available data: {len(combined_data)} records for {filename}")
        else:
            combined_data = day_data_clean
            logger.info(f"🆕 Creating new archive: {filename} with {len(combined_data)} records")
        
        # Save daily archive locally with strict JSON (no NaN/Inf)
        write_json_records(combined_data, file_path)
        daily_files.append(filename)
        
        logger.info(f"📅 Generated daily archive: {filename} ({len(combined_data)} records)")
        
        # Upload to GCS
        if GCS_AVAILABLE:
            try:
                if upload_to_gcs(file_path, gcs_path, content_type="application/json"):
                    logger.info(f"✅ Uploaded {filename} to GCS")
                else:
                    logger.warning(f"⚠️ Failed to upload {filename} to GCS")
            except Exception as e:
                logger.error(f"❌ GCS upload error for {filename}: {e}")
    
    logger.info(f"✅ Generated {len(daily_files)} daily archive files")
    return daily_files

def generate_historical_json(df_10min):
    """Generate historical.json with 10-minute candles for long-term history"""
    if df_10min is None or df_10min.empty:
        logger.warning("⚠️ No data available for historical.json")
        return 0
    
    # Import download function
    try:
        from gcs_uploader import download_from_gcs
    except ImportError:
        logger.warning("⚠️ GCS download not available - will create new historical.json")
        download_from_gcs = None
    
    # Constants for historical.json
    HISTORICAL_JSON_LIMIT = 9000  # Keep last 9,000 entries (about 2 months of 10-minute data)
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    gcs_path = "historical.json"
    
    # Check if historical.json exists in GCS first (prioritize live data)
    existing_data = None
    
    # Try to download from GCS first (live data)
    if download_from_gcs and GCS_AVAILABLE:
        try:
            logger.info("📄 Downloading existing historical.json from GCS (live data)")
            if download_from_gcs(gcs_path, historical_path):
                existing_data = pd.read_json(historical_path, orient="records")
                logger.info(f"✅ Downloaded and loaded {len(existing_data)} existing records from GCS historical.json")
            else:
                logger.info("ℹ️ No existing historical.json found in GCS")
                existing_data = None
        except Exception as e:
            logger.warning(f"⚠️ Failed to download historical.json from GCS: {e}")
            existing_data = None
    
    # Only check local file if GCS is not available or download failed
    if existing_data is None and os.path.exists(historical_path):
        try:
            logger.info("📄 Loading existing local historical.json (fallback)")
            existing_data = pd.read_json(historical_path, orient="records")
            logger.info(f"✅ Loaded {len(existing_data)} existing records from local historical.json")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load local historical.json: {e}")
            existing_data = None
    
    # Prepare new data for historical.json
    new_data = df_10min.copy()
    
    # Combine existing and new data
    if existing_data is not None and not existing_data.empty:
        # Convert timestamps to datetime for proper merging - handle both timezone-aware and naive
        try:
            # Try parsing with timezone handling first
            existing_data['time_dt'] = pd.to_datetime(existing_data['time'], errors='coerce')
            # Remove timezone info if present
            existing_data['time_dt'] = existing_data['time_dt'].dt.tz_localize(None)
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse existing timestamps: {e}")
            # Fallback: try without timezone handling
            existing_data['time_dt'] = pd.to_datetime(existing_data['time'], errors='coerce')
        
        new_data['time_dt'] = pd.to_datetime(new_data['time']).dt.tz_localize(None)
        
        # Remove any rows with invalid timestamps
        existing_data = existing_data.dropna(subset=['time_dt'])
        new_data = new_data.dropna(subset=['time_dt'])
        
        if not existing_data.empty and not new_data.empty:
            # Remove duplicates based on timestamp
            combined_data = pd.concat([existing_data, new_data], ignore_index=True)
            combined_data = combined_data.drop_duplicates(subset=['time_dt'], keep='last')
            
            # Sort by timestamp
            combined_data = combined_data.sort_values('time_dt')
            
            # Remove temporary time_dt column
            combined_data = combined_data.drop(columns=['time_dt'])
            
            logger.info(f"🔄 Merged {len(existing_data)} existing + {len(new_data)} new = {len(combined_data)} total records for historical.json")
        else:
            combined_data = new_data.drop(columns=['time_dt']) if not new_data.empty else existing_data.drop(columns=['time_dt'])
            logger.info(f"🔄 Used available data: {len(combined_data)} records for historical.json")
    else:
        combined_data = new_data
        logger.info(f"🆕 Creating new historical.json with {len(combined_data)} records")
    
    # Trim to keep only the last HISTORICAL_JSON_LIMIT entries
    if len(combined_data) > HISTORICAL_JSON_LIMIT:
        combined_data = combined_data.tail(HISTORICAL_JSON_LIMIT)
        logger.info(f"✂️ Trimmed historical.json to last {HISTORICAL_JSON_LIMIT} entries")
    
    # Save historical.json locally with strict JSON (no NaN/Inf)
    write_json_records(combined_data, historical_path)
    
    logger.info(f"📚 Generated historical.json: {len(combined_data)} records (10-minute candles, max {HISTORICAL_JSON_LIMIT} entries)")
    
    # Upload to GCS
    if GCS_AVAILABLE:
        try:
            if upload_to_gcs(historical_path, gcs_path, content_type="application/json"):
                logger.info("✅ Uploaded historical.json to GCS")
            else:
                logger.warning("⚠️ Failed to upload historical.json to GCS")
        except Exception as e:
            logger.error(f"❌ GCS upload error for historical.json: {e}")
    
    return len(combined_data)

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
                "description": "Complete dataset with 10-minute candles",
                "records": historical_count,
                "update_frequency": "every_10_minutes"
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
            "historical.json": "Complete dataset with 10-minute candles", 
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
    """Main function to generate all JSON files from recent data only"""
    logger.info("🚀 Starting scalable JSON generation (recent data only)...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load recent CSV data (last 24 hours)
    df_raw = load_recent_csv_data(hours_back=24)
    if df_raw is None:
        logger.error("❌ No recent data to process")
        return False
    
    # Resample to 1-minute intervals
    df_1min = resample_to_1min(df_raw)
    if df_1min is None:
        logger.error("❌ Failed to resample to 1-minute intervals")
        return False
    
    # Resample to 1-hour intervals for historical data
    df_10min = resample_to_10min(df_raw)
    if df_10min is None:
        logger.error("❌ Failed to resample to 10-minute intervals")
        return False
    
    # Generate all JSON files
    recent_count = generate_recent_json(df_1min)
    daily_files = generate_daily_archives(df_1min)
    historical_count = generate_historical_json(df_10min)
    index_data = generate_index_json(recent_count, historical_count, daily_files)
    
    logger.info("✅ Scalable JSON generation completed (recent data only)!")
    logger.info(f"📊 Summary:")
    logger.info(f"   • recent.json: {recent_count} records")
    logger.info(f"   • historical.json: {historical_count} records") 
    logger.info(f"   • Daily archives: {len(daily_files)} files")
    
    return True

if __name__ == "__main__":
    generate_all_jsons()