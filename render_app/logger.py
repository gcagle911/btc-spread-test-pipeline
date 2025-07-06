import requests
import csv
import time
from datetime import datetime
from flask import Flask, send_file, jsonify
import threading
import os

CSV_FILE = 'data.csv'
JSON_FILE = 'output.json'
app = Flask(__name__)

# Initialize CSV if it doesn't exist
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'price', 'bid', 'ask', 'spread', 'volume'])

def fetch_data():
    while True:
        try:
            res = requests.get('https://api.exchange.coinbase.com/products/BTC-USD/ticker')
            data = res.json()

            price = float(data['price'])
            bid = float(data['bid'])
            ask = float(data['ask'])
            spread = ask - bid
            volume = float(data['volume'])
            timestamp = datetime.utcnow().isoformat()

            # Append to CSV
            with open(CSV_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, price, bid, ask, spread, volume])

            # Write latest row to JSON
            with open(JSON_FILE, 'w') as f:
                jsonify_obj = {
                    "timestamp": timestamp,
                    "price": price,
                    "bid": bid,
                    "ask": ask,
                    "spread": spread,
                    "volume": volume
                }
                f.write(str(jsonify_obj).replace("'", '"'))

        except Exception as e:
            print("Error fetching data:", e)

        time.sleep(1)

@app.route('/')
def root():
    return 'Logger running'

@app.route('/output.json')
def serve_json():
    return send_file(JSON_FILE)

# Background thread to fetch and log data
def start_logging():
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()

start_logging()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
