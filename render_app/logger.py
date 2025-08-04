# BTC Logger - Enhanced for Historical Data Support
# Updated: 2025-07-10 - Added hybrid data endpoints and improved debugging
# Updated: 2025-07-10 - Added Google Cloud Storage auto-backup functionality

from flask_cors import CORS
from process_data import process_csv_to_json
from gcs_backup import auto_backup_data, backup_file, get_gcs_backup

# Try to import enhanced backup system
try:
    from enhanced_backup_system import get_backup_system
    from startup_restore import check_data_integrity
    ENHANCED_BACKUP_AVAILABLE = True
except ImportError:
    ENHANCED_BACKUP_AVAILABLE = False
import requests
import csv
import time
import os
from datetime import datetime, UTC
from flask import Flask, jsonify, send_file, send_from_directory, abort
import threading
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

last_logged = {"timestamp": None}

DATA_FOLDER = "render_app/data"
os.makedirs(DATA_FOLDER, exist_ok=True)

# GCS Backup configuration
BACKUP_ENABLED = os.getenv('GCS_BACKUP_ENABLED', 'true').lower() in ['true', '1', 'yes']
BACKUP_INTERVAL_MINUTES = int(os.getenv('BACKUP_INTERVAL_MINUTES', '30'))  # Backup every 30 minutes by default
last_backup_time = {"timestamp": None}

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

            # Run comprehensive JSON generation with full historical context
            process_csv_to_json()
            
            # Check if backup is needed
            check_and_backup_data()

        except Exception as e:
            print("🚨 Error in logger loop:", str(e))

        elapsed = time.time() - start_time
        sleep_time = max(0, 1.0 - elapsed)
        time.sleep(sleep_time)

def check_and_backup_data():
    """Check if backup is needed and perform it"""
    if not BACKUP_ENABLED:
        return
    
    current_time = datetime.now(UTC)
    
    # Check if enough time has passed since last backup
    if last_backup_time["timestamp"] is None:
        should_backup = True
    else:
        time_diff = (current_time - last_backup_time["timestamp"]).total_seconds() / 60
        should_backup = time_diff >= BACKUP_INTERVAL_MINUTES
    
    if should_backup:
        try:
            logger.info(f"🔄 Starting automatic backup...")
            
            # Try enhanced backup first if available
            if ENHANCED_BACKUP_AVAILABLE:
                try:
                    backup_system = get_backup_system()
                    result = backup_system.check_and_backup_if_needed()
                    if result and result.get('success'):
                        last_backup_time["timestamp"] = current_time
                        logger.info(f"✅ Enhanced backup completed: {result.get('total_files', 0)} files uploaded")
                        return
                except Exception as e:
                    logger.warning(f"⚠️ Enhanced backup failed, falling back to GCS: {e}")
            
            # Fallback to original GCS backup
            result = auto_backup_data()
            if result:
                last_backup_time["timestamp"] = current_time
                logger.info(f"✅ GCS backup completed: {result['successful_uploads']} files uploaded")
            else:
                logger.warning("⚠️ Backup failed or not configured")
        except Exception as e:
            logger.error(f"❌ Backup error: {e}")

def manual_backup():
    """Manually trigger a backup"""
    if not BACKUP_ENABLED:
        return {"error": "Backup is disabled"}
    
    try:
        result = auto_backup_data()
        if result:
            last_backup_time["timestamp"] = datetime.now(UTC)
            return {
                "success": True,
                "message": f"Backup completed: {result['successful_uploads']} files uploaded",
                "details": result
            }
        else:
            return {"error": "Backup failed or not configured"}
    except Exception as e:
        return {"error": f"Backup error: {str(e)}"}

# ---- Flask Routes ----

@app.route("/")
def home():
    # Check if enhanced backup is available
    enhanced_backup_status = "Not Available"
    if ENHANCED_BACKUP_AVAILABLE:
        try:
            backup_system = get_backup_system()
            providers = backup_system.get_available_providers()
            enhanced_backup_status = f"Available ({', '.join(providers)})"
        except:
            enhanced_backup_status = "Error"
    
    endpoints = {
        "csv_data": [
            "/data.csv - Current CSV file",
            "/csv-list - List all CSV files",
            "/csv/<filename> - Download specific CSV"
        ],
        "json_data": [
            "/json/output_<YYYY-MM-DD>.json - Daily JSON data",
            "/output-latest.json - Latest daily JSON"
        ],
        "hybrid_chart_data": [
            "/recent.json - Last 24 hours (fast loading, updated every second)",
            "/historical.json - Last 7 days (chart-optimized, updated hourly)",
            "/historical/<YYYY-MM-DD>.json - Archived historical data for specific date",
            "/historical-archives - List all available historical archives",
            "/metadata.json - Dataset metadata",
            "/index.json - Data source index"
        ],
        "filtered_data": [
                "/chart-data?limit=1000 - Limited data points",
                "/chart-data?start_date=2025-01-01 - Date filtered data"
            ],
            "backup_management": [
                "/backup/status - Legacy backup status",
                "/backup/trigger - Legacy manual backup",
                "/backup/list - List legacy backups"
            ] + ([
                "/backup/enhanced/status - Enhanced backup status",
                "/backup/enhanced/trigger - Enhanced manual backup",
                "/backup/enhanced/restore - Manual restore",
                "/backup/enhanced/list - List enhanced backups"
            ] if ENHANCED_BACKUP_AVAILABLE else []),
            "health_monitoring": [
                "/health - System health check"
            ] + (["/dashboard - Backup dashboard"] if ENHANCED_BACKUP_AVAILABLE else [])
        }
    
    return {
        "status": "✅ BTC Logger is running" + (" with Enhanced Backup" if ENHANCED_BACKUP_AVAILABLE else ""),
        "last_log_time": last_logged["timestamp"],
        "description": "TradingView-style BTC-USD data with hybrid loading system and automated backup",
        "enhanced_backup": enhanced_backup_status,
        "endpoints": endpoints,
        "chart_integration": {
            "recommended_approach": "Hybrid loading for TradingView-style performance",
            "fast_startup": "Load /recent.json first (instant chart display)",
            "full_historical": "Load /historical.json for complete data",
            "benefits": [
                "Fast initial chart load (24h recent data)",
                "Full historical data available",
                "No chart resets",
                "Scalable performance",
                "Professional trading platform experience"
            ]
        }
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

@app.route("/recent.json")
def serve_recent_data():
    """Serve last 24 hours of data for fast chart startup"""
    file_path = os.path.join(DATA_FOLDER, "recent.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Recent data not available"}), 404

@app.route("/historical.json")
def serve_historical_data():
    """Serve current day's historical dataset for full TradingView-style charts"""
    file_path = os.path.join(DATA_FOLDER, "historical.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Historical data not available"}), 404

@app.route("/historical/<date>.json")
def serve_historical_archive(date):
    """Serve archived historical data for a specific date (YYYY-MM-DD)"""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    file_path = os.path.join(DATA_FOLDER, f"historical_{date}.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": f"Historical data for {date} not available"}), 404

@app.route("/historical-archives")
def list_historical_archives():
    """List all available historical archive files"""
    try:
        import glob
        pattern = os.path.join(DATA_FOLDER, "historical_*.json")
        archive_files = glob.glob(pattern)
        
        archives = []
        for file_path in sorted(archive_files):
            filename = os.path.basename(file_path)
            # Extract date from filename: historical_YYYY-MM-DD.json
            date_part = filename.replace("historical_", "").replace(".json", "")
            
            file_stats = os.stat(file_path)
            archives.append({
                "date": date_part,
                "filename": filename,
                "url": f"/historical/{date_part}.json",
                "size_bytes": file_stats.st_size,
                "size_mb": round(file_stats.st_size / 1024 / 1024, 2),
                "created": datetime.fromtimestamp(file_stats.st_ctime).isoformat()
            })
        
        return jsonify({
            "current_historical": "/historical.json",
            "archives": archives,
            "archive_count": len(archives)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/metadata.json")
def serve_metadata():
    """Serve metadata about the dataset"""
    file_path = os.path.join(DATA_FOLDER, "metadata.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Metadata not available"}), 404

@app.route("/index.json")
def serve_index():
    """Serve index of available data files"""
    file_path = os.path.join(DATA_FOLDER, "index.json")
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/json')
    else:
        return jsonify({"error": "Index not available"}), 404

@app.route("/chart-data")
def serve_chart_data():
    """Serve optimized data for charting with query parameters"""
    from flask import request
    
    # Check if historical data exists
    historical_path = os.path.join(DATA_FOLDER, "historical.json")
    if not os.path.exists(historical_path):
        return jsonify({"error": "Historical data not available"}), 404
    
    # Get query parameters
    limit = request.args.get('limit', type=int)  # Limit number of records
    start_date = request.args.get('start_date')  # Start date filter
    end_date = request.args.get('end_date')      # End date filter
    
    try:
        import pandas as pd
        df = pd.read_json(historical_path)
        
        # Apply date filters if provided
        if start_date:
            df = df[df['time'] >= start_date]
        if end_date:
            df = df[df['time'] <= end_date]
        
        # Apply limit if provided
        if limit:
            df = df.tail(limit)
        
        # Convert back to JSON
        result = df.to_dict('records')
        
        return jsonify({
            "data": result,
            "count": len(result),
            "filtered": bool(start_date or end_date or limit)
        })
        
    except Exception as e:
        return jsonify({"error": f"Error processing chart data: {str(e)}"}), 500

@app.route("/debug-status")
def debug_status():
    """Debug endpoint to check system status and file timestamps - UPDATED 2025-07-10"""
    try:
        import glob
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_folder": DATA_FOLDER,
            "files": {}
        }
        
        # Check file existence and timestamps
        files_to_check = ["recent.json", "historical.json", "metadata.json", "index.json"]
        
        for filename in files_to_check:
            file_path = os.path.join(DATA_FOLDER, filename)
            if os.path.exists(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                age_hours = (datetime.utcnow() - file_time).total_seconds() / 3600
                file_size = os.path.getsize(file_path)
                
                status["files"][filename] = {
                    "exists": True,
                    "last_modified": file_time.isoformat(),
                    "age_hours": round(age_hours, 2),
                    "size_bytes": file_size
                }
            else:
                status["files"][filename] = {"exists": False}
        
        # Check CSV files
        csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
        status["csv_files"] = []
        for csv_file in sorted(csv_files):
            file_time = datetime.fromtimestamp(os.path.getmtime(csv_file))
            file_size = os.path.getsize(csv_file)
            status["csv_files"].append({
                "name": os.path.basename(csv_file),
                "last_modified": file_time.isoformat(),
                "size_bytes": file_size
            })
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({"error": f"Debug status error: {str(e)}"}), 500

@app.route("/backup", methods=["POST"])
def trigger_backup():
    """Manually trigger a backup to Google Cloud Storage"""
    result = manual_backup()
    if "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result)

@app.route("/backup/status")
def backup_status():
    """Get backup configuration and status"""
    backup = get_gcs_backup()
    
    status = {
        "backup_enabled": BACKUP_ENABLED,
        "backup_interval_minutes": BACKUP_INTERVAL_MINUTES,
        "last_backup_time": last_backup_time["timestamp"].isoformat() if last_backup_time["timestamp"] else None,
        "gcs_configured": backup is not None
    }
    
    if backup:
        try:
            status["bucket_name"] = backup.bucket_name
            status["project_id"] = backup.project_id
        except:
            status["gcs_configured"] = False
    
    return jsonify(status)

@app.route("/backup/list")
def list_backups():
    """List all backup files in Google Cloud Storage"""
    backup = get_gcs_backup()
    if not backup:
        return jsonify({"error": "GCS backup not configured"}), 500
    
    try:
        backups = backup.list_backups()
        return jsonify({
            "backups": backups,
            "count": len(backups)
        })
    except Exception as e:
        return jsonify({"error": f"Failed to list backups: {str(e)}"}), 500

# ---- Enhanced Backup Routes ----

if ENHANCED_BACKUP_AVAILABLE:
    @app.route("/backup/enhanced/status")
    def enhanced_backup_status():
        """Get enhanced backup system status"""
        try:
            backup_system = get_backup_system()
            status = backup_system.get_backup_status()
            integrity_check = check_data_integrity()
            
            return jsonify({
                "enhanced_backup": True,
                "backup_system": status,
                "data_integrity": integrity_check,
                "available_providers": backup_system.get_available_providers()
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/backup/enhanced/trigger", methods=["POST"])
    def enhanced_trigger_backup():
        """Manually trigger enhanced backup"""
        try:
            from flask import request
            backup_system = get_backup_system()
            providers = request.json.get('providers', None) if request.is_json else None
            result = backup_system.backup_all_data(providers)
            
            if result.get('success'):
                return jsonify({
                    "success": True,
                    "message": "Enhanced backup completed successfully",
                    "details": result
                })
            else:
                return jsonify({
                    "success": False,
                    "message": result.get('error', 'Enhanced backup failed'),
                    "details": result
                }), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/backup/enhanced/restore", methods=["POST"])
    def enhanced_restore_backup():
        """Manually restore from enhanced backup"""
        try:
            from flask import request
            backup_system = get_backup_system()
            data = request.json if request.is_json else {}
            provider = data.get('provider', None)
            target_folder = data.get('target_folder', None)
            
            result = backup_system.restore_latest_backup(provider, target_folder)
            
            if result.get('success'):
                return jsonify({
                    "success": True,
                    "message": "Enhanced restore completed successfully",
                    "details": result
                })
            else:
                return jsonify({
                    "success": False,
                    "message": result.get('error', 'Enhanced restore failed'),
                    "details": result
                }), 500
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/backup/enhanced/list")
    def enhanced_list_backups():
        """List all enhanced backup files"""
        try:
            backup_system = get_backup_system()
            providers = backup_system.get_available_providers()
            all_backups = {}
            
            for provider_name in providers:
                provider = backup_system.providers[provider_name]
                backup_files = provider.list_files("btc-data/")
                all_backups[provider_name] = backup_files
            
            return jsonify({
                "enhanced_backup": True,
                "providers": providers,
                "backups": all_backups,
                "total_files": sum(len(files) for files in all_backups.values())
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route("/health")
def health_check():
    """Comprehensive health check"""
    try:
        # Basic health info
        health_info = {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "last_log_time": last_logged["timestamp"],
            "backup_enabled": BACKUP_ENABLED
        }
        
        # Add enhanced backup info if available
        if ENHANCED_BACKUP_AVAILABLE:
            try:
                integrity_check = check_data_integrity()
                backup_system = get_backup_system()
                backup_status = backup_system.get_backup_status()
                
                # Determine overall health
                is_healthy = (
                    not integrity_check['needs_restore'] and
                    backup_status and
                    backup_status.get('backup_enabled', False)
                )
                
                health_info.update({
                    "enhanced_backup": True,
                    "status": "healthy" if is_healthy else "degraded",
                    "data_integrity": integrity_check,
                    "backup_status": backup_status
                })
            except Exception as e:
                health_info.update({
                    "enhanced_backup": False,
                    "enhanced_backup_error": str(e)
                })
        
        return jsonify(health_info)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "timestamp": datetime.now(UTC).isoformat(),
            "error": str(e)
        }), 500

@app.route("/dashboard")
def backup_dashboard():
    """Serve the backup dashboard"""
    try:
        return send_file("backup_dashboard.html")
    except FileNotFoundError:
        return jsonify({
            "error": "Dashboard not found", 
            "message": "backup_dashboard.html file is missing"
        }), 404

# ---- App Runner ----

def run_app():
    app.run(host="0.0.0.0", port=10000)

# Start logger and web server
if __name__ == "__main__":
    threading.Thread(target=log_data, daemon=True).start()
    run_app()
