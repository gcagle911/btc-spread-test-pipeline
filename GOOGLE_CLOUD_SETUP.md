# ☁️ Google Cloud Storage Setup Guide

## Why You Need This
- **Survives code deployments** - Your data persists when you push new commits
- **Survives Render redeploys** - Charts keep working without interruption
- **Disaster recovery** - Data is safe even if Render has issues
- **Multiple environments** - Same data accessible from dev/staging/prod

## 🚀 Quick Setup (15 minutes)

### Step 1: Create Google Cloud Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign up for free account (gets $300 credit)
3. Create a new project or select existing one

### Step 2: Enable Cloud Storage API
```bash
# Option A: Via web console
# Go to APIs & Services > Library > Search "Cloud Storage API" > Enable

# Option B: Via command line (if you have gcloud installed)
gcloud services enable storage.googleapis.com
```

### Step 3: Create Storage Bucket
1. Go to [Cloud Storage](https://console.cloud.google.com/storage)
2. Click "Create Bucket"
3. **Bucket name**: `your-username-btc-data` (must be globally unique)
4. **Location**: Choose region close to Render (US-Central1 recommended)
5. **Storage class**: Standard
6. **Access control**: Uniform
7. Click "Create"

### Step 4: Create Service Account
1. Go to [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. **Name**: `btc-logger-backup`
4. **Description**: `Service account for BTC logger backups`
5. Click "Create and Continue"
6. **Role**: Select "Storage Admin"
7. Click "Continue" > "Done"

### Step 5: Generate Service Account Key
1. Click on your new service account
2. Go to "Keys" tab
3. Click "Add Key" > "Create New Key"
4. **Type**: JSON
5. Click "Create" - this downloads the key file
6. **⚠️ Important**: Rename the file to `service-account.json`

### Step 6: Upload Key to Render
1. Go to your Render dashboard
2. Select your BTC Logger service
3. Go to "Environment" tab
4. Add environment variables:

```bash
# Required for Google Cloud Storage
GCS_BUCKET_NAME=your-username-btc-data
GCP_PROJECT_ID=your-project-id
```

5. For the service account key, you have two options:

#### Option A: Environment Variable (Recommended)
```bash
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project",...}
```
*Copy the entire contents of your service-account.json file as the value*

#### Option B: Upload as Build File
- Add the `service-account.json` file to your repo
- Set: `GOOGLE_APPLICATION_CREDENTIALS=./service-account.json`
- **⚠️ Security**: Make sure it's in `.gitignore`

### Step 7: Update Your Environment Variables
Add these to your Render environment:

```bash
# Google Cloud Storage Configuration
GCS_BUCKET_NAME=your-username-btc-data
GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json

# Or if using JSON in environment variable:
# GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_INTERVAL_MINUTES=30
AUTO_RESTORE_ON_STARTUP=true
```

### Step 8: Test the Setup
Deploy your updated app and check:

1. **Dashboard**: `https://your-app.onrender.com/dashboard`
2. **Health Check**: `https://your-app.onrender.com/health`
3. **Trigger Backup**: 
   ```bash
   curl -X POST https://your-app.onrender.com/backup/enhanced/trigger
   ```

## 🔧 Alternative Setup Using gcloud CLI

If you prefer command line:

```bash
# 1. Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 2. Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 3. Enable API
gcloud services enable storage.googleapis.com

# 4. Create bucket
gsutil mb gs://your-username-btc-data

# 5. Create service account
gcloud iam service-accounts create btc-logger-backup \
    --display-name="BTC Logger Backup"

# 6. Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:btc-logger-backup@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# 7. Create key
gcloud iam service-accounts keys create service-account.json \
    --iam-account=btc-logger-backup@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## 🛡️ Security Best Practices

### For Development (.gitignore)
```gitignore
# Google Cloud credentials
service-account.json
*.json
.env
.env.local
```

### For Production (Render)
- Use environment variables instead of files when possible
- Rotate service account keys regularly
- Use minimal IAM permissions (Storage Admin for your bucket only)

## 💰 Cost Estimate

**Very affordable for BTC logging data:**
- **Storage**: ~$0.02/GB/month
- **Operations**: ~$0.05/10K operations
- **Your usage**: Probably $1-5/month for continuous logging

## 🧪 Testing Your Setup

### Manual Test
```bash
# Test backup
curl -X POST https://your-app.onrender.com/backup/enhanced/trigger

# Check status
curl https://your-app.onrender.com/backup/enhanced/status

# List backups
curl https://your-app.onrender.com/backup/enhanced/list
```

### View in Google Cloud Console
1. Go to [Cloud Storage](https://console.cloud.google.com/storage)
2. Click your bucket name
3. Navigate to `btc-data/` folder
4. You should see your backed up CSV and JSON files!

## 🚨 Troubleshooting

### Common Issues

**"Bucket not found"**
- Check bucket name in environment variables
- Verify bucket exists in Google Cloud Console

**"Permission denied"**
- Verify service account has Storage Admin role
- Check that service account key is valid

**"JSON decode error"**
- Verify service account JSON is properly formatted
- Check for extra characters or truncation

### Debug Commands
```bash
# Check environment variables
curl https://your-app.onrender.com/health

# Test backup manually
curl -X POST https://your-app.onrender.com/backup/enhanced/trigger

# View logs in Render dashboard
```

## ✅ Success Indicators

You'll know it's working when:
1. **Dashboard shows GCS provider**: Available providers includes "gcs"
2. **Backups appear in bucket**: Files visible in Google Cloud Console
3. **Health check passes**: `/health` shows enhanced backup available
4. **Deploy test works**: Push code, data survives the redeploy

## 🎯 What This Gives You

✅ **Code without fear** - Deploy new features, data is safe
✅ **Continuous charts** - Your JSON endpoints keep working
✅ **Disaster recovery** - Data survives any Render issues
✅ **Multi-environment** - Same data across dev/staging/prod
✅ **Version history** - Multiple backup snapshots over time

Your Bitcoin data will now survive everything! 🚀