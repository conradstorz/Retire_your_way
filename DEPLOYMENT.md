# Deployment Guide

This guide covers deploying your Retirement Planning App to make it accessible to others.

## 🚀 Option 1: Streamlit Cloud (Recommended - FREE)

Streamlit Cloud is the easiest way to deploy your app publicly or privately.

### Prerequisites
- ✅ GitHub repository (you have this!)
- ✅ Streamlit Cloud account (free at [share.streamlit.io](https://share.streamlit.io))

### Deployment Steps

1. **Go to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Deploy Your App**
   - Click "New app"
   - Select your repository: `conradstorz/Retire_your_way`
   - Branch: `master`
   - Main file path: `app.py`
   - Click "Deploy"

3. **Your App Will Be Live At:**
   ```
   https://retire-your-way-[random-string].streamlit.app
   ```

4. **Share the URL**
   - Send the URL to family, friends, or clients
   - Each person creates their own account
   - All data is isolated per user

### Important Notes for Public Deployment

⚠️ **Security Considerations:**
- Your app will be publicly accessible (anyone with the URL can register)
- Consider setting your Streamlit Cloud app to **Private** if you want to control access
- Private apps require users to have Streamlit Cloud accounts
- All passwords and recovery codes are hashed and secure
- User data is stored in SQLite (persists on Streamlit Cloud)

### Making Your App Private

In Streamlit Cloud settings:
1. Go to your app's settings
2. Change visibility to "Private"
3. Only invited users can access
4. Users must have Streamlit Cloud accounts

### Persistent Storage

Streamlit Cloud provides persistent storage for your SQLite database:
- `user_data.db` will persist between deployments
- `credentials.yaml` will persist between deployments
- Free tier includes sufficient storage for multiple users

---

## 🏠 Option 2: Local Network Deployment

Share on your home/office network (already configured):

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

## ☁️ Option 3: Cloud Hosting (Advanced)

For production deployment with custom domains:

### Heroku
- Free tier available
- CLI-based deployment
- Custom domains on paid plans

### Railway
- Modern platform
- Free tier with limitations
- Easy GitHub integration

### AWS/Google Cloud/Azure
- Full control
- Requires more technical knowledge
- Scalable but paid

### DigitalOcean App Platform
- Simple deployment
- Starting at $5/month
- Custom domains included

---

## 🐳 Option 4: Docker Deployment

For containerized deployment (any platform):

**Dockerfile is included** - see `Dockerfile` for details.

Build and run:
```bash
docker build -t retirement-planner .
docker run -p 8501:8501 retirement-planner
```

---

## 📋 Pre-Deployment Checklist

Before deploying publicly, ensure:

- ✅ `credentials.yaml` and `user_data.db` in `.gitignore` (already done)
- ✅ Change default admin password immediately after deployment
- ✅ Test registration and login flows
- ✅ Test password recovery features
- ✅ Verify all calculations are working
- ✅ Check mobile responsiveness

---

## 🔒 Production Security Recommendations

If deploying for serious use (not just family/friends):

1. **Environment Variables**
   - Move cookie secret key to environment variable
   - Don't hardcode secrets

2. **HTTPS**
   - Streamlit Cloud provides HTTPS automatically ✅
   - For self-hosting, use Nginx with Let's Encrypt

3. **Rate Limiting**
   - Prevent brute force attacks
   - Consider implementing login attempt limits

4. **Database Backups**
   - Regularly backup `user_data.db`
   - Streamlit Cloud maintains backups

5. **Email Verification** (Future enhancement)
   - Verify email addresses during registration
   - Send recovery codes via email

6. **Monitoring**
   - Track errors and usage
   - Monitor for suspicious activity

---

## 📊 Scaling Considerations

For many users (100+):

- Consider PostgreSQL instead of SQLite
- Implement caching for calculations
- Use load balancing for multiple instances
- Add database connection pooling

---

## 🆘 Support & Maintenance

**For Streamlit Cloud:**
- Check app logs in Streamlit Cloud dashboard
- Monitor resource usage
- Update by pushing to GitHub (auto-deploys)

**For Self-Hosting:**
- Keep dependencies updated: `pip install -r requirements.txt --upgrade`
- Monitor disk space for database growth
- Set up automated backups

---

## 🎯 Recommended Approach

**For Personal/Family Use (5-20 users):**
→ **Streamlit Cloud (Free)** is perfect!

**For Small Business/Clients (20-100 users):**
→ **Railway or DigitalOcean** with custom domain

**For Enterprise (100+ users):**
→ **AWS/Google Cloud** with proper infrastructure

---

## Next Steps

1. Deploy to Streamlit Cloud (takes 5 minutes!)
2. Test with a friend/family member
3. Share the URL
4. Enjoy transparent retirement planning for all! 🎉

**Need help?** Check the [Streamlit Cloud docs](https://docs.streamlit.io/streamlit-community-cloud)
