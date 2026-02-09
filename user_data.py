"""
User Data Management System

Handles user-specific data persistence using SQLite.
Each user has their own set of accounts, expenses, and events.
"""

import sqlite3
import json
from typing import Dict, List, Optional
from pathlib import Path
import hashlib


class UserDataManager:
    """Manages user-specific retirement planning data."""
    
    def __init__(self, db_path: str = "user_data.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
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
            )
        """)
        
        # User accounts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                balance REAL NOT NULL,
                annual_return REAL NOT NULL,
                contrib_share REAL NOT NULL,
                priority INTEGER NOT NULL,
                FOREIGN KEY (username) REFERENCES user_profiles(username)
            )
        """)
        
        # User expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                category_type TEXT NOT NULL,
                FOREIGN KEY (username) REFERENCES user_profiles(username)
            )
        """)
        
        # User events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                year INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (username) REFERENCES user_profiles(username)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_user_profile(self, username: str, profile: Dict):
        """Save or update user profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_profiles 
            (username, current_age, target_age, work_end_age, current_work_income,
             work_income_growth, ss_start_age, ss_monthly_benefit, ss_cola,
             inflation_rate, max_flex_reduction, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            username,
            profile.get('current_age'),
            profile.get('target_age'),
            profile.get('work_end_age'),
            profile.get('current_work_income'),
            profile.get('work_income_growth'),
            profile.get('ss_start_age'),
            profile.get('ss_monthly_benefit'),
            profile.get('ss_cola'),
            profile.get('inflation_rate'),
            profile.get('max_flex_reduction')
        ))
        
        conn.commit()
        conn.close()
    
    def load_user_profile(self, username: str) -> Optional[Dict]:
        """Load user profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT current_age, target_age, work_end_age, current_work_income,
                   work_income_growth, ss_start_age, ss_monthly_benefit, ss_cola,
                   inflation_rate, max_flex_reduction
            FROM user_profiles WHERE username = ?
        """, (username,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'current_age': row[0],
                'target_age': row[1],
                'work_end_age': row[2],
                'current_work_income': row[3],
                'work_income_growth': row[4],
                'ss_start_age': row[5],
                'ss_monthly_benefit': row[6],
                'ss_cola': row[7],
                'inflation_rate': row[8],
                'max_flex_reduction': row[9]
            }
        return None
    
    def save_user_accounts(self, username: str, accounts: List[Dict]):
        """Save user's investment accounts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing accounts
        cursor.execute("DELETE FROM user_accounts WHERE username = ?", (username,))
        
        # Insert new accounts
        for acc in accounts:
            cursor.execute("""
                INSERT INTO user_accounts 
                (username, name, balance, annual_return, contrib_share, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                username,
                acc['name'],
                acc['balance'],
                acc['return'],
                acc['contrib_share'],
                acc['priority']
            ))
        
        conn.commit()
        conn.close()
    
    def load_user_accounts(self, username: str) -> List[Dict]:
        """Load user's investment accounts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, balance, annual_return, contrib_share, priority
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
                'priority': row[4]
            })
        
        return accounts
    
    def save_user_expenses(self, username: str, expenses: List[Dict]):
        """Save user's expense categories."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing expenses
        cursor.execute("DELETE FROM user_expenses WHERE username = ?", (username,))
        
        # Insert new expenses
        for exp in expenses:
            cursor.execute("""
                INSERT INTO user_expenses 
                (username, name, amount, category_type)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                exp['name'],
                exp['amount'],
                exp['type']
            ))
        
        conn.commit()
        conn.close()
    
    def load_user_expenses(self, username: str) -> List[Dict]:
        """Load user's expense categories."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, amount, category_type
            FROM user_expenses WHERE username = ?
        """, (username,))
        
        rows = cursor.fetchall()
        conn.close()
        
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete existing events
        cursor.execute("DELETE FROM user_events WHERE username = ?", (username,))
        
        # Insert new events
        for evt in events:
            cursor.execute("""
                INSERT INTO user_events 
                (username, year, description, amount)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                evt['year'],
                evt['description'],
                evt['amount']
            ))
        
        conn.commit()
        conn.close()
    
    def load_user_events(self, username: str) -> List[Dict]:
        """Load user's one-time events."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT year, description, amount
            FROM user_events WHERE username = ? ORDER BY year
        """, (username,))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                'year': row[0],
                'description': row[1],
                'amount': row[2]
            })
        
        return events
    
    def user_exists(self, username: str) -> bool:
        """Check if user has saved data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM user_profiles WHERE username = ?
        """, (username,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def create_default_data_for_user(self, username: str):
        """Create default configuration for a new user."""
        default_profile = {
            'current_age': 45,
            'target_age': 90,
            'work_end_age': 65,
            'current_work_income': 80000,
            'work_income_growth': 0.02,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.50
        }
        
        default_accounts = [
            {'name': '401k', 'balance': 200000, 'return': 0.07, 'contrib_share': 0.80, 'priority': 1},
            {'name': 'Roth IRA', 'balance': 50000, 'return': 0.07, 'contrib_share': 0.20, 'priority': 2},
        ]
        
        default_expenses = [
            {'name': 'Housing', 'amount': 24000, 'type': 'CORE'},
            {'name': 'Food', 'amount': 12000, 'type': 'CORE'},
            {'name': 'Healthcare', 'amount': 8000, 'type': 'CORE'},
            {'name': 'Transportation', 'amount': 6000, 'type': 'CORE'},
            {'name': 'Travel', 'amount': 10000, 'type': 'FLEX'},
            {'name': 'Entertainment', 'amount': 5000, 'type': 'FLEX'},
        ]
        
        default_events = []
        
        self.save_user_profile(username, default_profile)
        self.save_user_accounts(username, default_accounts)
        self.save_user_expenses(username, default_expenses)
        self.save_user_events(username, default_events)
