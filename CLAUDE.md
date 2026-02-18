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

There is no test suite or linter configured.

## Architecture

Four-file Python application with clear separation of concerns:

- **`app.py`** — Streamlit UI. Handles authentication flow, sidebar configuration, tabbed account/expense/event editors, projection triggering, and Plotly chart rendering. Uses `st.session_state` for dynamic UI lists.
- **`calculations.py`** — Financial engine. Core function `run_comprehensive_projection()` runs a year-by-year simulation: work income → Social Security → expense inflation → one-time events → planned contributions → flex spending adjustment → deficit withdrawal → investment returns. `analyze_retirement_plan()` produces summary metrics (run-out age, cushion years, status, warnings). Uses Python `@dataclass` for `AccountBucket`, `ExpenseCategory`, and `OneTimeEvent`.
- **`auth_config.py`** — Authentication layer. Manages `credentials.yaml` with bcrypt-hashed passwords via `streamlit-authenticator`. Supports registration, password recovery via recovery codes (SHA-256 hashed) or security questions.
- **`user_data.py`** — SQLite persistence. `UserDataManager` class handles CRUD for four tables: `user_profiles`, `user_accounts`, `user_expenses`, `user_events`. Per-user data isolation by username. Creates default data for new users.

## Data Flow

1. Authentication gates access (`credentials.yaml` + bcrypt)
2. User config loads from SQLite (`user_data.db`)
3. UI inputs build dataclass instances (`AccountBucket`, `ExpenseCategory`, `OneTimeEvent`)
4. `run_comprehensive_projection()` returns a pandas DataFrame with year-by-year results
5. `analyze_retirement_plan()` extracts key metrics from the DataFrame
6. Plotly renders interactive charts; CSV export available

## Key Calculation Logic (calculations.py)

The projection engine processes each year in sequence:
- Work income applies growth rate, stops at `work_end_age`
- Social Security starts at `ss_start_age` with COLA adjustments
- Expenses inflate annually; FLEX categories can be reduced up to `max_flex_reduction` (default 50%) during deficits
- Planned contributions added to accounts (fixed dollar amounts per account)
- Deficits withdraw from accounts in `priority` order
- Investment returns applied to all account balances

## Expense Types

- **CORE**: Essential expenses, cannot be reduced
- **FLEX**: Discretionary expenses, automatically reduced when portfolio is in deficit

## Sensitive Files (git-ignored)

`credentials.yaml`, `user_data.db`, `.streamlit/secrets.toml` — never commit these.
