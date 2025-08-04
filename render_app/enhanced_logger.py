#!/usr/bin/env python3
"""
Enhanced BTC Logger with Robust Backup and Auto-Restore
Integrates the enhanced backup system with automatic crash recovery
"""

import os
import sys
import time
import logging
import threading
from pathlib import Path
from datetime import datetime, UTC

# Import existing modules
from flask import Flask, jsonify, send_file, send_from_directory, abort, request
from flask_cors import CORS
import requests
import csv

# Import enhanced backup components
from enhanced_backup_system import get_backup_system, auto_backup_enhanced
from startup_restore import startup_check, check_data_integrity
from process_data import process_csv_to_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
DATA_FOLDER = "render_app/data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# Global state
last_logged = {"timestamp": None}
backup_system = None

def initialize_backup_system():
    """Initialize the enhanced backup system"""
    global backup_system
    try:
        backup_system = get_backup_system()
        logger.info("✅ Enhanced backup system initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize backup system: {e}")
        return False

def get_current_csv_filename():
    """Generate current CSV filename with 8-hour rotation"""
    now = datetime.now(UTC)
    hour_block = (now.hour // 8) * 8
    block_label = f"{hour_block:02d}"
    date_str = now.strftime("%Y-%m-%d")
    return f"{date_str}_{block_label}.csv"

def fetch_orderbook():
    """Fetch BTC orderbook data from Coinbase"""
    try:
        url = "https://api.exchange.coinbase.com/products/BTC-USD/book?level=2"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        bids = data.get("bids", [])
        asks = data.get("asks", [])

        if not bids or not asks:
            raise ValueError("Empty orderbook data received")

        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        spread = best_ask - best_bid
        mid_price = (best_bid + best_ask) / 2

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "mid_price": mid_price,
            "bid_volume": float(bids[0][1]),
            "ask_volume": float(asks[0][1])
        }
    except Exception as e:
        logger.error(f"❌ Error fetching orderbook: {e}")
        raise

def backup_on_critical_events():
    """Trigger immediate backup on critical events"""
    if backup_system:
        try:
            logger.info("🚨 Critical event detected, triggering immediate backup...")
            result = backup_system.backup_all_data()
            if result and result.get('success'):
                logger.info("✅ Critical event backup completed")
            else:
                logger.warning("⚠️ Critical event backup failed")
        except Exception as e:
            logger.error(f"❌ Critical event backup error: {e}")

def log_data():
    """Main data logging loop with enhanced error handling"""
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    while True:
        start_time = time.time()
        
        try:
            # Fetch and log data
            data = fetch_orderbook()
            filename = os.path.join(DATA_FOLDER, get_current_csv_filename())
            file_exists = os.path.isfile(filename)

            with open(filename, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)

            last_logged["timestamp"] = data["timestamp"]
            logger.info(f"✅ Logged to {filename}")

            # Process JSON data
            try:
                process_csv_to_json()
            except Exception as e:
                logger.error(f"❌ JSON processing error: {e}")

            # Check if backup is needed
            if backup_system:
                backup_system.check_and_backup_if_needed()

            # Reset error counter on success
            consecutive_errors = 0

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"🚨 Error in logger loop (#{consecutive_errors}): {e}")
            
            # If we have too many consecutive errors, trigger critical event backup
            if consecutive_errors >= max_consecutive_errors:
                logger.critical(f"💥 {max_consecutive_errors} consecutive errors detected!")
                backup_on_critical_events()
                
                # Try to restore data in case of corruption
                logger.info("🔄 Attempting data integrity check and restore...")
                integrity_check = check_data_integrity()
                if integrity_check['needs_restore']:
                    logger.warning("⚠️ Data integrity issues detected during error recovery")
                    from startup_restore import attempt_restore
                    attempt_restore()
                
                # Reset counter to avoid infinite backup loops
                consecutive_errors = 0

        # Sleep with adaptive timing
        elapsed = time.time() - start_time
        base_sleep = 1.0
        error_penalty = min(consecutive_errors * 0.5, 5.0)  # Max 5 seconds penalty
        sleep_time = max(0, base_sleep + error_penalty - elapsed)
        
        time.sleep(sleep_time)

# Flask Routes

@app.route("/")
def home():
    """Enhanced home endpoint with backup status"""
    backup_status = backup_system.get_backup_status() if backup_system else None
    integrity_check = check_data_integrity()
    
    return jsonify({
        "status": "✅ Enhanced BTC Logger is running",
        "last_log_time": last_logged["timestamp"],
        "data_integrity": integrity_check,
        "backup_status": backup_status,
        "description": "Enhanced BTC Logger with robust backup and auto-restore",
        "endpoints": {
            "data_access": [
                "/data.csv - Current CSV file",
                "/csv-list - List all CSV files", 
                "/csv/<filename> - Download specific CSV",
                "/recent.json - Last 24 hours data",
                "/historical.json - Complete dataset",
                "/metadata.json - Dataset metadata"
            ],
            "backup_management": [
                "/backup/status - Backup system status",
                "/backup/trigger - Manual backup trigger",
                "/backup/restore - Manual restore",
                "/backup/list - List all backups",
                "/backup/cleanup - Clean old backups"
            ],
            "health_monitoring": [
                "/health - System health check",
                "/integrity - Data integrity check"
            ]
        }
    })

@app.route("/data.csv")
def get_current_csv():
    """Serve current CSV file"""
    filename = os.path.join(DATA_FOLDER, get_current_csv_filename())
    if os.path.exists(filename):
        return send_file(filename, as_attachment=False)
    else:
        return jsonify({"error": "No current data file available"}), 404

@app.route("/csv-list")
def list_csvs():
    """List all available CSV files"""
    try:
        files = sorted(os.listdir(DATA_FOLDER))
        csv_files = [f for f in files if f.endswith('.csv')]
        return jsonify({
            "available_csvs": csv_files,
            "count": len(csv_files)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/csv/<filename>")
def download_csv(filename):
    """Download specific CSV file"""
    try:
        return send_from_directory(DATA_FOLDER, filename)
    except FileNotFoundError:
        abort(404)

@app.route("/recent.json")
def serve_recent_data():
    """Serve last 24 hours of data"""
    file_path = os.path.join(DATA_FOLDER, "recent.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Recent data not available"}), 404

@app.route("/historical.json")
def serve_historical_data():
    """Serve complete historical dataset"""
    file_path = os.path.join(DATA_FOLDER, "historical.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Historical data not available"}), 404

@app.route("/metadata.json")
def serve_metadata():
    """Serve dataset metadata"""
    file_path = os.path.join(DATA_FOLDER, "metadata.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Metadata not available"}), 404

# Enhanced Backup Management Routes

@app.route("/backup/status")
def backup_status():
    """Get comprehensive backup status"""
    if not backup_system:
        return jsonify({"error": "Backup system not initialized"}), 500
    
    try:
        status = backup_system.get_backup_status()
        integrity_check = check_data_integrity()
        
        return jsonify({
            "backup_system": status,
            "data_integrity": integrity_check,
            "available_providers": backup_system.get_available_providers()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/backup/trigger", methods=["POST"])
def trigger_backup():
    """Manually trigger backup"""
    if not backup_system:
        return jsonify({"error": "Backup system not initialized"}), 500
    
    try:
        providers = request.json.get('providers', None) if request.is_json else None
        result = backup_system.backup_all_data(providers)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": "Backup completed successfully",
                "details": result
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get('error', 'Backup failed'),
                "details": result
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/backup/restore", methods=["POST"])
def restore_backup():
    """Manually restore from backup"""
    if not backup_system:
        return jsonify({"error": "Backup system not initialized"}), 500
    
    try:
        data = request.json if request.is_json else {}
        provider = data.get('provider', None)
        target_folder = data.get('target_folder', None)
        
        result = backup_system.restore_latest_backup(provider, target_folder)
        
        if result.get('success'):
            return jsonify({
                "success": True,
                "message": "Restore completed successfully",
                "details": result
            })
        else:
            return jsonify({
                "success": False,
                "message": result.get('error', 'Restore failed'),
                "details": result
            }), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/backup/list")
def list_backups():
    """List all available backups"""
    if not backup_system:
        return jsonify({"error": "Backup system not initialized"}), 500
    
    try:
        providers = backup_system.get_available_providers()
        all_backups = {}
        
        for provider_name in providers:
            provider = backup_system.providers[provider_name]
            backup_files = provider.list_files("btc-data/")
            all_backups[provider_name] = backup_files
        
        return jsonify({
            "providers": providers,
            "backups": all_backups,
            "total_files": sum(len(files) for files in all_backups.values())
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/backup/cleanup", methods=["POST"])
def cleanup_backups():
    """Clean up old backups"""
    if not backup_system:
        return jsonify({"error": "Backup system not initialized"}), 500
    
    try:
        data = request.json if request.is_json else {}
        provider = data.get('provider', 'local')
        keep_count = data.get('keep_count', 10)
        
        result = backup_system.cleanup_old_backups(provider, keep_count)
        
        return jsonify({
            "success": True,
            "message": f"Cleanup completed for {provider}",
            "details": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Health Monitoring Routes

@app.route("/health")
def health_check():
    """Comprehensive health check"""
    try:
        integrity_check = check_data_integrity()
        backup_status = backup_system.get_backup_status() if backup_system else None
        
        # Determine overall health
        is_healthy = (
            not integrity_check['needs_restore'] and
            backup_status and
            backup_status.get('backup_enabled', False)
        )
        
        return jsonify({
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.now(UTC).isoformat(),
            "data_integrity": integrity_check,
            "backup_status": backup_status,
            "last_log_time": last_logged["timestamp"]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "timestamp": datetime.now(UTC).isoformat(),
            "error": str(e)
        }), 500

@app.route("/integrity")
def data_integrity_check():
    """Check data integrity status"""
    try:
        integrity_check = check_data_integrity()
        return jsonify(integrity_check)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/dashboard")
def backup_dashboard():
    """Serve the backup dashboard"""
    try:
        return send_file("backup_dashboard.html")
    except FileNotFoundError:
        return jsonify({"error": "Dashboard not found"}), 404

def run_app():
    """Run the Flask application"""
    port = int(os.getenv('PORT', 10000))
    app.run(host="0.0.0.0", port=port, debug=False)

def main():
    """Main application entry point"""
    logger.info("🚀 Starting Enhanced BTC Logger...")
    
    # Run startup check first
    logger.info("🔍 Running startup integrity check...")
    if not startup_check():
        logger.error("💥 Startup check failed, exiting...")
        sys.exit(1)
    
    # Initialize backup system
    if not initialize_backup_system():
        logger.warning("⚠️ Backup system initialization failed, continuing without backup...")
    
    # Start data logging thread
    logger.info("📊 Starting data logging thread...")
    logging_thread = threading.Thread(target=log_data, daemon=True)
    logging_thread.start()
    
    # Start Flask app
    logger.info("🌐 Starting web server...")
    run_app()

if __name__ == "__main__":
    main()