import pandas as pd
import os
import json
from datetime import datetime, timedelta
import glob

DATA_FOLDER = "render_app/data"

def load_all_historical_data():
    """Load and combine all CSV files into a single chronological dataset"""
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    
    if not csv_files:
        print("❌ No CSV files found")
        return None
    
    print(f"📁 Found {len(csv_files)} CSV files")
    
    all_dfs = []
    for csv_file in sorted(csv_files):
        try:
            df = pd.read_csv(csv_file, parse_dates=["timestamp"])
            if not df.empty:
                all_dfs.append(df)
                print(f"📄 Loaded: {os.path.basename(csv_file)} ({len(df)} rows)")
        except Exception as e:
            print(f"⚠️ Error loading {csv_file}: {e}")
    
    if not all_dfs:
        print("❌ No valid data found")
        return None
    
    # Combine all data and sort chronologically
    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df = combined_df.sort_values("timestamp")
    combined_df = combined_df.drop_duplicates(subset=["timestamp"], keep="last")
    
    print(f"✅ Combined dataset: {len(combined_df)} total rows")
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

def save_daily_jsons(df_full):
    """Create individual daily JSON files for each day in the dataset"""
    if df_full is None or df_full.empty:
        return []
    
    df_full["date"] = pd.to_datetime(df_full["time"]).dt.date
    daily_files = []
    
    for date, day_data in df_full.groupby("date"):
        day_data_clean = day_data.drop(columns=["date"])
        
        output_file = f"output_{date}.json"
        output_path = os.path.join(DATA_FOLDER, output_file)
        
        day_data_clean.to_json(output_path, orient="records", date_format="iso")
        daily_files.append(output_file)
        print(f"� Saved daily: {output_file} ({len(day_data_clean)} records)")
    
    return daily_files

def save_historical_json(df_full):
    """Save complete historical dataset as one JSON file"""
    if df_full is None or df_full.empty:
        return None
    
    # Add metadata
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(df_full),
        "date_range": {
            "start": df_full["time"].min(),
            "end": df_full["time"].max()
        },
        "ma_info": {
            "ma_50_valid_count": int(df_full["ma_50_valid"].sum()),
            "ma_100_valid_count": int(df_full["ma_100_valid"].sum()),
            "ma_200_valid_count": int(df_full["ma_200_valid"].sum())
        }
    }
    
    # Prepare data for JSON output
    df_output = df_full.copy()
    
    # Save complete historical data
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    df_output.to_json(historical_path, orient="records", date_format="iso")
    
    # Save metadata separately
    metadata_path = os.path.join(DATA_FOLDER, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    
    print(f"✅ Saved historical: historical.json ({len(df_output)} records)")
    print(f"✅ Saved metadata: metadata.json")
    
    return historical_path

def save_index_json(daily_files):
    """Create index file with list of available daily files"""
    index_data = {
        "available_days": sorted(daily_files),
        "historical_file": "historical.json",
        "metadata_file": "metadata.json",
        "last_updated": datetime.utcnow().isoformat()
    }
    
    index_path = os.path.join(DATA_FOLDER, "index.json")
    with open(index_path, "w") as f:
        json.dump(index_data, f, indent=2)
    
    print(f"✅ Saved index: index.json")

def process_csv_to_json():
    """Main function: Process all data and create comprehensive JSON outputs"""
    print("🚀 Starting comprehensive data processing...")
    
    # Step 1: Load all historical data
    df_combined = load_all_historical_data()
    if df_combined is None:
        return
    
    # Step 2: Resample and calculate MAs with full context
    df_processed = resample_and_calculate_mas(df_combined)
    if df_processed is None:
        return
    
    # Step 3: Save individual daily JSON files
    daily_files = save_daily_jsons(df_processed)
    
    # Step 4: Save complete historical JSON
    save_historical_json(df_processed)
    
    # Step 5: Create index file
    save_index_json(daily_files)
    
    print("✅ Processing complete!")
    print(f"📈 Historical data spans {len(df_processed)} minutes")
    print(f"📅 Generated {len(daily_files)} daily files")
    print("🔄 Charts can now use 'historical.json' for continuous data")

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
