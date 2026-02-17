# Release Notes for v0.9.0

## 💰 Retirement Planning Application - Initial Release

I'm excited to announce the first release of a comprehensive, multi-user retirement planning application built with Python and Streamlit!

### 🎯 What is This?

A transparent retirement planning tool that replaces complex spreadsheet formulas with clear, documented Python code. Each user gets their own secure account with personalized financial data and projections.

### ✨ Key Features

#### Multi-User System
- **Secure authentication** with bcrypt password hashing
- **User registration** with email validation
- **Password recovery** via recovery codes or security questions
- **Independent data** for each user stored in SQLite

#### Advanced Financial Modeling
- **Planned annual contributions** per investment account
- **Account type rules** (401k stops at retirement, IRA at 73, Roth never stops)
- **Historical snapshots** to track actual performance over time
- **Required Minimum Distributions (RMDs)** calculated automatically
- **CORE vs FLEX expenses** with intelligent reduction during deficits
- **Year-by-year projections** with Social Security and inflation
- **Withdrawal priority ordering** for smart portfolio management

#### Analysis & Insights
- **Portfolio run-out age** calculation
- **Cushion years** to assess financial security
- **Sustainable withdrawal guidance** (4% rule comparison)
- **Sanity checks** tab for data validation
- **Comprehensive warnings** for potential issues

#### Modern Interface
- **Interactive Plotly charts** showing account balances and cash flow
- **Tabbed navigation** for easy configuration
- **CSV export** for detailed analysis
- **Real-time updates** as you adjust parameters

### 🚀 Getting Started

**Requirements:** Python 3.8+

```bash
pip install -r requirements.txt
streamlit run app.py
```

**Default login:**
- Username: `admin`
- Password: `admin`

⚠️ **Change the admin password immediately after first login!**

### 📚 Documentation

- [README.md](README.md) - Installation and usage guide
- [CHANGELOG.md](CHANGELOG.md) - Complete feature list and technical details
- [AUTHENTICATION.md](AUTHENTICATION.md) - Multi-user setup
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment options (Streamlit Cloud, Docker)

### 🔒 License

CC BY-NC-SA 4.0 (Non-commercial use)

### 🙏 Acknowledgments

Built with Streamlit, Pandas, Plotly, and streamlit-authenticator.

### 📋 What's Next?

Future versions may include:
- Monte Carlo simulations for probabilistic outcomes
- Tax-aware withdrawal strategies
- Healthcare cost modeling
- Estate planning features
- Mobile-optimized interface

---

**Full changelog:** [CHANGELOG.md](CHANGELOG.md)
**Installation guide:** [README.md](README.md)
