#!/usr/bin/env python3
"""
CSV Uploader for BTC Data
=========================

This module handles uploading CSV files to Google Cloud Storage.
CSV files are uploaded to the csv/ folder with proper content type and public access.
"""

import os
import glob
from datetime import datetime, timezone
from gcs_uploader import upload_to_gcs
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FOLDER = "render_app/data"

def upload_csv_to_gcs(csv_file_path):
    """
    Upload a CSV file to GCS with proper content type and public access
    
    Args:
        csv_file_path (str): Local path to the CSV file
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        if not os.path.exists(csv_file_path):
            logger.error(f"❌ CSV file not found: {csv_file_path}")
            return False
        
        # Extract date from filename (e.g., "2025-08-07_00.csv" -> "2025-08-07")
        filename = os.path.basename(csv_file_path)
        date_part = filename.split('_')[0]  # Get the date part before underscore
        
        # Create GCS path: csv/YYYY-MM-DD.csv
        gcs_path = f"csv/{date_part}.csv"
        
        # Upload with CSV content type and public access
        success = upload_to_gcs(
            local_path=csv_file_path,
            gcs_path=gcs_path,
            content_type="text/csv",
            public=True
        )
        
        if success:
            logger.info(f"✅ CSV uploaded: {filename} -> {gcs_path}")
        else:
            logger.error(f"❌ Failed to upload CSV: {filename}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ CSV upload error for {csv_file_path}: {e}")
        return False

def upload_all_csvs():
    """
    Upload all CSV files in the data folder to GCS
    
    Returns:
        dict: Summary of upload results
    """
    logger.info("🔄 Starting CSV upload to GCS...")
    
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not csv_files:
        logger.warning("⚠️ No CSV files found to upload")
        return {"uploaded": 0, "failed": 0, "total": 0}
    
    uploaded_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        if upload_csv_to_gcs(csv_file):
            uploaded_count += 1
        else:
            failed_count += 1
    
    logger.info(f"✅ CSV upload complete: {uploaded_count} uploaded, {failed_count} failed")
    return {
        "uploaded": uploaded_count,
        "failed": failed_count,
        "total": len(csv_files)
    }

def upload_recent_csvs(hours_back=24):
    """
    Upload only recent CSV files (within the specified hours)
    
    Args:
        hours_back (int): Number of hours back to consider "recent"
    
    Returns:
        dict: Summary of upload results
    """
    logger.info(f"🔄 Starting recent CSV upload (last {hours_back} hours)...")
    
    # Get current time and calculate cutoff
    now = datetime.now(timezone.utc)
    cutoff = now.replace(hour=now.hour - hours_back, minute=0, second=0, microsecond=0)
    
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not csv_files:
        logger.warning("⚠️ No CSV files found to upload")
        return {"uploaded": 0, "failed": 0, "total": 0}
    
    uploaded_count = 0
    failed_count = 0
    
    for csv_file in csv_files:
        try:
            # Check file modification time
            file_mtime = datetime.fromtimestamp(os.path.getmtime(csv_file), tz=timezone.utc)
            if file_mtime >= cutoff:
                if upload_csv_to_gcs(csv_file):
                    uploaded_count += 1
                else:
                    failed_count += 1
            else:
                logger.info(f"⏭️ Skipping old CSV: {os.path.basename(csv_file)} (modified: {file_mtime})")
        except Exception as e:
            logger.error(f"❌ Error processing {csv_file}: {e}")
            failed_count += 1
    
    logger.info(f"✅ Recent CSV upload complete: {uploaded_count} uploaded, {failed_count} failed")
    return {
        "uploaded": uploaded_count,
        "failed": failed_count,
        "total": len([f for f in csv_files if datetime.fromtimestamp(os.path.getmtime(f), tz=timezone.utc) >= cutoff])
    }