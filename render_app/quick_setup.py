#!/usr/bin/env python3
"""
Quick Setup Script for Enhanced BTC Logger Backup System
Sets up local backup without requiring Google Cloud Storage
"""

import os
import sys
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🚀 BTC Logger Enhanced Backup - Quick Setup")
    print("=" * 60)
    print()

def create_env_file():
    """Create .env file with local backup configuration"""
    env_path = Path(".env")
    
    if env_path.exists():
        print("📄 .env file already exists")
        return
    
    env_content = """# BTC Logger Configuration - Auto-generated
PORT=10000

# Enhanced Backup System Configuration
BACKUP_ENABLED=true
BACKUP_INTERVAL_MINUTES=30
AUTO_RESTORE_ON_STARTUP=true
MAX_LOCAL_BACKUPS=10

# Legacy GCS Backup (for compatibility)
GCS_BACKUP_ENABLED=true
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with local backup configuration")

def check_dependencies():
    """Check if required Python packages are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'flask',
        'flask-cors', 
        'requests',
        'pandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("📦 Install with: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def test_backup_system():
    """Test the enhanced backup system"""
    print("\n🧪 Testing enhanced backup system...")
    
    try:
        from enhanced_backup_system import get_backup_system
        backup_system = get_backup_system()
        available_providers = backup_system.get_available_providers()
        
        print(f"✅ Enhanced backup system initialized")
        print(f"📦 Available providers: {', '.join(available_providers)}")
        
        if 'local' in available_providers:
            print("💾 Local backup provider ready")
        
        if 'gcs' in available_providers:
            print("☁️ Google Cloud Storage provider ready")
        else:
            print("ℹ️ Google Cloud Storage not configured (using local backup only)")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced backup system test failed: {e}")
        return False

def test_startup_restore():
    """Test the startup restore functionality"""
    print("\n🔧 Testing startup restore...")
    
    try:
        from startup_restore import check_data_integrity
        integrity_check = check_data_integrity()
        
        print(f"✅ Data integrity check completed")
        print(f"📊 Status: {integrity_check['status']}")
        print(f"🔄 Needs restore: {integrity_check['needs_restore']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Startup restore test failed: {e}")
        return False

def show_next_steps():
    """Show next steps for the user"""
    print("\n🎯 Setup Complete! Next Steps:")
    print()
    print("1. Start your server:")
    print("   python start_server.py")
    print()
    print("2. Monitor your backups:")
    print("   📊 Dashboard: http://localhost:10000/dashboard")
    print("   🏥 Health: http://localhost:10000/health")
    print()
    print("3. Test backup functionality:")
    print("   curl -X POST http://localhost:10000/backup/enhanced/trigger")
    print()
    print("4. Optional - Set up Google Cloud Storage:")
    print("   - Follow ENHANCED_BACKUP_SETUP.md for cloud backup")
    print("   - Adds redundancy and survives server crashes")
    print()
    print("🔒 Your data is now protected with automatic backup and restore!")

def main():
    print_header()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("📁 Working directory:", os.getcwd())
    print()
    
    # Step 1: Create environment configuration
    create_env_file()
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        return False
    
    # Step 3: Test backup system
    if not test_backup_system():
        print("\n❌ Backup system test failed")
        return False
    
    # Step 4: Test startup restore
    if not test_startup_restore():
        print("\n⚠️ Startup restore test failed, but continuing...")
    
    # Step 5: Show next steps
    show_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)