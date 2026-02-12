# Contributions and Snapshots Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace surplus reinvestment with explicit planned contributions per account, add historical snapshot tracking, and add account type contribution rules.

**Architecture:** Four-file changes: user_data.py (schema + CRUD), calculations.py (data model + engine), app.py (UI). No new files. SQLite migration via ALTER TABLE. No test suite exists.

**Tech Stack:** Python, Streamlit, SQLite, Plotly, pandas

---

### Task 1: Database Schema Migration

**Files:**
- Modify: `user_data.py:23-86` (init_database method)

**Step 1: Add new columns and table to init_database()**

Add ALTER TABLE statements (wrapped in try/except for idempotency) to add
`account_type` and `planned_contribution` to `user_accounts`. Add CREATE TABLE
for `account_snapshots`.

```python
# After existing CREATE TABLE statements, add migration for new columns:

# Migration: add account_type and planned_contribution to user_accounts
try:
    cursor.execute("ALTER TABLE user_accounts ADD COLUMN account_type TEXT DEFAULT 'taxable_brokerage'")
except sqlite3.OperationalError:
    pass  # Column already exists

try:
    cursor.execute("ALTER TABLE user_accounts ADD COLUMN planned_contribution REAL DEFAULT 0")
except sqlite3.OperationalError:
    pass  # Column already exists

# Account snapshots table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS account_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        account_name TEXT NOT NULL,
        snapshot_date TEXT NOT NULL,
        amount_contributed REAL NOT NULL,
        total_value REAL NOT NULL,
        FOREIGN KEY (username) REFERENCES user_profiles(username)
    )
""")
```

**Step 2: Verify by running the app briefly**

Run: `streamlit run app.py` (manual check -- no test suite)

---

### Task 2: Update Account CRUD Methods

**Files:**
- Modify: `user_data.py:146-195` (save/load user_accounts)
- Modify: `user_data.py:305-339` (create_default_data_for_user)

**Step 1: Update save_user_accounts to include new fields**

```python
def save_user_accounts(self, username: str, accounts: List[Dict]):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_accounts WHERE username = ?", (username,))
    for acc in accounts:
        cursor.execute("""
            INSERT INTO user_accounts
            (username, name, balance, annual_return, contrib_share, priority,
             account_type, planned_contribution)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username,
            acc['name'],
            acc['balance'],
            acc['return'],
            acc.get('contrib_share', 0),
            acc['priority'],
            acc.get('account_type', 'taxable_brokerage'),
            acc.get('planned_contribution', 0)
        ))
    conn.commit()
    conn.close()
```

**Step 2: Update load_user_accounts to return new fields**

```python
def load_user_accounts(self, username: str) -> List[Dict]:
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, balance, annual_return, contrib_share, priority,
               account_type, planned_contribution
        FROM user_accounts WHERE username = ? ORDER BY priority
    """, (username,))
    rows = cursor.fetchall()
    conn.close()
    accounts = []
    for row in rows:
        accounts.append({
            'name': row[0],
            'balance': row[1],
            'return': row[2],
            'contrib_share': row[3],
            'priority': row[4],
            'account_type': row[5] or 'taxable_brokerage',
            'planned_contribution': row[6] or 0
        })
    return accounts
```

**Step 3: Update default data for new users**

```python
default_accounts = [
    {
        'name': '401k',
        'account_type': '401k',
        'balance': 200000,
        'return': 0.07,
        'contrib_share': 0,
        'planned_contribution': 20000,
        'priority': 1
    },
    {
        'name': 'Roth IRA',
        'account_type': 'roth_ira',
        'balance': 50000,
        'return': 0.07,
        'contrib_share': 0,
        'planned_contribution': 7000,
        'priority': 2
    },
]
```

---

### Task 3: Add Snapshot CRUD Methods

**Files:**
- Modify: `user_data.py` (add new methods before user_exists)

**Step 1: Add save, load, and delete snapshot methods**

```python
def save_snapshot(self, username: str, account_name: str,
                  snapshot_date: str, amount_contributed: float,
                  total_value: float):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO account_snapshots
        (username, account_name, snapshot_date, amount_contributed, total_value)
        VALUES (?, ?, ?, ?, ?)
    """, (username, account_name, snapshot_date,
          amount_contributed, total_value))
    conn.commit()
    conn.close()

def load_snapshots(self, username: str, account_name: str) -> List[Dict]:
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, snapshot_date, amount_contributed, total_value
        FROM account_snapshots
        WHERE username = ? AND account_name = ?
        ORDER BY snapshot_date
    """, (username, account_name))
    rows = cursor.fetchall()
    conn.close()
    snapshots = []
    for row in rows:
        snapshots.append({
            'id': row[0],
            'date': row[1],
            'contributed': row[2],
            'total_value': row[3]
        })
    return snapshots

def delete_snapshot(self, username: str, snapshot_id: int):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM account_snapshots WHERE id = ? AND username = ?",
        (snapshot_id, username))
    conn.commit()
    conn.close()

def get_latest_snapshot_value(self, username: str,
                               account_name: str) -> float | None:
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT total_value FROM account_snapshots
        WHERE username = ? AND account_name = ?
        ORDER BY snapshot_date DESC LIMIT 1
    """, (username, account_name))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None
```

---

### Task 4: Update Calculations Data Model

**Files:**
- Modify: `calculations.py:25-33` (AccountBucket dataclass)

**Step 1: Update AccountBucket**

Replace contribution_share with account_type and planned_contribution:

```python
@dataclass
class AccountBucket:
    """Represents an investment account (401k, Roth IRA, etc.)"""
    name: str
    balance: float
    annual_return: float
    priority: int  # Withdrawal order (1 = first)
    account_type: str  # '401k', 'traditional_ira', 'roth_ira', 'taxable_brokerage'
    planned_contribution: float  # Annual dollar amount to contribute
```

**Step 2: Add contribution rules constant**

```python
# When contributions must stop, by account type.
# None means contributions never stop.
CONTRIBUTION_STOP_RULES = {
    '401k': 'work_end_age',
    'traditional_ira': 73,
    'roth_ira': None,
    'taxable_brokerage': None,
}
```

**Step 3: Add helper function**

```python
def can_contribute(account_type: str, age: int, work_end_age: int) -> bool:
    """Check if an account type is eligible for contributions at this age."""
    rule = CONTRIBUTION_STOP_RULES.get(account_type)
    if rule is None:
        return True
    if rule == 'work_end_age':
        return age < work_end_age
    return age < rule
```

---

### Task 5: Rewrite Projection Engine

**Files:**
- Modify: `calculations.py:51-278` (run_comprehensive_projection)

**Step 1: Update function signature**

Remove `work_income_growth` parameter (income now grows at inflation_rate).
The `contribution_share` references on AccountBucket are gone.

**Step 2: Rewrite the yearly loop**

The new flow for each year:

1. Calculate income (work grows at inflation rate, SS with COLA)
2. Calculate inflated expenses (core + flex) and events
3. Calculate total planned contributions for eligible accounts
4. Determine funding: surplus = income - core_expenses - flex_expenses - events
5. If surplus >= contributions: fund them fully
6. If surplus < contributions: reduce flex to free up money
7. If still short after max flex reduction: fund what we can, flag warning
8. If deficit remains after contributions: withdraw from accounts
9. Apply investment returns

**Step 3: Update analyze_retirement_plan**

Add new warning type for underfunded contributions. The projection DataFrame
will include a `contribution_shortfall` column that analyze can check.

---

### Task 6: Update Account Editor UI

**Files:**
- Modify: `app.py:499-569` (accounts tab)

**Step 1: Replace contribution_share with account_type and planned_contribution**

Per account expander:
- Add account_type selectbox (401k, Traditional IRA, Roth IRA, Taxable Brokerage)
- Add planned_contribution number_input
- Remove contribution_share slider
- Remove contribution_share validation warning at bottom

**Step 2: Update "Add Account" defaults**

New account gets `account_type: 'taxable_brokerage'` and
`planned_contribution: 0`.

**Step 3: Update caption text**

Remove reference to "surplus is reinvested by contribution share."

---

### Task 7: Add Snapshot UI

**Files:**
- Modify: `app.py` (inside accounts tab, after each account's fields)

**Step 1: Add snapshot display and entry form per account**

Inside each account's expander, after the existing fields, add:
- Subheader "History"
- Display snapshot table with calculated columns
- "Add Snapshot" form with date, contributed, total_value inputs
- Auto-update account balance when snapshot is added

The snapshot calculation logic:
```python
from datetime import datetime

def calculate_snapshot_metrics(snapshots):
    """Add calculated columns to a list of snapshot dicts."""
    results = []
    for i, snap in enumerate(snapshots):
        row = dict(snap)
        if i == 0:
            row['growth'] = None
            row['growth_pct'] = None
            row['roi_pct'] = None
        else:
            prev = snapshots[i - 1]
            growth = snap['total_value'] - prev['total_value'] - snap['contributed']
            days = (datetime.strptime(snap['date'], '%Y-%m-%d')
                    - datetime.strptime(prev['date'], '%Y-%m-%d')).days
            annualize = 365 / days if days > 0 else 1
            prev_val = prev['total_value']
            if prev_val > 0:
                total_change = snap['total_value'] - prev_val
                row['growth'] = growth
                row['growth_pct'] = (total_change / prev_val) * annualize * 100
                row['roi_pct'] = (growth / prev_val) * annualize * 100
            else:
                row['growth'] = growth
                row['growth_pct'] = None
                row['roi_pct'] = None
        results.append(row)
    return results
```

---

### Task 8: Wire Up Projection with New Model

**Files:**
- Modify: `app.py:674-727` (projection building and running)

**Step 1: Update AccountBucket construction**

```python
accounts = [
    AccountBucket(
        name=acc['name'],
        balance=acc['balance'],
        annual_return=acc['return'],
        priority=acc['priority'],
        account_type=acc.get('account_type', 'taxable_brokerage'),
        planned_contribution=acc.get('planned_contribution', 0)
    )
    for acc in st.session_state.accounts
]
```

**Step 2: Update run_comprehensive_projection call**

Remove `work_income_growth` parameter (now uses inflation_rate internally).

---

### Task 9: Final Cleanup and Commit

**Step 1: Remove legacy functions from calculations.py**

The functions after line 353 (calculate_future_value, adjust_for_inflation,
calculate_required_savings, project_retirement_balance,
calculate_safe_withdrawal_rate, calculate_retirement_readiness) are marked
as legacy and no longer used. Remove them.

**Step 2: Update the app.py description text**

Update the intro text and any references to surplus reinvestment.

**Step 3: Commit all changes**

```bash
git add user_data.py calculations.py app.py docs/
git commit -m "feat: planned contributions, account types, and historical snapshots"
```
