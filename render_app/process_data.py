import pandas as pd
import os
from datetime import datetime

DATA_FOLDER = "data"
OUTPUT_FILE = os.path.join(DATA_FOLDER, "output.json")

def process_csv_to_json():
    today = datetime.utcnow().date()
    csv_file = os.path.join(DATA_FOLDER, f"{today}.csv")

    if not os.path.exists(csv_file):
        print("CSV file not found.")
        return

    df = pd.read_csv(csv_file, parse_dates=["timestamp"])

    # Resample to 1-minute intervals
    df.set_index("timestamp", inplace=True)
    df.index = pd.to_datetime(df.index)
    df_1min = df.resample("1min").agg({
        "price": "last",
        "spread_avg_L20_pct": "mean"
    }).dropna()

    # Calculate moving averages
    df_1min["ma_50"] = df_1min["spread_avg_L20_pct"].rolling(window=50).mean()
    df_1min["ma_100"] = df_1min["spread_avg_L20_pct"].rolling(window=100).mean()
    df_1min["ma_200"] = df_1min["spread_avg_L20_pct"].rolling(window=200).mean()

    # Save output
    df_1min.reset_index(inplace=True)
    df_1min.rename(columns={"timestamp": "time"}, inplace=True)
    df_1min.to_json(OUTPUT_FILE, orient="records", date_format="iso")
    print("✅ output.json updated")

if __name__ == "__main__":
    process_csv_to_json()
