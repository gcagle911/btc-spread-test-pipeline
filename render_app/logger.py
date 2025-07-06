# logger.py (Final enterprise version with 1-second logging + daily CSV rotation)
import requests
import csv
import time
from datetime import datetime
from flask import Flask, send_file
import threading
import os

app = Flask(__name__)

def get_csv_filename():
    return f"{datetime.utcnow().date()}.csv"

def write_header_if_needed(filename):
    if not os.path.exists(filename):
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'price', 'bid', 'ask', 'spread_L1',
                'spread_L20', 'spread_plus_minus_5pct',
                'volume'
            ])

def fetch_data():
    url = 'https://api.exchange.coinbase.com/products/BTC-USD/book?level=2'
    stats_url = 'https://api.exchange.coinbase.com/products/BTC-USD/stats'
    headers = {'User-Agent': 'Mozilla/5.0'}

    book = requests.get(url, headers=headers).json()
    stats = requests.get(stats_url, headers=headers).json()

    best_bid = float(book['bids'][0][0])
    best_ask = float(book['asks'][0][0])
    mid_price = (best_bid + best_ask) / 2
    spread_L1 = round(best_ask - best_bid, 2)

    # Top 20 levels
    top_20_bids = [float(bid[0]) for bid in book['bids'][:20]]
    top_20_asks = [float(ask[0]) for ask in book['asks'][:20]]
    spread_L20 = round(min(top_20_asks) - max(top_20_bids), 2)

    # ±5% depth spread
    lower = mid_price * 0.95
    upper = mid_price * 1.05
    bounded_bids = [float(bid[0]) for bid in book['bids'] if float(bid[0]) >= lower]
    bounded_asks = [float(ask[0]) for ask in book['asks'] if float(ask[0]) <= upper]
    if bounded_bids and bounded_asks:
        spread_pm_5pct = round(min(bounded_asks) - max(bounded_bids), 2)
    else:
        spread_pm_5pct = None

    volume = float(stats['volume'])

    return {
        'timestamp': datetime.utcnow().isoformat(),
        'price': mid_price,
        'bid': best_bid,
        'ask': best_ask,
        'spread_L1': spread_L1,
        'spread_L20': spread_L20,
        'spread_plus_minus_5pct': spread_pm_5pct,
        'volume': volume
    }

def log_to_csv():
    while True:
        try:
            filename = get_csv_filename()
            write_header_if_needed(filename)
            row = fetch_data()
            with open(filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    row['timestamp'],
                    row['price'], row['bid'], row['ask'], row['spread_L1'],
                    row['spread_L20'], row['spread_plus_minus_5pct'],
                    row['volume']
                ])
            time.sleep(1)  # 1-second logging
        except Exception as e:
            print("Logging error:", e)
            time.sleep(1)

@app.route('/')
def index():
    return 'Logger running (enterprise grade)'

@app.route('/data')
def get_data():
    filename = get_csv_filename()
    return send_file(filename, mimetype='text/csv')

threading.Thread(target=log_to_csv, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
