# Deployment Guide - Version 1.0.0

This guide covers deploying your Retirement Planning App with persistent storage.

## 🎯 Quick Start

**Local Development**: No configuration needed - just run:
```bash
pip install -r requirements.txt
streamlit run app.py
```

**Cloud Deployment**: See [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) for detailed instructions.

---

## 🚀 Recommended Cloud Deployment: Streamlit Cloud + Supabase

**Why this combination?**
- ✅ Both have free tiers
- ✅ Easy setup (15 minutes)
- ✅ True persistent storage
- ✅ Auto-deploys from GitHub
- ✅ HTTPS included
- ✅ Great for personal/family use (up to hundreds of users)

### Quick Steps

1. **Create Supabase database** ([supabase.com](https://supabase.com))
   - Sign up with GitHub
   - Create new project
   - Save database credentials

2. **Deploy to Streamlit Cloud** ([share.streamlit.io](https://share.streamlit.io))
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `conradstorz/Retire_your_way`
   - Branch: `master`
   - Main file: `app.py`

3. **Configure Secrets** (in Streamlit Cloud app settings)
   ```toml
   [postgres]
   host = "db.xxxxx.supabase.co"
   port = 5432
   database = "postgres"
user = "postgres"
   password = "your-supabase-password"
   ```

4. **Done!** Your app is live with persistent storage

**📖 Detailed walkthrough**: See [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md)

---

## ⚠️ Important: Streamlit Cloud Storage Limitations

**Streamlit Cloud filesystem is EPHEMERAL** - files are deleted on each deployment or restart.

❌ **This DOES NOT work:**
- Storing SQLite database directly on Streamlit Cloud
- Writing files to disk without external storage

✅ **This DOES work:**
- Using PostgreSQL (via Supabase, Render, Railway, etc.)
- Database-backed persistent storage (implemented in v1.0.0)

---

## 🌐 All Deployment Options

## 🌐 All Deployment Options

| Platform | Persistent Storage | Free Tier | Setup Complexity | Best For |
|----------|-------------------|-----------|------------------|----------|
| **Streamlit Cloud + Supabase** | ✅ PostgreSQL | ✅ Yes | ⭐⭐ Easy | Personal/Family |
| **Render.com** | ✅ PostgreSQL | ✅ Yes | ⭐⭐ Easy | Small Teams |
| **Railway.app** | ✅ PostgreSQL | ⚠️ Trial Credit | ⭐ Very Easy | Quick Prototypes |
| **Local SQLite** | ✅ Local File | ✅ Yes | ⭐ Easiest | Development/Testing |
| **Self-Hosted VPS** | ✅ Your Choice | ❌ Paid | ⭐⭐⭐⭐ Advanced | Full Control |

---

### Option 1: Streamlit Cloud + Supabase (Recommended)

**Cost**: FREE for both
**Setup Time**: 15 minutes
**Persistent Storage**: ✅ PostgreSQL

See [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) for complete instructions.

---

### Option 2: Render.com (All-in-One)

**Cost**: FREE (includes PostgreSQL)
**Setup Time**: 20 minutes
**Persistent Storage**: ✅ PostgreSQL

Render provides both app hosting and database in one platform.

See [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) for complete instructions.

---

### Option 3: Railway.app

**Cost**: FREE trial credit (then paid)
**Setup Time**: 10 minutes
**Persistent Storage**: ✅ PostgreSQL

Railway automatically connects your app to PostgreSQL with zero configuration.

See [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) for complete instructions.

---

### Option 4: Local Development

**Cost**: FREE
**Setup Time**: 2 minutes
**Persistent Storage**: ✅ SQLite (local file)

```bash
pip install -r requirements.txt
streamlit run app.py
```

**Perfect for:**
- Testing and development
- Single-user personal use
- Offline usage

**Limitations:**
- Only accessible on your computer
- Not accessible from mobile devices (unless on same network)
- No automatic backups

---

### Option 5: Local Network Deployment

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

**Access from other devices:**
- Find your computer's IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
- Share URL: `http://YOUR_IP_ADDRESS:8501`
- Users on same network can access it

**Pros:**
- Complete control
- Keep data on your computer
- No internet required

**Cons:**
- Only works on local network
- Computer must stay running
- Not accessible from outside your network

---

### Option 5: Local Network Deployment

**Cost**: FREE
**Setup Time**: 5 minutes
**Persistent Storage**: ✅ SQLite (local file)

Share on your home/office network:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

**Access from other devices:**
- Find your computer's IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
- Share URL: `http://YOUR_IP_ADDRESS:8501`
- Users on same network can access it

**Pros:**
- Complete control
- Keep data on your computer
- No internet required
- Free

**Cons:**
- Only works on local network
- Computer must stay running
- Not accessible from outside your network
- Manual backups required

---

## 🐳 Docker Deployment

For containerized deployment (any platform):

**Dockerfile is included** - see `Dockerfile` for details.

Build and run:
```bash
docker build -t retirement-planner .
docker run -p 8501:8501 -v $(pwd)/data:/app/data retirement-planner
```

**Note**: Mount a volume for persistent storage!

---

## 📋 Pre-Deployment Checklist

Before deploying publicly:

## 📋 Pre-Deployment Checklist

Before deploying publicly:

- ✅ Persistent storage configured (PostgreSQL or local SQLite)
- ✅ Database connection tested (data persists after restart)
- ✅ Change default admin password immediately after deployment
- ✅ Test user registration and login flows
- ✅ Test password recovery features
- ✅ Verify calculations are working correctly
- ✅ Check mobile responsiveness
- ✅ Secrets properly configured (not in git!)

---

## 🔒 Security Best Practices

### Streamlit Cloud + Supabase

**Already secure out-of-the-box:**
- ✅ HTTPS automatic
- ✅ Passwords bcrypt-hashed in database
- ✅ Database credentials in Streamlit secrets (not in code)
- ✅ Supabase has DDoS protection

**Additional recommendations:**
- Change default admin password immediately
- Set app to "Private" in Streamlit Cloud if not for public use
- Enable Supabase Row Level Security (RLS) for multi-tenancy
- Monitor Supabase logs for suspicious activity

### Self-Hosted Deployment

If deploying on your own server:
- Use HTTPS (Let's Encrypt is free)
- Set up firewall rules
- Keep dependencies updated
- Implement  rate limiting for login attempts
- Regular database backups
- Monitor server logs

---

## 📊 Performance & Scaling

### Current Capacity

**Streamlit Cloud Free Tier:**
- Suitable for 10-100 concurrent users
- 1 GB RAM limit
- Good for family/small team use

**Supabase Free Tier:**
- 500 MB database storage
- 2 GB bandwidth/month
- Sufficient for hundreds of users

### When to Upgrade

Consider paid tiers when:
- You have 100+ regular users
- Database exceeds 500 MB
- Need faster response times
- Want custom domain
- Need guaranteed uptime SLA

**Costs (approximate):**
- Supabase Pro: $25/month (8 GB database, better performance)
- Streamlit Cloud Team: $250/month (more resources, private sharing)
- Render Starter: $7/month (PostgreSQL with 1 GB storage)

---

## 🔄 Migrating Existing Data

### From v0.9.0 to v1.0.0 (YAML → Database)

If you have an existing deployment with `credentials.yaml`:

```bash
python migrate_to_db.py
```

This migrates:
- All user accounts and passwords
- Recovery codes  
- Security questions
- Cookie configuration

**After migration:**
- Keep `credentials.yaml` as backup
- Test that all users can still login
- Verify data persists after app restart

### Between Environments

**Export from local SQLite:**
```bash
sqlite3 user_data.db .dump > backup.sql
```

**Import to PostgreSQL:**
```bash
psql postgresql://user:pass@host:port/database < backup.sql
```

Or use hosting platform's database tools (Supabase has a SQL editor).

---

## 🆘 Troubleshooting

### Data Not Persisting

**Symptom**: Users register, but accounts disappear after restart

**Solutions:**
- Verify PostgreSQL is configured (check secrets)
- Test database connection manually
- Check deployment logs for connection errors
- Ensure `DATABASE_URL` or `[postgres]` secrets are set

### "Connection Refused" Errors

**Solutions:**
- Check database is running (Supabase projects pause after 7 days inactive)
- Verify host/port are correct
- Check firewall allows outbound connections
- Ensure credentials haven't expired

### Slow Performance

**Solutions:**
- Upgrade to paid tier (more CPU/RAM)
- Optimize calculations (reduce projection complexity)
- Add caching for repeated calculations
- Use database indexes for large user counts

### Module Not Found Errors

**Solutions:**
- Ensure `requirements.txt` is complete
- Include `psycopg2-binary>=2.9.0` for PostgreSQL
- Clear deployment cache and redeploy

See [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) for more troubleshooting help.

---

## ��� Recommended Deployment Path

**Choose based on your needs:**

### Just Me / My Family (< 10 users)
→ **Local SQLite** or **Streamlit Cloud + Supabase**

### Small Team (10-50 users)
→ **Streamlit Cloud + Supabase** (both free!)

### Growing Business (50-200 users)
→ **Render.com** or **Railway** (paid, with support)

### Large Organization (200+ users)
→ **Self-hosted** or **Enterprise cloud** (AWS/Azure/GCP)

---

## ��� Tips for Success

1. **Start Small**: Deploy locally first, test thoroughly
2. **Test Persistence**: After cloud deployment, register a user, restart the app, verify data remains
3. **Backup Early**: Export your database regularly
4. **Monitor Usage**: Watch for performance issues as users grow
5. **Update Regularly**: Keep dependencies current for security

---

## ��� Additional Resources

- **Persistent Storage Setup**: [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md)
- **Supabase Docs**: https://supabase.com/docs
- **Streamlit Cloud Docs**: https://docs.streamlit.io/streamlit-community-cloud
- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app

---

## ��� Next Steps

1. **Read** [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) for detailed setup
2. **Choose** your deployment platform
3. **Deploy** following the guide
4. **Test** that data persists after restart
5. **Share** with your users!

**Questions?** Open an issue on GitHub or check the documentation.

**Congratulations on deploying your retirement planner! ���**
