# Quick Setup Script for IP Tracker
# Run this after installing PostgreSQL and creating the database

import os
import sys

def main():
    print("=" * 60)
    print("IP TRACKER - GOD LEVEL - QUICK SETUP")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found!")
        print("Please run this script from the ip-tracker directory")
        sys.exit(1)
    
    print("✓ Found app.py")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    os.system('pip install -r requirements.txt')
    
    print("\n✓ Dependencies installed")
    
    # Initialize database
    print("\n🗄️  Initializing database...")
    try:
        from app import app, db
        with app.app_context():
            db.create_all()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running")
        print("2. Database 'ip_tracker' exists")
        print("3. Connection string in app.py is correct")
        sys.exit(1)
    
    # Display success message
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Run the application: python app.py")
    print("2. Open browser: http://localhost:5000")
    print("3. Admin login: http://localhost:5000/login")
    print("   - Username: admin")
    print("   - Password: admin123")
    print("\n🔒 SECURITY REMINDER:")
    print("Change default admin credentials in production!")
    print("\n📚 Documentation:")
    print("- Database setup: DATABASE_SETUP.md")
    print("- Features guide: See walkthrough artifact")
    print()

if __name__ == '__main__':
    main()
