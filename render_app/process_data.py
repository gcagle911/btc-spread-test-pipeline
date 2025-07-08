import pandas as pd
import os
import json
from datetime import datetime

DATA_FOLDER = "data"

def process_csv_to_json():
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Find all CSVs from today
    files = sorted(
        f for f in os.listdir(DATA_FOLDER)
        if f.startswith(today) and f.endswith(".csv")
    )

    if not files:
        print(f"❌ No CSVs found for {today}")
        return

    latest_file = files[-1]
    csv_path = os.path.join(DATA_FOLDER, latest_file)
    print(f"📄 Processing: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    if df.empty:
        print("❌ CSV is empty")
        return

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

    # Save output with today's date in filename
    df_1min.reset_index(inplace=True)
    df_1min.rename(columns={"timestamp": "time"}, inplace=True)

    output_path = os.path.join(DATA_FOLDER, f"output_{today}.json")
    df_1min.to_json(output_path, orient="records", date_format="iso")
    print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    process_csv_to_json()
