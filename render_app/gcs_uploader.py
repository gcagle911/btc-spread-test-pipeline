#!/usr/bin/env python3
"""
Google Cloud Storage Uploader for BTC Chart Data
================================================

This module provides a simple function to upload JSON files to Google Cloud Storage.
It uses environment variables for authentication and configuration.
"""

import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_to_gcs(local_path, gcs_path, bucket_name="garrettc-btc-bidspreadl20-data"):
    """
    Upload a file to Google Cloud Storage
    
    Args:
        local_path (str): Local file path to upload
        gcs_path (str): GCS destination path (e.g., "recent.json", "archive/1min/2025-08-07.json")
        bucket_name (str): GCS bucket name (default: "garrettc-btc-bidspreadl20-data")
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(local_path):
            logger.error(f"❌ File not found: {local_path}")
            return False
        
        # Get credentials from environment variable
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not credentials_json:
            logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")
            return False
        
        # Parse credentials JSON
        try:
            credentials_info = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
            return False
        
        # Create credentials object
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Initialize GCS client
        client = storage.Client(credentials=credentials)
        bucket = client.bucket(bucket_name)
        
        # Create blob and upload
        blob = bucket.blob(gcs_path)
        
        # Upload file in binary mode
        with open(local_path, 'rb') as f:
            blob.upload_from_file(f)
        
        logger.info(f"✅ Uploaded {local_path} to gs://{bucket_name}/{gcs_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Upload failed for {local_path}: {e}")
        return False