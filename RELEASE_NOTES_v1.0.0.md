# Release Notes - Version 1.0.0

**Release Date**: February 16, 2026

## 🎉 Major Release: Production-Ready with True Persistent Storage

Version 1.0.0 is a major milestone that makes the Retirement Planning App truly production-ready with reliable persistent storage for cloud deployments.

---

## ⚠️ Breaking Changes

### Authentication Storage Migration

**What Changed:**
- User credentials are now stored in the database instead of `credentials.yaml`
- Authentication system migrated from file-based (YAML) to database-based storage

**Migration Required:**
If you're upgrading from v0.9.0, run the migration tool:
```bash
python migrate_to_db.py
```

This will import your existing users from `credentials.yaml` into the database.

**Impact:**
- ✅ Existing users can continue logging in after migration
- ✅ All passwords, recovery codes, and security questions are preserved
- ⚠️ Keep `credentials.yaml` as backup until you verify everything works

---

## 🆕 New Features

### 1. PostgreSQL Support for Cloud Deployment

**The Problem:**
In v0.9.0, the app used SQLite with local file storage. Streamlit Cloud's filesystem is ephemeral - files are deleted on each deployment or restart. This meant:
- ❌ User accounts disappeared after app restarts
- ❌ All financial data was lost on redeployment
- ❌ Not suitable for production use

**The Solution:**
Version 1.0.0 introduces a flexible database abstraction layer that supports:
- ✅ **PostgreSQL** for cloud deployments (Streamlit Cloud, Render, Railway, etc.)
- ✅ **SQLite** for local development (zero configuration)
- ✅ Automatic database detection based on environment

**Benefits:**
- 🚀 Deploy to Streamlit Cloud with confidence
- 💾 True persistent storage that survives restarts
- 🔄 Easy migration between environments
- 🆓 Free tier options available (Supabase PostgreSQL)

### 2. Database Abstraction Layer

New `db_connection.py` module provides:
- Unified interface for both SQLite and PostgreSQL
- Automatic placeholder conversion (`?` → `%s`)
- Connection pooling and error handling
- Schema migration support

### 3. Streamlit Cloud + Supabase Integration

**Recommended deployment stack:**
- **App**: Streamlit Cloud (free tier)
- **Database**: Supabase PostgreSQL (free tier)

**Setup time**: ~15 minutes  
**Cost**: $0/month for typical personal/family use

See [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) for complete instructions.

### 4. Multiple Cloud Platform Support

Built-in support for:
- **Streamlit Cloud** + Supabase (recommended, free)
- **Render.com** (all-in-one, free tier with PostgreSQL)
- **Railway.app** (easy deploy, trial credit)
- **Heroku** (if you have paid tier)
- **Local SQLite** (development, zero config)

### 5. Database Migration Tooling

New `migrate_to_db.py` script:
- Automatically migrates v0.9.0 credentials to database
- Preserves all passwords (bcrypt hashes)
- Transfers recovery codes and security questions
- Safe to run multiple times (idempotent)

---

## 🔧 Technical Improvements

### Architecture

- **New Module**: `db_connection.py` - Database abstraction layer
- **New Module**: `auth_db.py` - Database-backed authentication
- **Refactored**: `user_data.py` - Now uses database abstraction
- **Refactored**: `app.py` - Updated to use new auth system

### Database Schema

All tables now support both SQLite and PostgreSQL:
- **users** - Authentication credentials (replaces credentials.yaml)
- **auth_config** - Cookie configuration
- **user_profiles** - User planning parameters
- **user_accounts** - Investment account data
- **user_expenses** - Expense categories
- **user_events** - One-time financial events
- **account_snapshots** - Historical performance tracking

### Dependencies

**New:**
- `psycopg2-binary>=2.9.0` - PostgreSQL driver

**Existing:**
- `streamlit>=1.30.0`
- `pandas>=2.0.0`
- `plotly>=5.18.0`
- `streamlit-authenticator>=0.3.0`
- `pyyaml>=6.0`

---

## 📝 Documentation Updates

### New Documentation

- **PERSISTENT_STORAGE_GUIDE.md** - Comprehensive setup guide for cloud deployment
- **secrets.toml.template** - Streamlit secrets configuration template
- **migrate_to_db.py** - Migration utility for v0.9.0 users

### Updated Documentation

- **DEPLOYMENT.md** - Completely rewritten with accurate information about cloud persistence
- **README.md** - Updated with v1.0.0 information
- **CLAUDE.md** - Updated architecture documentation

---

## 🐛 Bug Fixes

### Critical Fixes

- **Fixed**: Data persistence on Streamlit Cloud (was broken in v0.9.0)
- **Fixed**: Users losing accounts after app restart (was expected behavior in v0.9.0, now fixed)
- **Fixed**: DEPLOYMENT.md incorrectly stated Streamlit Cloud has persistent file storage

### Minor Fixes

- Improved error handling for database connection failures
- Better fallback behavior when PostgreSQL is unavailable
- More informative error messages for configuration issues

---

## 🔄 Migration Guide

### From v0.9.0 to v1.0.0

**Step 1: Update Code**
```bash
git pull origin master
pip install -r requirements.txt
```

**Step 2: Migrate Credentials (if you have existing users)**
```bash
python migrate_to_db.py
```

**Step 3: Test Locally**
```bash
streamlit run app.py
# Verify all users can login
# Verify data persists after restart
```

**Step 4: Deploy to Cloud (Optional)**

Follow [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) to:
1. Create Supabase database
2. Configure Streamlit Cloud secrets
3. Deploy and test persistence

### Rolling Back (If Needed)

If you encounter issues:
```bash
git checkout v0.9.0
# Your credentials.yaml backup still has all users
```

---

## ⚠️ Known Issues

### Supabase Free Tier Limitations

- Projects pause after 7 days of inactivity
- 500 MB database storage limit
- 2 GB bandwidth/month

**Workaround**: Visit your app once per week to keep database active, or upgrade to Supabase Pro ($25/month).

### PostgreSQL Required for Cloud

- Streamlit Cloud does NOT support persistent SQLite
- Must use PostgreSQL (Supabase, Render, Railway, etc.)
- Local development continues to work with SQLite

---

## 🚀 Upgrade Recommendations

### If You're Running v0.9.0 Locally

✅ **Upgrade immediately** - v1.0.0 adds future-proof database architecture

### If You're Running v0.9.0 on Streamlit Cloud

⚠️ **Upgrade CRITICAL** - Your data is being lost on every restart!  
Follow the migration guide above to get persistent storage.

### If You're Starting Fresh

✅ **Start with v1.0.0** - Production-ready from day one

---

## 📊 Testing Checklist

After upgrading, verify:

- [ ] App starts without errors
- [ ] Existing users can login
- [ ] New users can register
- [ ] Password recovery works
- [ ] Data saves correctly
- [ ] **CRITICAL**: Data persists after app restart
- [ ] Calculations still work correctly
- [ ] Charts render properly

---

## 💬 Feedback & Support

- **Bug Reports**: [GitHub Issues](https://github.com/conradstorz/Retire_your_way/issues)
- **Questions**: Check [PERSISTENT_STORAGE_GUIDE.md](PERSISTENT_STORAGE_GUIDE.md) first
- **Feature Requests**: Open a GitHub issue with `enhancement` label

---

## 🙏 Acknowledgments

This release addresses persistent storage challenges discovered during real-world Streamlit Cloud deployments. Special thanks to the Streamlit and Supabase communities for providing excellent documentation and free tiers that make this project accessible to everyone.

---

## 📅 Roadmap

### Planned for Future Releases

- **v1.1.0**: Monte Carlo simulation for risk analysis
- **v1.2.0**: Tax optimization strategies
- **v1.3.0**: Email notifications for account milestones
- **v2.0.0**: Multi-currency support and international tax systems

---

## 📦 What's Included

```
v1.0.0 Release Package:
├── app.py (updated)
├── calculations.py
├── auth_db.py (new)
├── auth_config.py (legacy, kept for reference)
├── user_data.py (refactored)
├── db_connection.py (new)
├── migrate_to_db.py (new)
├── requirements.txt (updated)
├── PERSISTENT_STORAGE_GUIDE.md (new)
├── DEPLOYMENT.md (rewritten)
├── secrets.toml.template (new)
├── README.md (updated)
└── RELEASE_NOTES_v1.0.0.md (this file)
```

---

## 🎯 Version 1.0.0 Summary

**Core Achievement**: Production-ready retirement planning app with true persistent storage for cloud deployments.

**Key Changes**:
- ✅ PostgreSQL support for cloud hosting
- ✅ Database-backed authentication
- ✅ Automatic environment detection
- ✅ Comprehensive deployment guides
- ✅ Migration tooling from v0.9.0

**Breaking Changes**:
- Credentials moved from YAML to database (migration provided)

**Recommendation**:
All users should upgrade to v1.0.0 for production reliability.

---

**Download**: [v1.0.0 Release](https://github.com/conradstorz/Retire_your_way/releases/tag/v1.0.0)

**Full Changelog**: [v0.9.0...v1.0.0](https://github.com/conradstorz/Retire_your_way/compare/v0.9.0...v1.0.0)

**Installation**: See [README.md](README.md)

---

*Last Updated: February 16, 2026*
