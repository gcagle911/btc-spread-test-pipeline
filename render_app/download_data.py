#!/usr/bin/env python3
"""
Data Download Helper for GCS Backup
Easy script to download your backed up BTC data
"""

import os
import sys
from datetime import datetime, timedelta
import argparse

def download_latest():
    """Download the most recent backup files"""
    print("📥 Downloading Latest Data...")
    
    try:
        from gcs_backup import get_gcs_backup
        backup = get_gcs_backup()
        
        if not backup:
            print("❌ GCS backup not configured")
            return False
        
        # List all backups and find the most recent
        backups = backup.list_backups()
        if not backups:
            print("❌ No backups found")
            return False
        
        # Find most recent historical.json
        historical_files = [b for b in backups if 'historical.json' in b['name']]
        if not historical_files:
            print("❌ No historical.json files found")
            return False
        
        latest = sorted(historical_files, key=lambda x: x.get('created', ''), reverse=True)[0]
        
        # Download it
        local_path = f"downloaded_historical_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if backup.download_backup(latest['name'], local_path):
            print(f"✅ Downloaded: {latest['name']} → {local_path}")
            return True
        else:
            print(f"❌ Failed to download {latest['name']}")
            return False
            
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def download_date(date_str):
    """Download data from a specific date (YYYY-MM-DD)"""
    print(f"📥 Downloading Data for {date_str}...")
    
    try:
        from gcs_backup import get_gcs_backup
        backup = get_gcs_backup()
        
        if not backup:
            print("❌ GCS backup not configured")
            return False
        
        # List backups for the specific date
        backups = backup.list_backups(prefix=f"btc-data/{date_str}/")
        
        if not backups:
            print(f"❌ No backups found for {date_str}")
            return False
        
        print(f"📁 Found {len(backups)} files for {date_str}")
        
        # Create download directory
        download_dir = f"downloaded_{date_str.replace('-', '')}"
        os.makedirs(download_dir, exist_ok=True)
        
        # Download all files
        success_count = 0
        for backup_file in backups:
            filename = os.path.basename(backup_file['name'])
            local_path = os.path.join(download_dir, filename)
            
            if backup.download_backup(backup_file['name'], local_path):
                print(f"✅ {filename}")
                success_count += 1
            else:
                print(f"❌ {filename}")
        
        print(f"\n📊 Download Summary: {success_count}/{len(backups)} files downloaded to {download_dir}/")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return False

def list_available_dates():
    """List all available backup dates"""
    print("📅 Available Backup Dates:")
    
    try:
        from gcs_backup import get_gcs_backup
        backup = get_gcs_backup()
        
        if not backup:
            print("❌ GCS backup not configured")
            return
        
        backups = backup.list_backups()
        
        # Extract unique dates
        dates = set()
        for backup_file in backups:
            path_parts = backup_file['name'].split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'btc-data':
                date_part = path_parts[1]  # Should be YYYY-MM-DD
                if len(date_part) == 10 and date_part.count('-') == 2:
                    dates.add(date_part)
        
        if dates:
            for date in sorted(dates, reverse=True):
                print(f"   📅 {date}")
            print(f"\nTotal: {len(dates)} days with backups")
        else:
            print("❌ No backup dates found")
            
    except Exception as e:
        print(f"❌ Failed to list dates: {e}")

def list_files(date_str=None):
    """List all backup files, optionally filtered by date"""
    if date_str:
        print(f"📋 Files for {date_str}:")
        prefix = f"btc-data/{date_str}/"
    else:
        print("📋 All Backup Files:")
        prefix = "btc-data/"
    
    try:
        from gcs_backup import get_gcs_backup
        backup = get_gcs_backup()
        
        if not backup:
            print("❌ GCS backup not configured")
            return
        
        backups = backup.list_backups(prefix=prefix)
        
        if not backups:
            print("❌ No files found")
            return
        
        # Group by type
        csv_files = []
        json_files = []
        other_files = []
        
        for backup_file in backups:
            name = backup_file['name']
            size = backup_file.get('size', 0)
            created = backup_file.get('created', 'Unknown')[:19] if backup_file.get('created') else 'Unknown'
            
            if name.endswith('.csv'):
                csv_files.append((name, size, created))
            elif name.endswith('.json'):
                json_files.append((name, size, created))
            else:
                other_files.append((name, size, created))
        
        # Display organized by type
        if json_files:
            print("\n📊 JSON Files (Processed Data):")
            for name, size, created in sorted(json_files):
                filename = os.path.basename(name)
                print(f"   📄 {filename:<25} {size:>8} bytes  {created}")
        
        if csv_files:
            print("\n📈 CSV Files (Raw Data):")
            for name, size, created in sorted(csv_files):
                filename = os.path.basename(name)
                print(f"   📄 {filename:<25} {size:>8} bytes  {created}")
        
        if other_files:
            print("\n📁 Other Files:")
            for name, size, created in sorted(other_files):
                filename = os.path.basename(name)
                print(f"   📄 {filename:<25} {size:>8} bytes  {created}")
        
        print(f"\nTotal: {len(backups)} files")
        
    except Exception as e:
        print(f"❌ Failed to list files: {e}")

def main():
    parser = argparse.ArgumentParser(description='Download BTC data from Google Cloud Storage')
    parser.add_argument('action', choices=['latest', 'date', 'list-dates', 'list-files'], 
                       help='Action to perform')
    parser.add_argument('--date', help='Date in YYYY-MM-DD format (for date/list-files actions)')
    
    args = parser.parse_args()
    
    print("🌟 BTC Data Download Helper")
    print("=" * 40)
    
    if args.action == 'latest':
        download_latest()
    elif args.action == 'date':
        if not args.date:
            print("❌ --date required for date action")
            print("   Example: python3 download_data.py date --date 2025-01-15")
        else:
            download_date(args.date)
    elif args.action == 'list-dates':
        list_available_dates()
    elif args.action == 'list-files':
        list_files(args.date)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments, show help
        print("🌟 BTC Data Download Helper")
        print("=" * 40)
        print("\nUsage examples:")
        print("  python3 download_data.py latest                    # Download most recent data")
        print("  python3 download_data.py date --date 2025-01-15    # Download specific date")
        print("  python3 download_data.py list-dates                # Show available dates")
        print("  python3 download_data.py list-files                # List all files")
        print("  python3 download_data.py list-files --date 2025-01-15  # List files for date")
        print("\nFor full help: python3 download_data.py --help")
    else:
        main()