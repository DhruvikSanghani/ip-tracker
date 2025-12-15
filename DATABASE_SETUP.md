# PostgreSQL Database Setup Guide

Complete guide for setting up the PostgreSQL database for the IP Tracker application on Windows.

## Prerequisites

- Windows OS
- Administrator access
- Internet connection

## Step 1: Install PostgreSQL

### Download PostgreSQL

1. Visit the official PostgreSQL download page: https://www.postgresql.org/download/windows/
2. Click on "Download the installer" (recommended: PostgreSQL 15 or later)
3. Download the Windows x86-64 installer

### Install PostgreSQL

1. Run the downloaded installer
2. Click "Next" through the setup wizard
3. **Installation Directory**: Use default (`C:\Program Files\PostgreSQL\15`)
4. **Select Components**: Keep all selected (PostgreSQL Server, pgAdmin 4, Stack Builder, Command Line Tools)
5. **Data Directory**: Use default (`C:\Program Files\PostgreSQL\15\data`)
6. **Password**: Set a strong password for the `postgres` superuser (e.g., `admin`)
   - **IMPORTANT**: Remember this password!
7. **Port**: Use default `5432`
8. **Locale**: Use default locale
9. Click "Next" and then "Finish"

## Step 2: Verify PostgreSQL Installation

1. Open Command Prompt (Win + R, type `cmd`, press Enter)
2. Navigate to PostgreSQL bin directory:
   ```cmd
   cd "C:\Program Files\PostgreSQL\15\bin"
   ```
3. Test connection:
   ```cmd
   psql -U postgres
   ```
4. Enter the password you set during installation
5. You should see the PostgreSQL prompt: `postgres=#`
6. Type `\q` to exit

## Step 3: Create Database

### Option A: Using Command Line (Recommended)

1. Open Command Prompt as Administrator
2. Navigate to PostgreSQL bin:
   ```cmd
   cd "C:\Program Files\PostgreSQL\15\bin"
   ```
3. Connect to PostgreSQL:
   ```cmd
   psql -U postgres
   ```
4. Create the database:
   ```sql
   CREATE DATABASE ip_tracker;
   ```
5. Verify database creation:
   ```sql
   \l
   ```
   You should see `ip_tracker` in the list
6. Exit:
   ```sql
   \q
   ```

### Option B: Using pgAdmin 4 (GUI)

1. Open pgAdmin 4 from Start Menu
2. Enter your master password (if prompted)
3. Expand "Servers" → "PostgreSQL 15"
4. Enter your postgres password
5. Right-click "Databases" → "Create" → "Database"
6. Database name: `ip_tracker`
7. Owner: `postgres`
8. Click "Save"

## Step 4: Update Application Configuration

The application is already configured to connect to the database. Verify the connection string in `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/ip_tracker'
```

**If you used a different password**, update the connection string:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:YOUR_PASSWORD@localhost:5432/ip_tracker'
```

## Step 5: Install Python Dependencies

1. Open Command Prompt in your project directory:
   ```cmd
   cd C:\Users\sangh\Desktop\ip-tracker
   ```

2. Install required packages:
   ```cmd
   pip install -r requirements.txt
   ```

## Step 6: Initialize Database Tables

The application will automatically create all necessary tables on first run. However, you can also use Flask-Migrate for better control:

### Option A: Automatic Creation (Simple)

Just run the application:
```cmd
python app.py
```

The tables will be created automatically when the app starts.

### Option B: Using Flask-Migrate (Recommended for Production)

1. Initialize migrations:
   ```cmd
   flask db init
   ```

2. Create initial migration:
   ```cmd
   flask db migrate -m "Initial migration with enhanced tracking"
   ```

3. Apply migration:
   ```cmd
   flask db upgrade
   ```

## Step 7: Verify Database Tables

1. Connect to PostgreSQL:
   ```cmd
   cd "C:\Program Files\PostgreSQL\15\bin"
   psql -U postgres -d ip_tracker
   ```

2. List tables:
   ```sql
   \dt
   ```

3. View table structure:
   ```sql
   \d visitor_data
   ```

You should see all columns including:
- Basic fields: `id`, `ip_address`, `user_agent`, `browser`, etc.
- Location fields: `latitude`, `longitude`, `country`, `city`, etc.
- **New enhanced fields**: `camera_image`, `device_fingerprint`, `timezone`, `battery_level`, `connection_type`, `canvas_fingerprint`, `webgl_fingerprint`, etc.

## Step 8: Test the Application

1. Start the Flask application:
   ```cmd
   python app.py
   ```

2. Open your browser and navigate to:
   - Main page: `http://localhost:5000`
   - Admin login: `http://localhost:5000/login`
   - Default credentials: `admin` / `admin123`

3. Test data collection:
   - Visit the main page
   - Grant location permission
   - Grant camera permission (if prompted)
   - Check admin dashboard to see captured data

## Troubleshooting

### Issue: "psql: command not found"

**Solution**: Add PostgreSQL to PATH:
1. Open System Properties → Advanced → Environment Variables
2. Under System Variables, find "Path"
3. Click "Edit" → "New"
4. Add: `C:\Program Files\PostgreSQL\15\bin`
5. Click OK and restart Command Prompt

### Issue: "password authentication failed for user postgres"

**Solution**: 
1. Locate `pg_hba.conf` file (usually in `C:\Program Files\PostgreSQL\15\data\`)
2. Open with Notepad as Administrator
3. Find lines with `md5` and change to `trust` (temporarily)
4. Restart PostgreSQL service
5. Reset password and change back to `md5`

### Issue: "could not connect to server"

**Solution**:
1. Open Services (Win + R, type `services.msc`)
2. Find "postgresql-x64-15"
3. Right-click → Start
4. Set Startup Type to "Automatic"

### Issue: Database tables not created

**Solution**:
1. Delete the database and recreate:
   ```sql
   DROP DATABASE ip_tracker;
   CREATE DATABASE ip_tracker;
   ```
2. Run the application again or use Flask-Migrate

### Issue: "relation 'visitor_data' does not exist"

**Solution**: The tables haven't been created. Run:
```python
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

## Database Maintenance

### Backup Database

```cmd
cd "C:\Program Files\PostgreSQL\15\bin"
pg_dump -U postgres ip_tracker > backup.sql
```

### Restore Database

```cmd
cd "C:\Program Files\PostgreSQL\15\bin"
psql -U postgres ip_tracker < backup.sql
```

### View All Data

```sql
SELECT * FROM visitor_data ORDER BY visit_time DESC LIMIT 10;
```

### Clear All Data (Caution!)

```sql
TRUNCATE TABLE visitor_data;
```

## Security Recommendations

1. **Change default admin password**: Update `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env` file
2. **Use strong database password**: Don't use `admin` in production
3. **Enable SSL**: Configure PostgreSQL to use SSL connections
4. **Firewall**: Only allow local connections to PostgreSQL (port 5432)
5. **Regular backups**: Set up automated daily backups

## Production Deployment

For production deployment:

1. Use environment variables for sensitive data:
   ```python
   # In .env file
   DATABASE_URL=postgresql://username:password@localhost:5432/ip_tracker
   ADMIN_USERNAME=your_admin_username
   ADMIN_PASSWORD=your_secure_password
   SECRET_KEY=your_secret_key_here
   ```

2. Update `app.py` to use environment variables:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
   app.secret_key = os.getenv('SECRET_KEY')
   ```

3. Never commit `.env` file to version control

## Additional Resources

- PostgreSQL Documentation: https://www.postgresql.org/docs/
- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/
- Flask-Migrate: https://flask-migrate.readthedocs.io/

## Support

If you encounter any issues:
1. Check PostgreSQL logs: `C:\Program Files\PostgreSQL\15\data\log\`
2. Check Flask application logs in the console
3. Verify all services are running
4. Ensure firewall isn't blocking port 5432
