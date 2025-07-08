from flask_cors import CORS
from process_data import process_csv_to_json
import requests
import csv
import time
import os
from datetime import datetime, UTC
from flask import Flask, jsonify, send_file, send_from_directory, abort
import threading

app = Flask(__name__)
CORS(app)

last_logged = {"timestamp": None}

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# 🔁 Rotates files every 8 hours (00, 08, 16 UTC)
def get_current_csv_filename():
    now = datetime.now(UTC)
    hour_block = (now.hour // 8) * 8
    block_label = f"{hour_block:02d}"
    date_str = now.strftime("%Y-%m-%d")
    return f"{date_str}_{block_label}.csv"

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
        spread_avg_L20 = spread
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

            last_logged["timestamp"] = data["timestamp"]
            print(f"[{data['timestamp']}] ✅ Logged to {filename}")

            # Run JSON generation based on today's latest CSV
            process_csv_to_json()

        except Exception as e:
            print("🚨 Error in logger loop:", str(e))

        elapsed = time.time() - start_time
        sleep_time = max(0, 1.0 - elapsed)
        time.sleep(sleep_time)

# ---- Flask Routes ----

@app.route("/")
def home():
    return {
        "status": "✅ BTC Logger is running",
        "last_log_time": last_logged["timestamp"],
        "endpoints": [
            "/data.csv",
            "/csv-list",
            "/csv/<filename>",
            "/json/output_<YYYY-MM-DD>.json"
        ]
    }

@app.route("/data.csv")
def get_current_csv():
    filename = os.path.join(DATA_FOLDER, get_current_csv_filename())
    if os.path.exists(filename):
        return send_file(filename, as_attachment=False)
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

@app.route("/json/output_<date>.json")
def serve_json_file(date):
    file_path = os.path.join(DATA_FOLDER, f"output_{date}.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return "JSON file not found", 404

@app.route("/output-latest.json")
def serve_latest_output():
    today = datetime.utcnow().date()
    filename = f"output_{today}.json"
    file_path = os.path.join(DATA_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return "Latest JSON not available", 404

# ---- App Runner ----

def run_app():
    app.run(host="0.0.0.0", port=10000)

# Start logger and web server
if __name__ == "__main__":
    threading.Thread(target=log_data, daemon=True).start()
    run_app()
