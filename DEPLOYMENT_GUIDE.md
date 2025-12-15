# Free HTTPS Hosting Guide for IP Tracker

Complete guide to deploy your IP tracker application for free with HTTPS support.

## 🚀 Best Free Hosting Options

### Option 1: Render.com (Recommended) ⭐
- **Free HTTPS** included automatically
- **PostgreSQL database** included (free tier)
- **Easy deployment** from GitHub
- **Auto-deploy** on git push
- **Custom domain** support

### Option 2: Railway.app
- **Free HTTPS** included
- **PostgreSQL** included
- **$5 free credit** monthly
- **Easy setup**

### Option 3: Fly.io
- **Free HTTPS** included
- **PostgreSQL** available
- **Good free tier**

---

## 📋 Recommended: Render.com Deployment

### Prerequisites
1. GitHub account
2. Your code pushed to GitHub repository

---

## Step-by-Step Deployment on Render.com

### Step 1: Prepare Your Code

#### 1.1 Create `.gitignore` file

Create `c:\Users\sangh\Desktop\ip-tracker\.gitignore`:

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.env
*.db
*.sqlite3
instance/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
migrations/
```

#### 1.2 Update `requirements.txt`

Ensure your `requirements.txt` is complete (already done):
```
Flask
Flask-SQLAlchemy
Flask-Migrate
requests
python-dotenv
Werkzeug
SQLAlchemy
WTForms
Flask-WTF
Flask-Login
psycopg2-binary
Pillow
python-dateutil
pytz
gunicorn
```

**Note**: Add `gunicorn` if not present (production server)

#### 1.3 Create `Procfile`

Create `c:\Users\sangh\Desktop\ip-tracker\Procfile`:

```
web: gunicorn app:app
```

#### 1.4 Update `app.py` for Production

Add this at the end of `app.py` (before `if __name__ == '__main__':`):

```python
# Production configuration
if os.getenv('RENDER'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
```

---

### Step 2: Push to GitHub

```cmd
cd C:\Users\sangh\Desktop\ip-tracker

# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - IP Tracker"

# Create repository on GitHub (via website)
# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/ip-tracker.git
git branch -M main
git push -u origin main
```

---

### Step 3: Deploy on Render.com

#### 3.1 Create Account
1. Go to https://render.com
2. Sign up with GitHub
3. Authorize Render to access your repositories

#### 3.2 Create PostgreSQL Database
1. Click **"New +"** → **"PostgreSQL"**
2. Settings:
   - **Name**: `ip-tracker-db`
   - **Database**: `ip_tracker`
   - **User**: (auto-generated)
   - **Region**: Choose closest to your users
   - **Plan**: **Free**
3. Click **"Create Database"**
4. **Save the Internal Database URL** (you'll need this)

#### 3.3 Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Settings:
   - **Name**: `ip-tracker`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: (leave empty)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: **Free**

#### 3.4 Add Environment Variables
In the **Environment** section, add:

```
RENDER=true
DATABASE_URL=<paste your Internal Database URL from step 3.2>
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_secure_password
SECRET_KEY=your_random_secret_key_here
```

**Generate SECRET_KEY**:
```python
import secrets
print(secrets.token_hex(32))
```

4. Click **"Create Web Service"**

#### 3.5 Initialize Database
After deployment completes:
1. Go to your web service dashboard
2. Click **"Shell"** tab
3. Run:
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

---

### Step 4: Access Your Site

Your site will be available at:
```
https://ip-tracker.onrender.com
```

**HTTPS is automatic!** ✅

---

## 🔧 Alternative: Railway.app Deployment

### Step 1: Prepare Code
Same as Render (Steps 1.1 - 1.4 above)

### Step 2: Deploy on Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose your repository
6. Railway will auto-detect Flask app

### Step 3: Add PostgreSQL
1. Click **"New"** → **"Database"** → **"PostgreSQL"**
2. Database will be automatically linked

### Step 4: Environment Variables
Add in **Variables** tab:
```
ADMIN_USERNAME=your_admin
ADMIN_PASSWORD=your_password
SECRET_KEY=your_secret_key
```

### Step 5: Custom Domain (Optional)
1. Go to **Settings** → **Domains**
2. Click **"Generate Domain"**
3. Your site: `https://your-app.up.railway.app`

**HTTPS is automatic!** ✅

---

## 🌐 Custom Domain Setup (Optional)

### For Render.com:
1. Go to your web service
2. Click **"Settings"** → **"Custom Domains"**
3. Click **"Add Custom Domain"**
4. Enter your domain (e.g., `mytracker.com`)
5. Add DNS records at your domain registrar:
   ```
   Type: CNAME
   Name: www (or @)
   Value: <your-app>.onrender.com
   ```
6. **SSL certificate** is automatic!

### Free Domain Options:
- **Freenom** (free .tk, .ml, .ga domains)
- **InfinityFree** (free subdomain)
- Use Render's free subdomain

---

## 🔒 Security Checklist

Before going live:

### 1. Change Default Credentials
```python
# In .env or Render environment variables
ADMIN_USERNAME=strong_username_here
ADMIN_PASSWORD=VeryStr0ng!P@ssw0rd123
SECRET_KEY=<64-character-random-string>
```

### 2. Update `app.py`
```python
# Remove hardcoded credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
app.secret_key = os.getenv('SECRET_KEY')
```

### 3. Add Rate Limiting
Install Flask-Limiter:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

### 4. HTTPS Only
Add to `app.py`:
```python
@app.before_request
def before_request():
    if not request.is_secure and os.getenv('RENDER'):
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
```

---

## 📊 Monitoring & Maintenance

### Render.com Dashboard
- **Logs**: View real-time logs
- **Metrics**: CPU, Memory usage
- **Events**: Deployment history

### Database Backups
Render Free tier includes:
- Automatic backups (7 days retention)
- Manual backup via dashboard

### Scaling
Free tier limitations:
- **Render**: Spins down after 15 min inactivity
- **Railway**: $5/month credit
- **Upgrade** to paid plan for 24/7 uptime

---

## 🐛 Troubleshooting

### Issue: "Application Error"
**Solution**: Check logs in Render dashboard
```bash
# Common fixes:
1. Ensure all dependencies in requirements.txt
2. Check DATABASE_URL is set correctly
3. Verify Python version compatibility
```

### Issue: Database Connection Failed
**Solution**:
```bash
# Verify DATABASE_URL format
# Should be: postgresql://user:pass@host:5432/dbname
```

### Issue: Camera Not Working
**Solution**: HTTPS is required for camera access
- Render provides HTTPS automatically ✅
- Never use HTTP for camera features

### Issue: Site Slow to Wake Up
**Solution**: Free tier spins down after inactivity
- First request takes 30-60 seconds
- Upgrade to paid plan for always-on
- Use UptimeRobot to ping every 5 minutes (keeps it awake)

---

## 🎯 Quick Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] `requirements.txt` includes `gunicorn`
- [ ] `Procfile` created
- [ ] `.gitignore` created
- [ ] Render account created
- [ ] PostgreSQL database created on Render
- [ ] Web service created on Render
- [ ] Environment variables set
- [ ] Database initialized
- [ ] Site accessible via HTTPS
- [ ] Admin login working
- [ ] Camera permission working (HTTPS required)
- [ ] Location permission working
- [ ] Default credentials changed

---

## 💰 Cost Comparison

| Platform | Free Tier | HTTPS | Database | Custom Domain |
|----------|-----------|-------|----------|---------------|
| **Render** | ✅ 750 hrs/mo | ✅ Auto | ✅ Free PostgreSQL | ✅ Free |
| **Railway** | ✅ $5 credit | ✅ Auto | ✅ Free PostgreSQL | ✅ Free |
| **Fly.io** | ✅ Limited | ✅ Auto | ✅ Free PostgreSQL | ✅ Free |
| **Heroku** | ❌ Paid only | ✅ Auto | ✅ Paid | ✅ Paid |

**Recommendation**: Start with **Render.com** for best free tier.

---

## 🚀 Going Live

Once deployed:

1. **Test everything**:
   - Visit your site
   - Grant camera permission
   - Grant location permission
   - Check admin dashboard
   - Verify data is captured

2. **Share your link**:
   ```
   https://your-app-name.onrender.com
   ```

3. **Monitor usage**:
   - Check Render dashboard regularly
   - Monitor database size
   - Review captured data

---

## 📝 Summary

**Fastest Path to Free HTTPS Hosting**:

1. Add `gunicorn` to `requirements.txt`
2. Create `Procfile` with `web: gunicorn app:app`
3. Push code to GitHub
4. Sign up on Render.com
5. Create PostgreSQL database
6. Create Web Service from GitHub repo
7. Add environment variables
8. Deploy!

**Your site will be live with HTTPS in ~10 minutes!** 🎉

---

## 🔗 Useful Links

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **Flask Deployment**: https://flask.palletsprojects.com/en/latest/deploying/
- **Gunicorn Docs**: https://docs.gunicorn.org/

---

## ⚠️ Legal Reminder

Before going live:
- Add **Privacy Policy** (camera & location data collection)
- Add **Terms of Service** (18+ age verification)
- Add **Cookie Notice**
- Ensure **GDPR/CCPA compliance**
- Add **Data Deletion** mechanism

**Your site collects biometric data (camera images) and precise location. Ensure legal compliance in your jurisdiction.**
