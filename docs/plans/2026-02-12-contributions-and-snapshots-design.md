# Planned Contributions and Account Snapshots

## Overview

Two related features that replace the surplus reinvestment model with explicit,
user-controlled contributions and add historical performance tracking per account.

**Code readability requirement:** All code must be as easy to read by humans as
it is by AI. Clear variable names, straightforward control flow, minimal
abstraction. Comments where the "why" isn't obvious.

## Feature 1: Planned Annual Contributions

### What Changes

Each investment account gets:
- An **account type** (401k, Traditional IRA, Roth IRA, Taxable Brokerage)
- A **planned annual contribution** (flat dollar amount)

The old `contribution_share` field is removed from the UI and calculation logic.

### Account Type Contribution Rules

| Account Type        | Contributions Stop        |
|---------------------|---------------------------|
| 401k                | At `work_end_age`         |
| Traditional IRA     | At age 73                 |
| Roth IRA            | Never (assumes earned income in retirement) |
| Taxable Brokerage   | Never                     |

### Projection Engine Changes

**Removed:** Surplus income calculation that distributes excess income to
accounts by `contribution_share` proportions.

**New yearly flow:**

1. Calculate income (work at inflation rate + Social Security with COLA)
2. Calculate inflated expenses (core + flex) and one-time events
3. Calculate surplus = income - (core expenses + full flex expenses + events)
4. Determine how much of planned contributions can be funded:
   - If surplus covers all contributions: contribute fully
   - If surplus is short: reduce flex spending to free up more
   - If still short after max flex reduction: contribute what's possible,
     flag a warning
5. Handle remaining deficit (if expenses still exceed income after flex
   reduction): withdraw from accounts in priority order
6. Apply investment returns to remaining balances

**Contributions are prioritized over flex spending but not over core expenses.**

### Warning Condition

When planned contributions cannot be fully funded even after maximum flex
spending reduction, the app surfaces a warning:

> "Planned contributions to [account] cannot be fully funded starting at
> age [X] -- discretionary spending already at minimum."

This appears in the existing warnings section on the main results page.

## Feature 2: Historical Account Snapshots

### What It Does

Each account has an expandable "History" section in the account editor. Users
record periodic snapshots of their account's actual performance.

### User Enters (per snapshot)

- **Date** (YYYY-MM-DD)
- **Amount contributed** since last snapshot
- **Total account value** at this date

### App Calculates (displayed, not stored)

- **Growth amount** = total_value - previous_total_value - amount_contributed
- **Growth %** = annualized total change including contributions
  `((total_value - prev_total_value) / prev_total_value) * (365 / days_elapsed)`
- **Annualized ROI** = investment-only return, annualized
  `(growth_amount / prev_total_value) * (365 / days_elapsed)`

The first snapshot is the baseline -- calculated fields show "N/A".

### Auto-Update Account Balance

The most recent snapshot's `total_value` automatically becomes the account's
current balance used in projections. One source of truth.

## Data Model Changes

### AccountBucket Dataclass

Add two fields:
- `account_type: str` -- one of "401k", "traditional_ira", "roth_ira",
  "taxable_brokerage"
- `planned_contribution: float` -- annual dollar amount

Remove from calculation logic (keep in DB to avoid migration issues):
- `contribution_share`

### Database: user_accounts Table

Add columns via ALTER TABLE (graceful migration):
- `account_type TEXT DEFAULT 'taxable_brokerage'`
- `planned_contribution REAL DEFAULT 0`

### Database: New account_snapshots Table

```sql
CREATE TABLE IF NOT EXISTS account_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    account_name TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    amount_contributed REAL NOT NULL,
    total_value REAL NOT NULL,
    FOREIGN KEY (username) REFERENCES user_profiles(username)
)
```

### Default Data for New Users

```python
default_accounts = [
    {
        'name': '401k',
        'account_type': '401k',
        'balance': 200000,
        'return': 0.07,
        'planned_contribution': 20000,
        'priority': 1
    },
    {
        'name': 'Roth IRA',
        'account_type': 'roth_ira',
        'balance': 50000,
        'return': 0.07,
        'planned_contribution': 7000,
        'priority': 2
    },
]
```

## UI Changes

### Account Editor Tab

Per account:
- **Account type** dropdown (401k, Traditional IRA, Roth IRA, Taxable Brokerage)
- **Planned annual contribution** dollar input
- **Remove** contribution share field
- **Historical Snapshots** expandable section:
  - Table showing all snapshots: date, contributed, growth, growth %, ROI %, total value
  - "Add Snapshot" form: date picker, contributed amount, total value

### Projection Results

- Contributions shown as a distinct column/line in the results table and chart
- Per-account contributions visible in the detailed breakdown

### Warnings

- New warning type for underfunded contributions
