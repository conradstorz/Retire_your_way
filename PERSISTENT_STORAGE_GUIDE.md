# Setup Guide for Version 1.0.0

This guide explains how to set up persistent storage for the Retirement Planning Application v1.0.0.

## Overview

Version 1.0.0 introduces flexible database support:
- **Local Development**: Uses SQLite (no configuration needed)
- **Cloud Deployment**: Uses PostgreSQL for persistent storage

## Local Development (SQLite)

**No configuration needed!** Just run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app automatically creates a local `user_data.db` SQLite database file.

### Migrating from Previous Version

If you have an existing `credentials.yaml` file from version 0.9.0:

```bash
python migrate_to_db.py
```

This will import your users into the database. Keep the `credentials.yaml` file as a backup.

---

## Cloud Deployment Options

### Option 1: Streamlit Cloud + Supabase (Recommended, FREE)

**Best for**: Easy deployment with persistent storage

#### Step 1: Create Supabase Account

1. Go to [supabase.com](https://supabase.com)
2. Click "Start your project"
3. Sign in with GitHub
4. Create a new project:
   - Name: `retirement-planner`
   - Database Password: (create a strong password, save it!)
   - Region: (choose closest to your users)

#### Step 2: Get Database Credentials

1. In your Supabase project, go to **Settings** → **Database**
2. Copy the connection parameters:
   - **Host**: `db.xxxxxxxxxxxxx.supabase.co`
   - **Port**: `5432`
   - **Database name**: `postgres`
   - **User**: `postgres`
   - **Password**: (your database password)

#### Step 3: Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click **"New app"**
5. Select:
   - Repository: `your-username/your-repo`
   - Branch: `master`  
   - Main file: `app.py`

#### Step 4: Add Secrets to Streamlit Cloud

1. In your Streamlit Cloud app settings, go to **"Secrets"**
2. Paste your database credentials:

```toml
[postgres]
host = "db.xxxxxxxxxxxxx.supabase.co"
port = 5432
database = "postgres"
user = "postgres"
password = "your-supabase-password"
```

3. Click **"Save"**
4. Your app will restart automatically

**Done! Your app now has persistent storage.**

---

### Option 2: Render.com (FREE with PostgreSQL)

**Best for**: All-in-one solution with built-in database

#### Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Create a new **Web Service**:
   - Connect your GitHub repository
   - Name: `retirement-planner`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

#### Step 2: Create PostgreSQL Database

1. In Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Name: `retirement-planner-db`
3. Plan: **Free** (stores 1GB)
4. Create database

#### Step 3: Connect Database to Web Service

1. Go to your web service settings
2. Click **"Environment"** tab
3. Add environment variable:
   - Key: `DATABASE_URL`
   - Value: (copy the **Internal Database URL** from your PostgreSQL database)

4. Save changes

**Done! Render automatically provides persistent storage via PostgreSQL.**

---

### Option 3: Railway.app

**Best for**: Simple deployment with databases

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Create new project → Deploy from GitHub
4. Select your repository
5. Add PostgreSQL plugin
6. Railway automatically sets `DATABASE_URL`

**Done! Railway manages everything automatically.**

---

### Option 4: Heroku

**Note**: Heroku no longer has a free tier, but is included for completeness.

1. Install Heroku CLI
2. Login: `heroku login`
3. Create app: `heroku create your-app-name`
4. Add PostgreSQL: `heroku addons:create heroku-postgresql:mini`
5. Deploy: `git push heroku master`

---

## Testing Your Cloud Deployment

After deployment:

1. Visit your app URL
2. Register a new account
3. Add some data and save
4. Stop and restart your app (in the hosting platform)
5. Login again - **your data should still be there!**

If data persists after restart, your persistent storage is working correctly.

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'psycopg2'"

Make sure `requirements.txt` includes:
```
psycopg2-binary>=2.9.0
```

### "Unable to connect to database"

**For Supabase:**
- Check that your secrets match exactly (no extra spaces)
- Verify your project is not paused (Supabase pauses inactive free projects after 7 days)
- Check host format: should be `db.xxxxx.supabase.co` (not `https://...`)

**For Render/Railway/Heroku:**
- Verify `DATABASE_URL` environment variable is set
- Check database status in hosting dashboard

### "Permission denied" on database

Your database user needs permission to create tables. For Supabase, the default `postgres` user has full permissions.

### App works locally but not in cloud

- Verify secrets are configured correctly in your hosting platform
- Check deployment logs for error messages
- Make sure `psycopg2-binary` is in requirements.txt

---

## Security Notes

- Never commit `credentials.yaml`, `user_data.db`, or `.streamlit/secrets.toml` to git
- Change the default admin password immediately after first login
- Use strong passwords for your database
- For Supabase, enable Row Level Security (RLS) for additional protection

---

## Data Migration

If you need to move data between environments:

### Export from Local SQLite:
```bash
sqlite3 user_data.db .dump > backup.sql
```

### Import to PostgreSQL:
```bash
# Connect to your PostgreSQL database
psql postgresql://user:pass@host:port/database < backup.sql
```

Or use the Supabase web interface:
1. Go to **Table Editor**
2. Import SQL file

---

## Getting Help

- **GitHub Issues**: [Report a bug](https://github.com/your-repo/issues)
- **Documentation**: See [README.md](README.md) and [DEPLOYMENT.md](DEPLOYMENT.md)
- **Supabase Docs**: https://supabase.com/docs
- **Streamlit Docs**: https://docs.streamlit.io

---

**Congratulations!** Your retirement planner now has rock-solid persistent storage. 🎉
