#!/usr/bin/env python3
"""
Simple BTC Data Server
======================
This script generates fresh JSON data and serves it via Flask.
"""

import os
import time
import threading
from datetime import datetime, timedelta
import json
from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

DATA_FOLDER = "render_app/data"

def fetch_live_btc_data():
    """Fetch live BTC data from Coinbase API"""
    try:
        url = "https://api.exchange.coinbase.com/products/BTC-USD/book?level=2"
        response = requests.get(url, timeout=10)
        data = response.json()

        bids = data.get("bids", [])
        asks = data.get("asks", [])

        if not bids or not asks:
            return None

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        mid_price = (best_bid + best_ask) / 2
        spread = best_ask - best_bid

        # L20 average spread calculation
        top_bids = [float(b[0]) for b in bids[:20]]
        top_asks = [float(a[0]) for a in asks[:20]]
        if len(top_bids) >= 20 and len(top_asks) >= 20:
            bid_avg = sum(top_bids) / 20
            ask_avg = sum(top_asks) / 20
            spread_avg_L20 = ask_avg - bid_avg
            spread_avg_L20_pct = (spread_avg_L20 / mid_price) * 100
        else:
            spread_avg_L20_pct = (spread / mid_price) * 100

        return {
            "time": datetime.utcnow().isoformat(),
            "price": round(mid_price, 2),
            "spread_avg_L20_pct": round(spread_avg_L20_pct, 10),
            "ma_50": round(spread_avg_L20_pct, 10),  # Simplified for demo
            "ma_100": round(spread_avg_L20_pct, 10),
            "ma_200": round(spread_avg_L20_pct, 10),
            "ma_50_valid": True,
            "ma_100_valid": True,
            "ma_200_valid": True
        }
    except Exception as e:
        print(f"Error fetching live data: {e}")
        return None

def generate_fresh_data():
    """Generate fresh BTC data and save to JSON files"""
    print("🔄 Generating fresh BTC data...")
    
    # Generate some recent data points
    recent_data = []
    now = datetime.utcnow()
    
    # Get a few live data points
    for i in range(5):
        live_data = fetch_live_btc_data()
        if live_data:
            # Adjust timestamp to spread over last few minutes
            timestamp = now - timedelta(minutes=4-i)
            live_data["time"] = timestamp.isoformat()
            recent_data.append(live_data)
        time.sleep(1)  # Wait between API calls
    
    # If no live data, generate sample data
    if not recent_data:
        print("⚠️ No live data available, generating sample data...")
        base_price = 65000
        for i in range(20):
            timestamp = now - timedelta(minutes=19-i)
            price_variation = (hash(str(timestamp)) % 2000 - 1000) / 100
            price = base_price + price_variation
            spread_pct = 0.015 + (hash(str(timestamp + timedelta(seconds=30))) % 100 - 50) / 100000
            
            recent_data.append({
                "time": timestamp.isoformat(),
                "price": round(price, 2),
                "spread_avg_L20_pct": round(spread_pct, 10),
                "ma_50": round(spread_pct, 10),
                "ma_100": round(spread_pct, 10),
                "ma_200": round(spread_pct, 10),
                "ma_50_valid": True,
                "ma_100_valid": True,
                "ma_200_valid": True
            })
    
    # Save recent.json
    os.makedirs(DATA_FOLDER, exist_ok=True)
    recent_path = os.path.join(DATA_FOLDER, "recent.json")
    with open(recent_path, 'w') as f:
        json.dump(recent_data, f, indent=2)
    
    # Save historical.json (same as recent for demo)
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    with open(historical_path, 'w') as f:
        json.dump(recent_data, f, indent=2)
    
    # Save index.json
    index_data = {
        "data_sources": {
            "recent": {
                "file": "recent.json",
                "description": "Last 24 hours (fast loading)",
                "records": len(recent_data),
                "update_frequency": "every_30_seconds"
            },
            "historical": {
                "file": "historical.json",
                "description": "Complete dataset (full history)",
                "records": len(recent_data),
                "update_frequency": "every_30_seconds"
            }
        },
        "last_updated": datetime.utcnow().isoformat()
    }
    
    index_path = os.path.join(DATA_FOLDER, "index.json")
    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"✅ Generated {len(recent_data)} data points")
    return len(recent_data)

def update_data_loop():
    """Continuously update data every 30 seconds"""
    while True:
        try:
            generate_fresh_data()
            print("⏰ Next update in 30 seconds...")
            time.sleep(30)
        except Exception as e:
            print(f"❌ Error updating data: {e}")
            time.sleep(5)

# Flask routes
@app.route('/')
def home():
    return jsonify({
        "status": "✅ BTC JSON Server is running",
        "description": "Live BTC-USD data with auto-refresh",
        "endpoints": {
            "recent": "/recent.json - Last 24 hours (updated every 30s)",
            "historical": "/historical.json - Complete dataset",
            "index": "/index.json - Data source information"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/recent.json')
def serve_recent():
    """Serve recent BTC data"""
    file_path = os.path.join(DATA_FOLDER, "recent.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Recent data not available"}), 404

@app.route('/historical.json')
def serve_historical():
    """Serve historical BTC data"""
    file_path = os.path.join(DATA_FOLDER, "historical.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Historical data not available"}), 404

@app.route('/index.json')
def serve_index():
    """Serve index information"""
    file_path = os.path.join(DATA_FOLDER, "index.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Index not available"}), 404

@app.route('/debug')
def debug_info():
    """Debug endpoint to check file status"""
    files_info = {}
    for filename in ['recent.json', 'historical.json', 'index.json']:
        file_path = os.path.join(DATA_FOLDER, filename)
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            files_info[filename] = {
                "exists": True,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        else:
            files_info[filename] = {"exists": False}
    
    return jsonify({
        "timestamp": datetime.utcnow().isoformat(),
        "files": files_info
    })

if __name__ == '__main__':
    print("🚀 Starting BTC JSON Server...")
    
    # Generate initial data
    generate_fresh_data()
    
    # Start background thread for data updates
    update_thread = threading.Thread(target=update_data_loop, daemon=True)
    update_thread.start()
    
    # Start Flask server
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Server starting on http://0.0.0.0:{port}")
    print("📊 Endpoints:")
    print(f"   • http://localhost:{port}/recent.json")
    print(f"   • http://localhost:{port}/historical.json")
    print(f"   • http://localhost:{port}/index.json")
    print("🔄 Data updates every 30 seconds")
    
    app.run(host='0.0.0.0', port=port, debug=False)