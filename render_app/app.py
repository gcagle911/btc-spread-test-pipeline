from flask import Flask, jsonify
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Test Render app is live ✅",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "price": 12345.67,   # fake data
        "spread": 0.01,      # fake data
        "bug_detector": "🪲 If this loads, backend is working!"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
