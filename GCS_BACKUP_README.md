# 🌟 Google Cloud Storage Backup for BTC Historical Data

This guide helps you set up automatic backup of your BTC historical data to Google Cloud Storage (GCS). All your CSV files, JSON outputs, and metadata will be automatically saved to the cloud for safekeeping and easy access.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd render_app
pip install -r requirements.txt
```

### 2. Run the Setup Script
```bash
python3 setup_gcs.py
```
The setup script will guide you through:
- Creating a Google Cloud service account
- Setting up a GCS bucket
- Configuring authentication
- Testing the backup system

### 3. Start Your Logger
```bash
python3 logger.py
```
That's it! Your data will now automatically backup to Google Cloud Storage every 30 minutes.

## 📋 Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Create Google Cloud Project & Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Cloud Storage API
4. Go to IAM & Admin > Service Accounts
5. Create a new service account with "Storage Admin" role
6. Download the JSON key file

### 2. Create GCS Bucket

```bash
# Using gcloud CLI
gsutil mb gs://your-btc-data-bucket

# Or create via Web Console
```

### 3. Configure Environment

Create a `.env` file in the `render_app` directory:

```bash
# Required: Your GCS bucket name
GCS_BUCKET_NAME=your-btc-data-bucket

# Required: Path to service account JSON key file
GOOGLE_APPLICATION_CREDENTIALS=./gcs-service-account.json

# Optional: GCP Project ID
GCP_PROJECT_ID=your-project-id

# Optional: Enable/disable backup (default: true)
GCS_BACKUP_ENABLED=true

# Optional: Backup interval in minutes (default: 30)
BACKUP_INTERVAL_MINUTES=30
```

## 🔄 How It Works

### Automatic Backups
- **Frequency**: Every 30 minutes (configurable)
- **Trigger**: Automatic during data logging
- **Files**: All CSV and JSON files in the data folder
- **Organization**: Files are organized by date and type in GCS

### Backup Structure in GCS
```
gs://your-bucket/btc-data/
├── 2025-01-15/14/
│   ├── csv/
│   │   ├── 2025-01-15_08.csv
│   │   └── 2025-01-15_16.csv
│   ├── json/
│   │   ├── historical.json
│   │   ├── metadata.json
│   │   └── output_2025-01-15.json
│   └── backup-summary.json
└── 2025-01-16/02/
    └── ...
```

### What Gets Backed Up
- **CSV Files**: Raw orderbook data (rotated every 8 hours)
- **JSON Files**: Processed historical data, metadata, and indices
- **Metadata**: File timestamps, sizes, and processing information
- **Summaries**: Backup logs and success/failure reports

## 🛠️ API Endpoints

Your Flask application now includes backup management endpoints:

### Check Backup Status
```bash
curl http://localhost:10000/backup/status
```
Returns backup configuration and last backup time.

### Manual Backup
```bash
curl -X POST http://localhost:10000/backup
```
Immediately triggers a backup of all data files.

### List Backups
```bash
curl http://localhost:10000/backup/list
```
Lists all backup files stored in Google Cloud Storage.

## ⚙️ Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GCS_BUCKET_NAME` | None | **Required**: Your GCS bucket name |
| `GOOGLE_APPLICATION_CREDENTIALS` | None | **Required**: Path to service account JSON |
| `GCP_PROJECT_ID` | Auto-detect | GCP project ID |
| `GCS_BACKUP_ENABLED` | `true` | Enable/disable automatic backup |
| `BACKUP_INTERVAL_MINUTES` | `30` | Minutes between automatic backups |

### Backup Frequency Options

```bash
# Backup every 5 minutes (for testing)
BACKUP_INTERVAL_MINUTES=5

# Backup every hour
BACKUP_INTERVAL_MINUTES=60

# Backup every 6 hours
BACKUP_INTERVAL_MINUTES=360

# Disable automatic backup
GCS_BACKUP_ENABLED=false
```

## 📊 Monitoring & Logs

### Application Logs
The backup system logs all activities:
```
✅ GCS client initialized for bucket: btc-data-backup
🔄 Starting automatic backup...
✅ Uploaded: render_app/data/historical.json → gs://btc-data-backup/btc-data/2025-01-15/14/json/historical.json
📊 Backup complete: 5 successful, 0 failed
```

### Backup Summary Files
Each backup creates a summary file with details:
```json
{
  "backup_timestamp": "2025-01-15T14:30:00.123456Z",
  "total_files": 5,
  "successful_uploads": 5,
  "failed_uploads": 0,
  "uploaded_files": [
    "render_app/data/historical.json",
    "render_app/data/metadata.json"
  ]
}
```

## 🔒 Security Best Practices

### 1. Secure Your Service Account Key
```bash
# Set proper permissions
chmod 600 gcs-service-account.json

# Add to .gitignore
echo "*.json" >> .gitignore
echo ".env" >> .gitignore
```

### 2. Use Least Privilege
Your service account only needs:
- `Storage Object Creator` (to upload files)
- `Storage Object Viewer` (to list files)

### 3. Bucket Security
Consider setting up:
- Bucket-level IAM policies
- Object lifecycle rules
- Regional restrictions

## 💰 Cost Optimization

### Storage Classes
For cost optimization, consider GCS storage classes:

```bash
# Set bucket default to Nearline (cheaper for infrequent access)
gsutil defstorageclass set NEARLINE gs://your-bucket

# Or use Coldline for archival
gsutil defstorageclass set COLDLINE gs://your-bucket
```

### Lifecycle Rules
Set up automatic deletion of old backups:
```bash
# Delete files older than 90 days
gsutil lifecycle set lifecycle.json gs://your-bucket
```

Example `lifecycle.json`:
```json
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 90}
  }]
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
❌ Failed to initialize GCS client: Could not automatically determine credentials
```
**Solution**: Check your service account key path and permissions.

#### 2. Bucket Access Denied
```
❌ Upload failed: 403 Forbidden
```
**Solution**: Verify your service account has Storage Admin role.

#### 3. Bucket Not Found
```
❌ Upload failed: 404 Not Found
```
**Solution**: Check bucket name spelling and ensure it exists.

### Debug Commands

```bash
# Test GCS connection
python3 -c "from gcs_backup import get_gcs_backup; print(get_gcs_backup())"

# Check environment variables
python3 -c "import os; print(os.getenv('GCS_BUCKET_NAME'))"

# Manual test upload
python3 -c "from gcs_backup import backup_file; backup_file('render_app/data/metadata.json')"
```

### Enable Debug Logging

Add to your `.env` file:
```bash
PYTHONPATH=.
GOOGLE_CLOUD_DISABLE_GRPC=true  # If having gRPC issues
```

## 📈 Usage Examples

### Programmatic Access
```python
from gcs_backup import GCSBackup

# Initialize backup client
backup = GCSBackup()

# Backup specific file
backup.upload_file('data/important.csv', 'archive/important.csv')

# Backup entire data folder
result = backup.backup_data_folder()
print(f"Uploaded {result['successful_uploads']} files")

# List all backups
backups = backup.list_backups()
for backup_file in backups:
    print(f"{backup_file['name']} - {backup_file['size']} bytes")

# Download a backup
backup.download_backup('btc-data/2025-01-15/14/json/historical.json', 'restored.json')
```

### Restore Data
```bash
# Download specific backup
gsutil cp gs://your-bucket/btc-data/2025-01-15/14/json/historical.json ./restored_historical.json

# Download entire day's backup
gsutil -m cp -r gs://your-bucket/btc-data/2025-01-15/ ./restore/
```

## 🎯 Integration with Existing Systems

### Cron Jobs
For additional backup security, set up cron jobs:
```bash
# Backup every hour as additional safety
0 * * * * cd /path/to/render_app && python3 -c "from gcs_backup import auto_backup_data; auto_backup_data()"

# Daily backup verification
0 6 * * * cd /path/to/render_app && python3 -c "from gcs_backup import get_gcs_backup; print(len(get_gcs_backup().list_backups()))"
```

### Monitoring Alerts
Set up Google Cloud Monitoring alerts for:
- Backup failures
- Missing daily backups
- Storage quota warnings

### Other Cloud Providers
The backup system can be extended for other cloud providers:
- AWS S3 (boto3)
- Azure Blob Storage (azure-storage-blob)
- Dropbox API

## 🔄 Migration & Recovery

### Disaster Recovery Plan

1. **Set up new environment**:
   ```bash
   git clone your-repo
   cd render_app
   pip install -r requirements.txt
   ```

2. **Restore configuration**:
   ```bash
   # Download your service account key
   # Create .env file with your settings
   ```

3. **Restore latest data**:
   ```bash
   # Download latest backups
   gsutil -m cp -r gs://your-bucket/btc-data/$(date +%Y-%m-%d)/ ./render_app/data/
   ```

4. **Restart services**:
   ```bash
   python3 logger.py
   ```

### Backup Verification
Regularly verify your backups:
```python
from gcs_backup import get_gcs_backup
import json

backup = get_gcs_backup()
backups = backup.list_backups()

# Check for recent backups
recent_backups = [b for b in backups if 'json' in b['name']]
print(f"Found {len(recent_backups)} JSON backups")

# Verify backup integrity
for backup_file in recent_backups[:5]:  # Check last 5
    # Download and verify the file can be loaded
    local_path = f"verify_{backup_file['name'].split('/')[-1]}"
    if backup.download_backup(backup_file['name'], local_path):
        try:
            with open(local_path, 'r') as f:
                json.load(f)  # Verify JSON is valid
            print(f"✅ {backup_file['name']} is valid")
        except:
            print(f"❌ {backup_file['name']} is corrupted")
        os.remove(local_path)
```

## 🤝 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Test your GCS connection manually
4. Verify your service account permissions

Your BTC historical data is now safely backed up to Google Cloud Storage! 🎉