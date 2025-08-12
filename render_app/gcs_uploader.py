#!/usr/bin/env python3
"""
Google Cloud Storage Uploader for BTC Chart Data
================================================

This module provides simple functions to upload and download JSON and CSV files to/from Google Cloud Storage.
It uses environment variables for authentication and configuration.
"""

import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import logging
import mimetypes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_gcs_client():
    """
    Get GCS client with proper authentication
    
    Returns:
        tuple: (client, bucket) or (None, None) if authentication fails
    """
    try:
        # Get credentials from environment variable
        credentials_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        if not credentials_json:
            logger.error("❌ GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable not set")
            return None, None
        
        # Parse credentials JSON
        try:
            credentials_info = json.loads(credentials_json)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
            return None, None
        
        # Create credentials object
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        
        # Initialize GCS client
        client = storage.Client(credentials=credentials)
        bucket = client.bucket("garrettc-btc-bidspreadl20-data")
        
        return client, bucket
        
    except Exception as e:
        logger.error(f"❌ GCS client initialization failed: {e}")
        return None, None

def upload_to_gcs(local_path, gcs_path, bucket_name="garrettc-btc-bidspreadl20-data", content_type=None, public=False):
    """
    Upload a file to Google Cloud Storage
    
    Args:
        local_path (str): Local file path to upload
        gcs_path (str): GCS destination path (e.g., "recent.json", "csv/2025-08-07.csv")
        bucket_name (str): GCS bucket name (default: "garrettc-btc-bidspreadl20-data")
        content_type (str): Content type for the file (e.g., "text/csv", "application/json")
        public (bool): Whether to make the file publicly readable (default: False) - IGNORED for uniform bucket access
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    try:
        # Check if file exists
        if not os.path.exists(local_path):
            logger.error(f"❌ File not found: {local_path}")
            return False
        
        # Get GCS client
        client, bucket = get_gcs_client()
        if not client or not bucket:
            return False
        
        # Create blob
        blob = bucket.blob(gcs_path)
        
        # Infer content type if not provided
        if not content_type:
            guessed_type, _ = mimetypes.guess_type(local_path)
            content_type = guessed_type or "application/octet-stream"
            # Override for common types if needed
            if local_path.lower().endswith(".json"):
                content_type = "application/json"
            elif local_path.lower().endswith(".csv"):
                content_type = "text/csv"
        
        # Set metadata to reduce caching issues in browsers/console
        blob.cache_control = "no-cache, max-age=0"
        blob.content_type = content_type
        
        # Upload file and explicitly pass content_type
        with open(local_path, 'rb') as f:
            blob.upload_from_file(f, content_type=content_type)
        
        logger.info(f"✅ Uploaded {local_path} to gs://{bucket_name}/{gcs_path} (Content-Type: {content_type})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Upload failed for {local_path}: {e}")
        return False

def download_from_gcs(gcs_path, local_path, bucket_name="garrettc-btc-bidspreadl20-data"):
    """
    Download a file from Google Cloud Storage
    
    Args:
        gcs_path (str): GCS source path (e.g., "archive/1min/2025-08-07.json")
        local_path (str): Local destination path
        bucket_name (str): GCS bucket name (default: "garrettc-btc-bidspreadl20-data")
    
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        # Get GCS client
        client, bucket = get_gcs_client()
        if not client or not bucket:
            return False
        
        # Create blob and download
        blob = bucket.blob(gcs_path)
        
        # Check if blob exists
        if not blob.exists():
            logger.info(f"ℹ️ File not found in GCS: gs://{bucket_name}/{gcs_path}")
            return False
        
        # Ensure local directory exists
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Download file
        blob.download_to_filename(local_path)
        
        logger.info(f"✅ Downloaded gs://{bucket_name}/{gcs_path} to {local_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Download failed for gs://{bucket_name}/{gcs_path}: {e}")
        return False