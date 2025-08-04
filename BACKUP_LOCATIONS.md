# 📁 Backup Storage Locations

## Where Your Data Gets Backed Up

### 🏠 **Local Development (Your Computer)**
```
~/btc_backup/
└── btc-data/
    └── 2025-01-15/14-30/
        ├── 2025-01-15_08.csv
        ├── historical.json
        ├── recent.json
        ├── metadata.json
        └── backup-summary.json
```
- **Location**: `~/btc_backup/` (your home directory)
- **Persistence**: Survives app restarts
- **Space**: Limited by your disk space

### ☁️ **Render Deployment**
```
./backup_data/
└── btc-data/
    └── 2025-01-15/14-30/
        ├── 2025-01-15_08.csv
        ├── historical.json
        ├── recent.json
        ├── metadata.json
        └── backup-summary.json
```
- **Location**: `./backup_data/` (in your app directory)
- **Persistence**: Survives app crashes and restarts during deployment
- **⚠️ Limitation**: Gets wiped when Render redeploys your service
- **Space**: Limited by Render's disk allocation

### 🌐 **Google Cloud Storage (Recommended for Production)**
```
gs://your-bucket-name/
└── btc-data/
    └── 2025-01-15/14-30/
        ├── 2025-01-15_08.csv
        ├── historical.json
        ├── recent.json
        ├── metadata.json
        └── backup-summary.json
```
- **Location**: Your Google Cloud Storage bucket
- **Persistence**: Survives everything (crashes, restarts, redeploys)
- **Space**: Virtually unlimited (pay per GB)
- **Access**: Available from anywhere, any time

## 🔧 **Customizing Backup Locations**

### Environment Variable
Set `LOCAL_BACKUP_DIR` to customize the local backup location:
```bash
export LOCAL_BACKUP_DIR="/path/to/your/backup/folder"
```

### In your .env file
```bash
LOCAL_BACKUP_DIR=./my_custom_backup_folder
```

## 🛡️ **Protection Levels**

| Scenario | Local Backup | Google Cloud |
|----------|-------------|--------------|
| App crash | ✅ Protected | ✅ Protected |
| Server restart | ✅ Protected | ✅ Protected |
| Render redeploy | ❌ Lost | ✅ Protected |
| Account issues | ❌ Lost | ✅ Protected |
| Complete disaster | ❌ Lost | ✅ Protected |

## 🎯 **Recommendations**

### For Development
- Local backup is sufficient
- Quick setup with `python quick_setup.py`

### For Production on Render
- **Essential**: Set up Google Cloud Storage
- Local backup provides crash protection
- Cloud backup provides disaster recovery

### Setup Priority
1. **Start with local backup** (works immediately)
2. **Add Google Cloud Storage** (for production safety)
3. **Monitor via dashboard** (`/dashboard`)

## 📊 **Checking Your Backups**

### Via Dashboard
Visit: `http://your-app-url/dashboard`

### Via API
```bash
# Check backup status
curl http://your-app-url/backup/enhanced/status

# List all backups
curl http://your-app-url/backup/enhanced/list

# System health
curl http://your-app-url/health
```

### Via File System
```bash
# Local backups
ls -la ~/btc_backup/btc-data/
# or on Render:
ls -la ./backup_data/btc-data/
```

Your data is automatically backed up every 30 minutes to all configured locations! 🔒