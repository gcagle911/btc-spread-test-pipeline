from process_data import process_csv_to_json
import requests
import csv
import time
import os
from datetime import datetime, UTC
from flask import Flask, jsonify, send_file, send_from_directory, abort
import threading

app = Flask(__name__)

last_logged = {"timestamp": None}

DATA_FOLDER = "data"
def get_current_csv_filename():
     return f"{datetime.now(UTC).date()}.csv"
os.makedirs(DATA_FOLDER, exist_ok=True)

def fetch_orderbook():
    url = "https://api.exchange.coinbase.com/products/BTC-USD/book?level=2"
    response = requests.get(url)
    data = response.json()

    bids = data.get("bids", [])
    asks = data.get("asks", [])

    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    mid_price = (best_bid + best_ask) / 2
    spread = best_ask - best_bid

    # L20 average spread calculation
    top_bids = [float(b[0]) for b in bids[:20]]
    top_asks = [float(a[0]) for a in asks[:20]]
    if len(top_bids) < 20 or len(top_asks) < 20:
        spread_avg_L20 = spread  # fallback
        spread_avg_L20_pct = (spread / mid_price) * 100
    else:
        bid_avg = sum(top_bids) / 20
        ask_avg = sum(top_asks) / 20
        spread_avg_L20 = ask_avg - bid_avg
        spread_avg_L20_pct = (spread_avg_L20 / mid_price) * 100

    volume = sum(float(b[1]) for b in bids[:20]) + sum(float(a[1]) for a in asks[:20])
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "asset": "BTC-USD",
        "exchange": "Coinbase",
        "price": mid_price,
        "bid": best_bid,
        "ask": best_ask,
        "spread": spread,
        "volume": volume,
        "spread_avg_L20": spread_avg_L20,
        "spread_avg_L20_pct": spread_avg_L20_pct
    }

def log_data():
    while True:
        start_time = time.time()
        try:
            data = fetch_orderbook()
            filename = os.path.join(DATA_FOLDER, get_current_csv_filename())
            file_exists = os.path.isfile(filename)

            with open(filename, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)

            last_logged["timestamp"] = data["timestamp"]  # ✅ update heartbeat
            print(f"[{data['timestamp']}] ✅ Logged")

            process_csv_to_json()

        except Exception as e:
            print("🚨 Error in logger loop:", str(e))

        elapsed = time.time() - start_time
        sleep_time = max(0, 1.0 - elapsed)
        time.sleep(sleep_time)

@app.route("/")
def home():
    return {
        "status": "✅ BTC Logger is running",
        "last_log_time": last_logged["timestamp"],
        "endpoints": [
            "/data.csv",
            "/csv-list",
            "/csv/<filename>"
        ]
    }

@app.route("/data.csv")
def get_current_csv():
    today_file = os.path.join(DATA_FOLDER, f"{datetime.utcnow().date()}.csv")
    if os.path.exists(today_file):
        return send_file(today_file, as_attachment=False)
    else:
        return "No data file available", 404

@app.route("/csv-list")
def list_csvs():
    try:
        files = sorted(os.listdir(DATA_FOLDER))
        return jsonify({"available_csvs": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/csv/<filename>")
def download_csv(filename):
    try:
        return send_from_directory(DATA_FOLDER, filename)
    except FileNotFoundError:
        abort(404)

from flask import send_from_directory

import os

@app.route("/output.json")
def serve_output_json():
    output_path = os.path.join(os.path.dirname(__file__), "data")
    return send_from_directory(output_path, "output.json")

def run_app():
    app.run(host="0.0.0.0", port=10000)
    
import process_data
process_data.process_csv_to_json()

if __name__ == "__main__":
    threading.Thread(target=log_data, daemon=True).start()
    run_app()

import subprocess
subprocess.run(["python", "process_data.py"])
