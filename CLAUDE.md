# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A multi-user retirement planning web application built with **Streamlit** and **Python**. Replaces spreadsheet-based financial planning with transparent, auditable Python calculations. Licensed under CC BY-NC-SA 4.0.

## Running the Application

```bash
pip install -r requirements.txt
streamlit run app.py
```

Access at `http://localhost:8501`. Default credentials: admin/admin.

For network access: `streamlit run app.py --server.address 0.0.0.0 --server.port 8501`

Docker: `docker build -t retirement-planner . && docker run -p 8501:8501 retirement-planner`

## Running Tests

```bash
pytest test_calculations.py          # Run all tests
pytest test_calculations.py -v       # Verbose output
pytest test_calculations.py -k test_name  # Run specific test
```

No linter is configured.

## Architecture

Multi-file Python application with clear separation of concerns:

**Core Application:**
- **`app.py`** (94KB) — Streamlit UI. Handles authentication flow, sidebar configuration, tabbed account/expense/event editors, projection triggering, and Plotly chart rendering. Uses `st.session_state` for dynamic UI lists.
- **`calculations.py`** (36KB) — Financial engine. Core function `run_comprehensive_projection()` runs a year-by-year simulation: work income → Social Security → expense inflation → one-time events → planned contributions → flex spending adjustment → deficit withdrawal → investment returns → RMDs. `analyze_retirement_plan()` produces summary metrics. Uses Python `@dataclass` for `AccountBucket`, `ExpenseCategory`, and `OneTimeEvent`.

**Authentication & Data Layer:**
- **`auth_db.py`** (13KB) — Database-backed authentication. `AuthManager` class stores user credentials in database (not YAML). Supports bcrypt password hashing, recovery codes (SHA-256), and security questions. Handles cookie-based session management.
- **`auth_config.py`** (9KB) — Legacy authentication wrapper. May be deprecated in favor of `auth_db.py`.
- **`user_data.py`** (19KB) — User data persistence. `UserDataManager` class handles CRUD for four tables: `user_profiles`, `user_accounts`, `user_expenses`, `user_events`. Per-user data isolation by username.

**Database Abstraction:**
- **`db_connection.py`** (10KB) — Database abstraction layer. `DatabaseConnection` class provides unified interface for SQLite (local) and PostgreSQL (cloud). Auto-detects environment via `st.secrets` or `DATABASE_URL`. Handles placeholder conversion (`?` → `%s`) and schema differences.

**Utilities:**
- **`migrate_to_db.py`** (4KB) — Migration script for transitioning from YAML-based auth to database storage.
- **`test_calculations.py`** (86KB) — Comprehensive pytest suite covering projections, RMDs, FLEX spending, historical snapshots. Uses hypothesis for property-based testing.

## Data Flow

1. **Authentication**: `auth_db.AuthManager` validates credentials from database (SQLite local, PostgreSQL cloud via `db_connection`)
2. **User Config Load**: `UserDataManager` loads per-user data from database tables
3. **UI Inputs**: Streamlit sidebar/tabs build dataclass instances (`AccountBucket`, `ExpenseCategory`, `OneTimeEvent`)
4. **Projection**: `run_comprehensive_projection()` returns pandas DataFrame with year-by-year simulation
5. **Analysis**: `analyze_retirement_plan()` extracts summary metrics (run-out age, cushion years, status, warnings)
6. **Visualization**: Plotly renders interactive charts; CSV export available
7. **Persistence**: Changes saved back to database via `UserDataManager`

## Key Calculation Logic (calculations.py)

The projection engine processes each year in sequence:
- Work income applies growth rate, stops at `work_end_age`
- Social Security starts at `ss_start_age` with COLA adjustments
- Expenses inflate annually; FLEX categories can be reduced up to `max_flex_reduction` (default 50%) during deficits
- Planned contributions added to accounts (fixed dollar amounts per account, respects contribution rules like employer matching age limits)
- Required Minimum Distributions (RMDs) enforced for tax-deferred accounts starting at age determined by birth year
- Deficits withdraw from accounts in `priority` order
- Investment returns applied to all account balances
- Historical snapshots can be integrated to show actual vs projected performance

## Core Data Models

**Account Types** (`AccountBucket.account_type`):
- Tax-deferred (Traditional 401k, Traditional IRA) — subject to RMDs, withdrawals taxed
- Tax-free (Roth 401k, Roth IRA) — no RMDs, withdrawals tax-free
- Taxable (Brokerage) — capital gains treatment

**Expense Types** (`ExpenseCategory.category_type`):
- **CORE**: Essential expenses, cannot be reduced
- **FLEX**: Discretionary expenses, automatically reduced up to `max_flex_reduction` during deficits

**Withdrawal Priority**: Accounts are drained by `priority` value (lower = earlier). Typical ordering: taxable → tax-deferred → tax-free.

**Contribution Rules**: Accounts can have contribution limits, employer matching (with age cutoffs), and catch-up contribution eligibility.

## Database Support

**Local Development**: Uses SQLite (`user_data.db`) — no configuration needed.

**Cloud Deployment**: Supports PostgreSQL via:
- Streamlit secrets (`.streamlit/secrets.toml` with `[postgres]` section)
- Environment variable `DATABASE_URL` (Render, Heroku, Railway)

See `db_connection.py` for auto-detection logic and `DEPLOYMENT.md` for setup instructions.

## Sensitive Files (git-ignored)

- `user_data.db` — SQLite database (local only)
- `.streamlit/secrets.toml` — PostgreSQL credentials for cloud deployments
- `credentials.yaml` — Legacy auth file (deprecated, may still exist in old installations)
