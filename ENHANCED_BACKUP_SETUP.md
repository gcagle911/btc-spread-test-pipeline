# 🔒 Enhanced Backup System for BTC Logger

## Overview

This enhanced backup system provides robust data protection for your BTC logger application running on Render. It includes multiple backup providers, automatic crash recovery, real-time monitoring, and a user-friendly dashboard.

## 🌟 Key Features

- **Multiple Backup Providers**: Local filesystem and Google Cloud Storage
- **Automatic Crash Recovery**: Detects data loss and restores automatically on startup
- **Real-time Monitoring**: Health checks and integrity verification
- **Interactive Dashboard**: Web-based interface for backup management
- **Critical Event Backup**: Immediate backup on errors or crashes
- **Scheduled Backups**: Configurable automatic backup intervals
- **Clean Restore Interface**: Simple API endpoints for data restoration

## 🚀 Quick Setup

### 1. Update Your Application

Replace your current startup file with the enhanced version:

```bash
# In your render_app directory
mv start_server.py start_server_original.py
cp enhanced_logger.py start_server.py
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Add these to your Render environment variables or `.env` file:

```bash
# Backup Configuration
BACKUP_ENABLED=true
BACKUP_INTERVAL_MINUTES=30
AUTO_RESTORE_ON_STARTUP=true
MAX_LOCAL_BACKUPS=10

# Google Cloud Storage (Optional)
GCS_BUCKET_NAME=your-btc-data-bucket
GCP_PROJECT_ID=your-gcp-project
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

### 4. Set Up Google Cloud Storage (Recommended)

1. **Create GCP Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing one

2. **Enable APIs**:
   ```bash
   gcloud services enable storage.googleapis.com
   ```

3. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create btc-logger-backup \
     --display-name="BTC Logger Backup Service"
   ```

4. **Grant Permissions**:
   ```bash
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:btc-logger-backup@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   ```

5. **Create and Download Key**:
   ```bash
   gcloud iam service-accounts keys create service-account.json \
     --iam-account=btc-logger-backup@YOUR_PROJECT_ID.iam.gserviceaccount.com
   ```

6. **Create Bucket**:
   ```bash
   gsutil mb gs://your-btc-data-bucket
   ```

### 5. Test the Setup

```bash
# Run the setup test
python startup_restore.py

# Start the enhanced logger
python enhanced_logger.py
```

## 📊 Using the Backup Dashboard

Access the backup dashboard at: `http://your-render-url/dashboard` (you'll need to add this route)

Or use the backup management endpoints:

- `GET /health` - System health check
- `GET /backup/status` - Backup system status
- `POST /backup/trigger` - Manual backup trigger
- `POST /backup/restore` - Manual restore
- `GET /backup/list` - List all backups
- `POST /backup/cleanup` - Clean old backups

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_ENABLED` | `true` | Enable/disable backup system |
| `BACKUP_INTERVAL_MINUTES` | `30` | Automatic backup interval |
| `AUTO_RESTORE_ON_STARTUP` | `true` | Auto-restore on startup |
| `MAX_LOCAL_BACKUPS` | `10` | Max local backups to keep |
| `GCS_BUCKET_NAME` | - | Google Cloud Storage bucket |
| `GCP_PROJECT_ID` | - | Google Cloud Project ID |

### Backup Providers

The system supports multiple backup providers:

1. **Local Backup** (always available):
   - Stores backups in `/tmp/btc_backup`
   - Good for temporary protection
   - Limited by disk space

2. **Google Cloud Storage** (recommended):
   - Cloud-based storage
   - Survives server crashes
   - Scalable and reliable

## 🔄 How It Works

### Automatic Backup Process

1. **Scheduled Backups**: Every 30 minutes (configurable)
2. **Critical Event Backups**: On consecutive errors or crashes
3. **File Detection**: Automatically finds `*.csv` and `*.json` files
4. **Multi-Provider**: Uploads to all available providers
5. **Metadata**: Includes timestamps and file information

### Crash Recovery Process

1. **Startup Check**: Verifies data integrity on application start
2. **Missing Data Detection**: Checks for recent files (within 2 hours)
3. **Automatic Restore**: Downloads latest backup if needed
4. **Verification**: Confirms restoration was successful
5. **Logging**: Detailed logs of all recovery operations

### Data Integrity Monitoring

- **File Freshness**: Checks for recent data files
- **File Existence**: Verifies critical files are present
- **Health Status**: Reports overall system health
- **API Endpoints**: Programmatic access to status

## 🚨 Troubleshooting

### Common Issues

1. **GCS Authentication Failed**:
   ```bash
   # Check service account file exists
   ls -la path/to/service-account.json
   
   # Test authentication
   gcloud auth activate-service-account --key-file=service-account.json
   ```

2. **Backup Not Running**:
   - Check `BACKUP_ENABLED=true`
   - Verify backup interval setting
   - Check application logs for errors

3. **Restore Failed**:
   - Verify backup files exist: `GET /backup/list`
   - Check provider availability
   - Review error logs

4. **Permission Denied**:
   - Ensure service account has Storage Admin role
   - Check bucket permissions
   - Verify project ID is correct

### Debug Commands

```bash
# Test backup manually
curl -X POST http://localhost:10000/backup/trigger

# Check backup status
curl http://localhost:10000/backup/status

# List available backups
curl http://localhost:10000/backup/list

# Test restore
curl -X POST http://localhost:10000/backup/restore
```

## 📈 Monitoring and Alerts

### Health Check Endpoint

```bash
curl http://localhost:10000/health
```

Response includes:
- Overall system health
- Data integrity status
- Backup system status
- Last log timestamp

### Setting Up Monitoring

You can use external monitoring services to check the health endpoint:

```bash
# Example: Check if system is healthy
if curl -s http://your-app/health | grep -q '"status":"healthy"'; then
  echo "System is healthy"
else
  echo "System needs attention"
fi
```

## 🔒 Security Considerations

1. **Service Account Keys**:
   - Never commit to version control
   - Use environment variables in production
   - Rotate keys regularly

2. **Bucket Security**:
   - Use IAM policies for access control
   - Enable audit logging
   - Consider bucket versioning

3. **Network Security**:
   - Use HTTPS for all API calls
   - Implement authentication if needed
   - Monitor access logs

## 📊 Performance Optimization

### Backup Optimization

1. **Backup Interval**: Adjust based on data importance
2. **File Filtering**: Only backup critical files
3. **Compression**: Consider compressing large files
4. **Cleanup**: Regular cleanup of old backups

### Storage Costs

1. **GCS Storage Classes**:
   - Standard: Frequent access
   - Nearline: Monthly access
   - Coldline: Quarterly access

2. **Lifecycle Policies**:
   ```json
   {
     "rule": [{
       "condition": {"age": 30},
       "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"}
     }]
   }
   ```

## 🎯 Best Practices

1. **Regular Testing**:
   - Test restore process monthly
   - Verify backup integrity
   - Monitor system health

2. **Multiple Providers**:
   - Use both local and cloud backups
   - Consider additional cloud providers
   - Test cross-provider restore

3. **Documentation**:
   - Document recovery procedures
   - Keep configuration updated
   - Train team on backup system

4. **Monitoring**:
   - Set up alerts for backup failures
   - Monitor storage usage
   - Track restore times

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review application logs
3. Test individual components
4. Use the debug endpoints
5. Check GCP service status

## 🔄 Migration from Old System

If upgrading from the original backup system:

1. **Backup Current Data**: Manual backup before migration
2. **Update Code**: Replace with enhanced versions
3. **Test Thoroughly**: Verify all functionality
4. **Monitor**: Watch for any issues during transition

Your data is now protected with enterprise-grade backup and recovery capabilities! 🎉