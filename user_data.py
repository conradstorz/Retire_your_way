"""
User Data Management System

Handles user-specific data persistence using database abstraction.
Supports both SQLite (local) and PostgreSQL (cloud deployment).
Each user has their own set of accounts, expenses, and events.
"""

from typing import Dict, List, Optional
from db_connection import get_db


class UserDataManager:
    """Manages user-specific retirement planning data."""
    
    def __init__(self, db_path: str = "user_data.db"):
        """Initialize the database connection."""
        # db_path parameter kept for backward compatibility but not used
        # Database connection is managed by db_connection module
        self.db = get_db()
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        # User profiles table
        self.db.create_table_if_not_exists('user_profiles', """
            username TEXT PRIMARY KEY,
            current_age INTEGER,
            target_age INTEGER,
            work_end_age INTEGER,
            current_work_income REAL,
            work_income_growth REAL,
            ss_start_age INTEGER,
            ss_monthly_benefit REAL,
            ss_cola REAL,
            inflation_rate REAL,
            max_flex_reduction REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        
        # User accounts table
        self.db.create_table_if_not_exists('user_accounts', """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT NOT NULL,
            balance REAL NOT NULL,
            annual_return REAL NOT NULL,
            contrib_share REAL NOT NULL,
            priority INTEGER NOT NULL,
            FOREIGN KEY (username) REFERENCES user_profiles(username)
        """)
        
        # User expenses table
        self.db.create_table_if_not_exists('user_expenses', """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            category_type TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES user_profiles(username)
        """)
        
        # User events table
        self.db.create_table_if_not_exists('user_events', """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            year INTEGER NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            FOREIGN KEY (username) REFERENCES user_profiles(username)
        """)

        # Account snapshots table (historical performance tracking)
        self.db.create_table_if_not_exists('account_snapshots', """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            account_name TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            amount_contributed REAL NOT NULL,
            total_value REAL NOT NULL,
            FOREIGN KEY (username) REFERENCES user_profiles(username)
        """)

        # Migration: add columns that may not exist in older databases
        self.db.add_column_if_not_exists('user_accounts', 'account_type', 
                                         'TEXT', "'taxable_brokerage'")
        self.db.add_column_if_not_exists('user_accounts', 'planned_contribution', 
                                         'REAL', '0')
        self.db.add_column_if_not_exists('user_accounts', 'continue_post_retirement', 
                                         'INTEGER', '0')
        self.db.add_column_if_not_exists('user_events', 'account_name', 
                                         'TEXT', "''")
        self.db.add_column_if_not_exists('user_profiles', 'ultimate_max_age', 
                                         'INTEGER', '110')
    
    def save_user_profile(self, username: str, profile: Dict):
        """Save or update user profile."""
        self.db.execute_update("""
            INSERT OR REPLACE INTO user_profiles 
            (username, current_age, target_age, ultimate_max_age, work_end_age, current_work_income,
             work_income_growth, ss_start_age, ss_monthly_benefit, ss_cola,
             inflation_rate, max_flex_reduction, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            username,
            profile.get('current_age'),
            profile.get('target_age'),
            profile.get('ultimate_max_age', 110),
            profile.get('work_end_age'),
            profile.get('current_work_income'),
            profile.get('work_income_growth'),
            profile.get('ss_start_age'),
            profile.get('ss_monthly_benefit'),
            profile.get('ss_cola'),
            profile.get('inflation_rate'),
            profile.get('max_flex_reduction')
        ))
    
    def load_user_profile(self, username: str) -> Optional[Dict]:
        """Load user profile."""
        rows = self.db.execute_query("""
            SELECT current_age, target_age, ultimate_max_age, work_end_age, current_work_income,
                   work_income_growth, ss_start_age, ss_monthly_benefit, ss_cola,
                   inflation_rate, max_flex_reduction
            FROM user_profiles WHERE username = ?
        """, (username,))
        
        if rows:
            row = rows[0]
            return {
                'current_age': row[0],
                'target_age': row[1],
                'ultimate_max_age': row[2],
                'work_end_age': row[3],
                'current_work_income': row[4],
                'work_income_growth': row[5],
                'ss_start_age': row[6],
                'ss_monthly_benefit': row[7],
                'ss_cola': row[8],
                'inflation_rate': row[9],
                'max_flex_reduction': row[10]
            }
        return None
    
    def save_user_accounts(self, username: str, accounts: List[Dict]):
        """Save user's investment accounts."""
        # Delete existing accounts
        self.db.execute_update("DELETE FROM user_accounts WHERE username = ?", (username,))

        # Insert new accounts
        params_list = []
        for acc in accounts:
            params_list.append((
                username,
                acc['name'],
                acc['balance'],
                acc['return'],
                acc.get('contrib_share', 0),
                acc['priority'],
                acc.get('account_type', 'taxable_brokerage'),
                acc.get('planned_contribution', 0),
                1 if acc.get('continue_post_retirement', False) else 0
            ))
        
        if params_list:
            self.db.execute_many("""
                INSERT INTO user_accounts
                (username, name, balance, annual_return, contrib_share, priority,
                 account_type, planned_contribution, continue_post_retirement)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, params_list)
    
    def load_user_accounts(self, username: str) -> List[Dict]:
        """Load user's investment accounts."""
        rows = self.db.execute_query("""
            SELECT name, balance, annual_return, contrib_share, priority,
                   account_type, planned_contribution, continue_post_retirement
            FROM user_accounts WHERE username = ? ORDER BY priority
        """, (username,))
        
        accounts = []
        for row in rows:
            accounts.append({
                'name': row[0],
                'balance': row[1],
                'return': row[2],
                'contrib_share': row[3],
                'priority': row[4],
                'account_type': row[5] or 'taxable_brokerage',
                'planned_contribution': row[6] or 0,
                'continue_post_retirement': bool(row[7]) if row[7] is not None else False
            })

        return accounts
    
    def save_user_expenses(self, username: str, expenses: List[Dict]):
        """Save user's expense categories."""
        # Delete existing expenses
        self.db.execute_update("DELETE FROM user_expenses WHERE username = ?", (username,))
        
        # Insert new expenses
        params_list = []
        for exp in expenses:
            params_list.append((
                username,
                exp['name'],
                exp['amount'],
                exp['type']
            ))
        
        if params_list:
            self.db.execute_many("""
                INSERT INTO user_expenses 
                (username, name, amount, category_type)
                VALUES (?, ?, ?, ?)
            """, params_list)
    
    def load_user_expenses(self, username: str) -> List[Dict]:
        """Load user's expense categories."""
        rows = self.db.execute_query("""
            SELECT name, amount, category_type
            FROM user_expenses WHERE username = ?
        """, (username,))
        
        expenses = []
        for row in rows:
            expenses.append({
                'name': row[0],
                'amount': row[1],
                'type': row[2]
            })
        
        return expenses
    
    def save_user_events(self, username: str, events: List[Dict]):
        """Save user's one-time events."""
        # Delete existing events
        self.db.execute_update("DELETE FROM user_events WHERE username = ?", (username,))
        
        # Insert new events
        params_list = []
        for evt in events:
            params_list.append((
                username,
                evt['year'],
                evt['description'],
                evt['amount'],
                evt.get('account_name', '')
            ))
        
        if params_list:
            self.db.execute_many("""
                INSERT INTO user_events 
                (username, year, description, amount, account_name)
                VALUES (?, ?, ?, ?, ?)
            """, params_list)
    
    def load_user_events(self, username: str) -> List[Dict]:
        """Load user's one-time events."""
        rows = self.db.execute_query("""
            SELECT year, description, amount, account_name
            FROM user_events WHERE username = ? ORDER BY year
        """, (username,))
        
        events = []
        for row in rows:
            events.append({
                'year': row[0],
                'description': row[1],
                'amount': row[2],
                'account_name': row[3] if row[3] else 'No Account'
            })
        
        return events
    
    # --- Account Snapshot Methods ---

    def save_snapshot(self, username: str, account_name: str,
                      snapshot_date: str, amount_contributed: float,
                      total_value: float):
        """Record a point-in-time snapshot of an account's value."""
        self.db.execute_update("""
            INSERT INTO account_snapshots
            (username, account_name, snapshot_date, amount_contributed, total_value)
            VALUES (?, ?, ?, ?, ?)
        """, (username, account_name, snapshot_date,
              amount_contributed, total_value))

    def load_snapshots(self, username: str, account_name: str) -> List[Dict]:
        """Load all snapshots for an account, ordered by date."""
        rows = self.db.execute_query("""
            SELECT id, snapshot_date, amount_contributed, total_value
            FROM account_snapshots
            WHERE username = ? AND account_name = ?
            ORDER BY snapshot_date
        """, (username, account_name))

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
        """Delete a single snapshot by ID."""
        self.db.execute_update(
            "DELETE FROM account_snapshots WHERE id = ? AND username = ?",
            (snapshot_id, username))

    def get_latest_snapshot_value(self, username: str,
                                  account_name: str):
        """Return the total_value from the most recent snapshot, or None."""
        rows = self.db.execute_query("""
            SELECT total_value FROM account_snapshots
            WHERE username = ? AND account_name = ?
            ORDER BY snapshot_date DESC LIMIT 1
        """, (username, account_name))
        return rows[0][0] if rows else None

    def rename_account_snapshots(self, username: str, old_name: str,
                                  new_name: str):
        """Update snapshot records when an account is renamed."""
        self.db.execute_update("""
            UPDATE account_snapshots SET account_name = ?
            WHERE username = ? AND account_name = ?
        """, (new_name, username, old_name))

    def user_exists(self, username: str) -> bool:
        """Check if user has saved data."""
        rows = self.db.execute_query("""
            SELECT COUNT(*) FROM user_profiles WHERE username = ?
        """, (username,))
        
        count = rows[0][0] if rows else 0
        return count > 0
    
    def create_default_data_for_user(self, username: str):
        """Create default configuration for a new user."""
        default_profile = {
            'current_age': 45,
            'target_age': 90,
            'ultimate_max_age': 110,
            'work_end_age': 68,
            'current_work_income': 35000,
            'work_income_growth': 0.02,
            'ss_start_age': 68,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.50
        }
        
        default_accounts = [
            {'name': '401k', 'account_type': '401k', 'balance': 2000,
             'return': 0.08, 'contrib_share': 0, 'planned_contribution': 2700, 'priority': 1,
             'continue_post_retirement': False},  # 401k contributions must stop at retirement
            {'name': 'Roth IRA', 'account_type': 'roth_ira', 'balance': 500,
             'return': 0.08, 'contrib_share': 0, 'planned_contribution': 700, 'priority': 2,
             'continue_post_retirement': True},  # Roth IRA can continue indefinitely if you have income
        ]
        
        default_expenses = [
            {'name': 'Housing', 'amount': 12000, 'type': 'CORE'},
            {'name': 'Food', 'amount': 6000, 'type': 'CORE'},
            {'name': 'Healthcare', 'amount': 800, 'type': 'CORE'},
            {'name': 'Transportation', 'amount': 3600, 'type': 'CORE'},
            {'name': 'Travel', 'amount': 1000, 'type': 'FLEX'},
            {'name': 'Entertainment', 'amount': 2000, 'type': 'FLEX'},
        ]
        
        default_events = []
        
        self.save_user_profile(username, default_profile)
        self.save_user_accounts(username, default_accounts)
        self.save_user_expenses(username, default_expenses)
        self.save_user_events(username, default_events)
