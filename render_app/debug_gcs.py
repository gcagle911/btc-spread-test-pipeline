#!/usr/bin/env python3
"""
Debug GCS Connection
Simple script to test what's wrong with Google Cloud Storage
"""

import os
import json

def check_environment():
    """Check if environment variables are set correctly"""
    print("🔍 Checking Environment Variables...")
    
    # Check required variables
    bucket = os.getenv('GCS_BUCKET_NAME')
    project = os.getenv('GCP_PROJECT_ID')
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    creds_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    print(f"GCS_BUCKET_NAME: {bucket}")
    print(f"GCP_PROJECT_ID: {project}")
    print(f"GOOGLE_APPLICATION_CREDENTIALS_JSON: {'Set' if creds_json else 'Not set'}")
    print(f"GOOGLE_APPLICATION_CREDENTIALS: {creds_file}")
    
    if not bucket:
        print("❌ GCS_BUCKET_NAME is missing!")
        return False
    
    if not project:
        print("❌ GCP_PROJECT_ID is missing!")
        return False
    
    if not creds_json and not creds_file:
        print("❌ No credentials found!")
        return False
    
    # Test JSON parsing if using JSON credentials
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            print(f"✅ JSON credentials parsed successfully")
            print(f"   Service account email: {creds_dict.get('client_email', 'Not found')}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON credentials are malformed: {e}")
            return False
    
    return True

def test_gcs_connection():
    """Test actual connection to GCS"""
    print("\n🌐 Testing GCS Connection...")
    
    try:
        from google.cloud import storage
        from google.oauth2 import service_account
        
        # Get credentials
        creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
        bucket_name = os.getenv('GCS_BUCKET_NAME')
        project_id = os.getenv('GCP_PROJECT_ID')
        
        if creds_json:
            creds_dict = json.loads(creds_json)
            credentials = service_account.Credentials.from_service_account_info(creds_dict)
            client = storage.Client(credentials=credentials, project=project_id)
        else:
            client = storage.Client(project=project_id)
        
        # Test bucket access
        bucket = client.bucket(bucket_name)
        
        # Try to list files (this tests permissions)
        blobs = list(client.list_blobs(bucket, max_results=1))
        print(f"✅ Successfully connected to bucket: {bucket_name}")
        print(f"   Found {len(blobs)} files in bucket")
        
        return True
        
    except Exception as e:
        print(f"❌ GCS connection failed: {e}")
        return False

def main():
    print("=" * 50)
    print("🔧 GCS Debug Tool")
    print("=" * 50)
    
    # Step 1: Check environment
    env_ok = check_environment()
    
    if not env_ok:
        print("\n❌ Environment variables need to be fixed first")
        print("\n🔧 Fix these issues:")
        print("1. Go to Render → Your Service → Environment")
        print("2. Add missing variables")
        print("3. Make sure JSON is valid (starts with { ends with })")
        return
    
    # Step 2: Test connection
    conn_ok = test_gcs_connection()
    
    if conn_ok:
        print("\n🎉 GCS is working correctly!")
        print("The error might be elsewhere. Check your app logs.")
    else:
        print("\n❌ GCS connection failed")
        print("\n🔧 Common fixes:")
        print("1. Re-download service account JSON")
        print("2. Check bucket name is correct and exists")
        print("3. Verify service account has Storage Admin role")

if __name__ == "__main__":
    main()