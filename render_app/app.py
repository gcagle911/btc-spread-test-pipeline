from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '✅ Render backend is running.'

@app.route('/static/output.json')
def serve_json():
    return send_from_directory('static', 'output.json')

if __name__ == '__main__':
    app.run()
