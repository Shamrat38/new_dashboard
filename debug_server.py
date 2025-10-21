#!/usr/bin/env python
"""
Django Server Debugging Script
This script helps identify common issues that cause 500 errors on servers.
Run this script on your server to diagnose problems.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

def check_environment():
    """Check environment variables and configuration"""
    print("=== Environment Check ===")
    
    # Check if .env file exists
    env_file = project_dir / '.env'
    if env_file.exists():
        print("✓ .env file found")
    else:
        print("⚠ .env file not found - using default values")
    
    # Check critical environment variables
    critical_vars = ['SECRET_KEY', 'DEBUG', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST']
    for var in critical_vars:
        value = os.environ.get(var)
        if value:
            if var == 'DB_PASSWORD':
                print(f"✓ {var}: {'*' * len(value)}")
            else:
                print(f"✓ {var}: {value}")
        else:
            print(f"⚠ {var}: Not set")

def check_django_setup():
    """Check Django configuration"""
    print("\n=== Django Setup Check ===")
    
    try:
        django.setup()
        print("✓ Django setup successful")
        
        # Check settings
        from django.conf import settings
        print(f"✓ DEBUG: {settings.DEBUG}")
        print(f"✓ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"✓ DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
        print(f"✓ STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"✓ MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
    except Exception as e:
        print(f"✗ Django setup failed: {e}")
        return False
    
    return True

def check_database():
    """Check database connection"""
    print("\n=== Database Check ===")
    
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            if result:
                print("✓ Database connection successful")
                return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def check_migrations():
    """Check if migrations are applied"""
    print("\n=== Migrations Check ===")
    
    try:
        from django.core.management import execute_from_command_line
        from django.db import connection
        
        # Check for unapplied migrations
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT app, name FROM django_migrations 
                WHERE app IN ('authentication', 'pilgrims', 'office')
                ORDER BY app, name
            """)
            migrations = cursor.fetchall()
            
            if migrations:
                print("✓ Migrations found in database:")
                for app, name in migrations:
                    print(f"  - {app}: {name}")
            else:
                print("⚠ No migrations found - you may need to run migrations")
                
    except Exception as e:
        print(f"✗ Migration check failed: {e}")

def check_static_files():
    """Check static files configuration"""
    print("\n=== Static Files Check ===")
    
    try:
        from django.conf import settings
        
        static_root = Path(settings.STATIC_ROOT)
        if static_root.exists():
            print(f"✓ STATIC_ROOT exists: {static_root}")
        else:
            print(f"⚠ STATIC_ROOT does not exist: {static_root}")
            print("  Run: python manage.py collectstatic")
        
        media_root = Path(settings.MEDIA_ROOT)
        if media_root.exists():
            print(f"✓ MEDIA_ROOT exists: {media_root}")
        else:
            print(f"⚠ MEDIA_ROOT does not exist: {media_root}")
            print("  Create the directory: mkdir -p media")
            
    except Exception as e:
        print(f"✗ Static files check failed: {e}")

def check_logs():
    """Check log files"""
    print("\n=== Logs Check ===")
    
    logs_dir = project_dir / 'logs'
    if logs_dir.exists():
        print(f"✓ Logs directory exists: {logs_dir}")
        
        log_file = logs_dir / 'django_errors.log'
        if log_file.exists():
            print(f"✓ Error log file exists: {log_file}")
            # Show last few lines of error log
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        print("  Last 5 error log entries:")
                        for line in lines[-5:]:
                            print(f"    {line.strip()}")
                    else:
                        print("  Error log is empty")
            except Exception as e:
                print(f"  Could not read error log: {e}")
        else:
            print(f"⚠ Error log file does not exist: {log_file}")
    else:
        print(f"⚠ Logs directory does not exist: {logs_dir}")

def main():
    """Main debugging function"""
    print("Django Server Debugging Tool")
    print("=" * 50)
    
    check_environment()
    
    if check_django_setup():
        check_database()
        check_migrations()
        check_static_files()
        check_logs()
    
    print("\n=== Recommendations ===")
    print("1. Set DEBUG=False in production")
    print("2. Create .env file with proper environment variables")
    print("3. Run: python manage.py collectstatic")
    print("4. Run: python manage.py migrate")
    print("5. Check server error logs (nginx/apache)")
    print("6. Ensure database is accessible from server")
    print("7. Check file permissions on static/media directories")

if __name__ == '__main__':
    main()
