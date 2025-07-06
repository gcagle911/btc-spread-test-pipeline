from flask import Flask, send_file, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return {
        'status': '✅ BTC Logger API is live',
        'available_endpoints': [
            '/data.csv',
            '/list_csvs',
            '/data/YYYY-MM-DD.csv'
        ]
    }

@app.route('/data.csv')
def serve_current_csv():
    return send_file('data.csv')

@app.route('/list_csvs')
def list_csvs():
    files = [f for f in os.listdir() if f.endswith('.csv') and f != 'data.csv']
    return jsonify({'available_csvs': files})

@app.route('/data/<date>.csv')
def serve_csv_by_date(date):
    filename = f"{date}.csv"
    if os.path.exists(filename):
        return send_file(filename)
    else:
        return jsonify({'error': f'CSV for {date} not found'}), 404

if __name__ == '__main__':
    app.run()
