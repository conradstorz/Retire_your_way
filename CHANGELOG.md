# Changelog

All notable changes to the Retirement Planning Application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0] - 2026-02-16

### Initial Release

A comprehensive multi-user retirement planning application with transparent, auditable Python calculations replacing spreadsheet-based planning.

### Core Features

#### Authentication & User Management
- **Multi-user authentication system** with bcrypt-hashed passwords
- **User registration** with email validation
- **Password recovery** via SHA-256 hashed recovery codes
- **Security question recovery** as alternative password reset method
- **Per-user data isolation** with SQLite persistence
- **Session management** with configurable cookie expiry
- Display of registered account count on login page

#### Account Management
- **Multiple account types** with type-specific rules:
  - 401(k) - contributions stop at work end age
  - Traditional IRA - contributions stop at age 73
  - Roth IRA - contributions never stop (assumes earned income)
  - Taxable Brokerage - contributions never stop
- **Planned annual contributions** per account (flat dollar amounts)
- **Post-retirement contribution options** for eligible accounts
- **Withdrawal priority ordering** for deficit handling
- **Historical account snapshots** with performance tracking:
  - Date-stamped balance records
  - Contribution tracking between snapshots
  - Calculated growth amounts and percentages
  - Annualized ROI calculations
  - Auto-update account balance from latest snapshot
- **Investment return modeling** per account

#### Financial Calculations
- **Comprehensive year-by-year projection engine**:
  - Work income with annual growth rate (stops at retirement)
  - Social Security with COLA adjustments (starts at user-specified age)
  - Inflation-adjusted expenses
  - One-time portfolio events (withdrawals/additions)
  - Surplus reinvestment and deficit withdrawal logic
  - Investment returns on remaining balances
- **Required Minimum Distributions (RMDs)**:
  - Automatic RMD calculations for Traditional IRAs and 401(k)s
  - IRS Uniform Lifetime Table implementation
  - RMD start age 73 (current tax law)
- **CORE vs FLEX spending categories**:
  - CORE expenses cannot be reduced (essentials)
  - FLEX expenses automatically reduce up to 50% during deficits
  - Warning system when deficit persists after flex reduction
- **Withdrawal-funded contributions**: When income is insufficient, contributions are funded by withdrawing from accounts in priority order
- **Conservative calculation approach**: Applies investment returns only after all transactions complete

#### Analysis & Reporting
- **Plan analysis metrics**:
  - Portfolio run-out age (when money depletes)
  - Cushion years (buffer beyond life expectancy)
  - Plan status (Excellent/Good/Adequate/At Risk/Concerning)
  - Target age analysis (balance at chosen milestone)
- **Sustainable withdrawal guidance**: 4% rule comparison to current spending level
- **Sanity Checks tab**: Validates account balances vs. contributions
- **Comprehensive warnings system**:
  - Underfunded contribution alerts
  - Persistent deficit warnings
  - Portfolio depletion notifications
  - Age mismatch warnings (retirement before Social Security)
  - Contribution feasibility checks

#### User Interface
- **Modern Streamlit web interface** with responsive layout
- **Tabbed navigation**:
  - Dashboard: Key metrics and summary
  - Profile: Personal information and assumptions
  - Accounts: Investment account management with snapshots
  - Expenses: CORE and FLEX spending categories
  - Events: One-time portfolio transactions
  - Projections: Detailed year-by-year results
  - Sanity Checks: Data validation
- **Interactive Plotly visualizations**:
  - Combined account balance projections
  - Per-account balance breakdowns
  - Expense vs income tracking
- **Dynamic expander sections** with persistent state
- **CSV export** for detailed projection data
- **Real-time calculation updates** as inputs change

#### Data Persistence
- **SQLite database** (user_data.db) with four tables:
  - `user_profiles`: Personal information and assumptions
  - `user_accounts`: Investment accounts with types and contributions
  - `user_expenses`: CORE and FLEX spending categories
  - `user_events`: One-time portfolio transactions
  - `account_snapshots`: Historical performance tracking
- **Automatic default data** for new users (example 401k + Roth IRA)
- **Graceful schema migration** with ALTER TABLE support

#### Documentation
- Comprehensive README with installation and usage instructions
- AUTHENTICATION.md with multi-user setup guide
- DEPLOYMENT.md with Streamlit Cloud and Docker instructions
- CLAUDE.md with project architecture and development guidance
- Detailed code comments throughout codebase
- CC BY-NC-SA 4.0 license (non-commercial use)

### Technical Details
- **Python 3.8+** required
- **Key dependencies**:
  - streamlit 1.31.0+
  - streamlit-authenticator
  - pandas
  - plotly
  - PyYAML
  - bcrypt
- **Four-file architecture**:
  - `app.py`: Streamlit UI and orchestration
  - `calculations.py`: Financial projection engine
  - `auth_config.py`: Authentication management
  - `user_data.py`: SQLite persistence layer
- **Dataclass-based models** for type safety (AccountBucket, ExpenseCategory, OneTimeEvent)
- **Security**: Bcrypt password hashing, SHA-256 recovery codes, credentials isolation

### Known Limitations
- No test suite (manual validation only)
- No linter configured
- Single-file credentials.yaml (not distributed system ready)
- No Monte Carlo simulations (deterministic projections only)
- No tax calculations (pre-tax planning only)

### Default Credentials
- **Username**: admin
- **Password**: admin
- **⚠️ SECURITY**: Change admin password immediately after first login

---

## Future Roadmap

Future versions may include:
- Monte Carlo simulation for probabilistic outcomes
- Tax-aware withdrawal strategies
- Healthcare cost modeling (Medicare, premiums, out-of-pocket)
- Estate planning features
- Asset allocation recommendations
- Inflation scenario modeling
- Multiple projection scenarios with side-by-side comparison
- Email notifications for plan warnings
- PDF report generation
- Mobile-optimized interface

---

[0.9.0]: https://github.com/conradstorz/Retire_your_way/releases/tag/v0.9.0
