# 🚀 Quick Start: Google Cloud Storage Backup

## Setup in 3 Easy Steps

### 1. Install Dependencies
```bash
cd render_app
pip install google-cloud-storage
```

### 2. Run Setup Script
```bash
python3 setup_gcs.py
```
This interactive script will:
- Guide you through creating a Google Cloud service account
- Help you set up a GCS bucket
- Configure authentication
- Test the backup system

### 3. Start Your Logger
```bash
python3 logger.py
```

**That's it!** Your BTC data will now automatically backup to Google Cloud Storage every 30 minutes.

## Verify Everything Works

```bash
# Test your configuration
python3 test_backup.py

# Check backup status via API
curl http://localhost:10000/backup/status

# Manually trigger a backup
curl -X POST http://localhost:10000/backup

# List all your backups
curl http://localhost:10000/backup/list
```

## What Gets Backed Up

- **CSV files**: Raw Bitcoin orderbook data
- **JSON files**: Processed historical data with moving averages
- **Metadata**: Information about your dataset
- **Backup summaries**: Logs of each backup operation

## Backup Structure in Google Cloud

```
gs://your-bucket/btc-data/
├── 2025-01-15/14/           # Date/Hour organization
│   ├── csv/
│   │   ├── 2025-01-15_08.csv
│   │   └── 2025-01-15_16.csv
│   ├── json/
│   │   ├── historical.json   # Complete dataset
│   │   ├── metadata.json     # Dataset info
│   │   └── recent.json       # Last 24 hours
│   └── backup-summary.json   # Backup log
└── 2025-01-16/02/
    └── ...
```

## Configuration Options

Edit your `.env` file to customize:

```bash
# How often to backup (in minutes)
BACKUP_INTERVAL_MINUTES=30

# Enable/disable automatic backup
GCS_BACKUP_ENABLED=true

# Your bucket name
GCS_BUCKET_NAME=your-btc-data-bucket
```

## API Endpoints

Your Flask app now includes backup endpoints:

- `GET /backup/status` - Check backup configuration
- `POST /backup` - Manually trigger backup
- `GET /backup/list` - List all backup files

## Troubleshooting

If something doesn't work:

1. **Run the test script**: `python3 test_backup.py`
2. **Check your credentials**: Make sure your service account JSON is in the right place
3. **Verify permissions**: Your service account needs "Storage Admin" role
4. **Check the logs**: Look for error messages in the terminal

## Security Notes

- Your service account key file is protected by `.gitignore`
- Never commit `.env` or `*.json` files to version control
- Consider using IAM roles instead of keys in production

## Need Help?

Check the full documentation in `GCS_BACKUP_README.md` for:
- Detailed setup instructions
- Advanced configuration options
- Cost optimization tips
- Disaster recovery procedures

Your Bitcoin data is now safely backed up to the cloud! 🎉