"""
Authentication System with Database Storage

This module manages user credentials and authentication using database storage
instead of YAML files. Supports both SQLite (local) and PostgreSQL (cloud).
Passwords are hashed using bcrypt for security.
"""

import secrets
import hashlib
from typing import Optional, Dict
import streamlit_authenticator as stauth
from db_connection import get_db


class AuthManager:
    """Manages user authentication with database persistence."""
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.db = get_db()
        self.init_auth_tables()
        self._ensure_admin_exists()
    
    def init_auth_tables(self):
        """Create authentication tables if they don't exist."""
        # Users table for authentication
        self.db.create_table_if_not_exists('users', """
            username TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            recovery_code_hash TEXT,
            security_question TEXT,
            security_answer_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """)
        
        # Cookie configuration (single row)
        self.db.create_table_if_not_exists('auth_config', """
            id INTEGER PRIMARY KEY DEFAULT 1,
            cookie_name TEXT DEFAULT 'retirement_planner_auth',
            cookie_key TEXT,
            cookie_expiry_days INTEGER DEFAULT 30,
            CHECK (id = 1)
        """)
        
        # Initialize cookie config if not exists
        rows = self.db.execute_query("SELECT cookie_key FROM auth_config WHERE id = 1")
        if not rows:
            cookie_key = secrets.token_urlsafe(32)
            self.db.execute_update(
                "INSERT INTO auth_config (id, cookie_key) VALUES (1, ?)",
                (cookie_key,)
            )
    
    def _ensure_admin_exists(self):
        """Create default admin account if no users exist."""
        rows = self.db.execute_query("SELECT COUNT(*) FROM users")
        user_count = rows[0][0] if rows else 0
        
        if user_count == 0:
            # Create default admin account
            hashed_password = stauth.Hasher.hash('admin')
            self.db.execute_update("""
                INSERT INTO users (username, name, email, password_hash)
                VALUES (?, ?, ?, ?)
            """, ('admin', 'Administrator', 'admin@example.com', hashed_password))
            print("⚠️  Created default admin account (username: admin, password: admin)")
            print("⚠️  IMPORTANT: Change the admin password immediately!")
    
    def get_credentials_config(self) -> Dict:
        """
        Get credentials in the format expected by streamlit-authenticator.
        
        Returns:
            Dictionary with credentials, cookie, and preauthorized config
        """
        # Load all users
        rows = self.db.execute_query("""
            SELECT username, name, email, password_hash 
            FROM users
        """)
        
        usernames = {}
        for row in rows:
            usernames[row[0]] = {
                'name': row[1],
                'email': row[2],
                'password': row[3]
            }
        
        # Load cookie config
        cookie_rows = self.db.execute_query("""
            SELECT cookie_name, cookie_key, cookie_expiry_days 
            FROM auth_config WHERE id = 1
        """)
        
        if cookie_rows:
            cookie_name, cookie_key, cookie_expiry = cookie_rows[0]
        else:
            # Fallback defaults
            cookie_name = 'retirement_planner_auth'
            cookie_key = secrets.token_urlsafe(32)
            cookie_expiry = 30
        
        return {
            'credentials': {
                'usernames': usernames
            },
            'cookie': {
                'name': cookie_name,
                'key': cookie_key,
                'expiry_days': cookie_expiry
            },
            'preauthorized': {
                'emails': []
            }
        }
    
    def register_user(self, username: str, name: str, password: str, email: str) -> bool:
        """
        Register a new user.
        
        Args:
            username: Unique username for login
            name: Full name of the user
            password: Plain text password (will be hashed)
            email: User's email address
        
        Returns:
            bool: True if successful, False if username already exists
        """
        # Check if username already exists
        rows = self.db.execute_query(
            "SELECT COUNT(*) FROM users WHERE username = ?",
            (username,)
        )
        if rows and rows[0][0] > 0:
            return False
        
        # Hash the password
        hashed_password = stauth.Hasher.hash(password)
        
        # Insert new user
        self.db.execute_update("""
            INSERT INTO users (username, name, email, password_hash)
            VALUES (?, ?, ?, ?)
        """, (username, name, email, hashed_password))
        
        return True
    
    def change_password(self, username: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            username: Username to change password for
            new_password: New plain text password (will be hashed)
        
        Returns:
            bool: True if successful, False if user doesn't exist
        """
        # Check if user exists
        rows = self.db.execute_query(
            "SELECT COUNT(*) FROM users WHERE username = ?",
            (username,)
        )
        if not rows or rows[0][0] == 0:
            return False
        
        # Hash the new password
        hashed_password = stauth.Hasher.hash(new_password)
        
        # Update password
        self.db.execute_update("""
            UPDATE users 
            SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (hashed_password, username))
        
        return True
    
    def generate_recovery_code(self) -> str:
        """Generate a secure 16-character recovery code."""
        return secrets.token_urlsafe(12)[:16].upper()
    
    def hash_recovery_code(self, code: str) -> str:
        """Hash a recovery code for secure storage."""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def add_recovery_code(self, username: str, recovery_code: str) -> bool:
        """
        Add a hashed recovery code to a user's account.
        
        Args:
            username: Username to add recovery code for
            recovery_code: Plain text recovery code (will be hashed)
        
        Returns:
            bool: True if successful, False if user doesn't exist
        """
        # Check if user exists
        rows = self.db.execute_query(
            "SELECT COUNT(*) FROM users WHERE username = ?",
            (username,)
        )
        if not rows or rows[0][0] == 0:
            return False
        
        # Hash and store the recovery code
        hashed_code = self.hash_recovery_code(recovery_code)
        self.db.execute_update("""
            UPDATE users 
            SET recovery_code_hash = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (hashed_code, username))
        
        return True
    
    def verify_recovery_code(self, username: str, recovery_code: str) -> bool:
        """
        Verify a recovery code for a user.
        
        Args:
            username: Username to verify recovery code for
            recovery_code: Plain text recovery code to verify
        
        Returns:
            bool: True if code matches, False otherwise
        """
        rows = self.db.execute_query(
            "SELECT recovery_code_hash FROM users WHERE username = ?",
            (username,)
        )
        
        if not rows or not rows[0][0]:
            return False
        
        stored_hash = rows[0][0]
        return self.hash_recovery_code(recovery_code) == stored_hash
    
    def add_security_question(self, username: str, question: str, answer: str) -> bool:
        """
        Add a security question and answer to a user's account.
        
        Args:
            username: Username to add security question for
            question: Security question text
            answer: Plain text answer (will be hashed)
        
        Returns:
            bool: True if successful, False if user doesn't exist
        """
        # Check if user exists
        rows = self.db.execute_query(
            "SELECT COUNT(*) FROM users WHERE username = ?",
            (username,)
        )
        if not rows or rows[0][0] == 0:
            return False
        
        # Hash the answer
        answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        
        # Update security question and answer
        self.db.execute_update("""
            UPDATE users 
            SET security_question = ?, security_answer_hash = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (question, answer_hash, username))
        
        return True
    
    def get_security_question(self, username: str) -> Optional[str]:
        """
        Get the security question for a user.
        
        Args:
            username: Username to get security question for
        
        Returns:
            str: Security question, or None if not set
        """
        rows = self.db.execute_query(
            "SELECT security_question FROM users WHERE username = ?",
            (username,)
        )
        
        if rows and rows[0][0]:
            return rows[0][0]
        return None
    
    def verify_security_answer(self, username: str, answer: str) -> bool:
        """
        Verify a security question answer.
        
        Args:
            username: Username to verify answer for
            answer: Plain text answer to verify
        
        Returns:
            bool: True if answer matches, False otherwise
        """
        rows = self.db.execute_query(
            "SELECT security_answer_hash FROM users WHERE username = ?",
            (username,)
        )
        
        if not rows or not rows[0][0]:
            return False
        
        stored_hash = rows[0][0]
        answer_hash = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
        return answer_hash == stored_hash
    
    def get_user_email(self, username: str) -> Optional[str]:
        """Get a user's email address."""
        rows = self.db.execute_query(
            "SELECT email FROM users WHERE username = ?",
            (username,)
        )
        
        if rows:
            return rows[0][0]
        return None
    
    def update_user_email(self, username: str, email: str) -> bool:
        """Update a user's email address."""
        rows = self.db.execute_query(
            "SELECT COUNT(*) FROM users WHERE username = ?",
            (username,)
        )
        if not rows or rows[0][0] == 0:
            return False
        
        self.db.execute_update("""
            UPDATE users 
            SET email = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        """, (email, username))
        
        return True


# Helper functions for compatibility with existing code

def reset_password_with_recovery(username: str, recovery_code: str, new_password: str) -> bool:
    """
    Reset password using recovery code.
    
    Args:
        username: Username to reset password for
        recovery_code: Plain text recovery code
        new_password: New plain text password (will be hashed)
    
    Returns:
        bool: True if successful, False otherwise
    """
    auth_manager = get_auth_manager()
    
    # Verify recovery code
    if not auth_manager.verify_recovery_code(username, recovery_code):
        return False
    
    # Change password
    return auth_manager.change_password(username, new_password)


def reset_password_with_security_question(username: str, answer: str, new_password: str) -> bool:
    """
    Reset password using security question answer.
    
    Args:
        username: Username to reset password for
        answer: Plain text answer to security question
        new_password: New plain text password (will be hashed)
    
    Returns:
        bool: True if successful, False otherwise
    """
    auth_manager = get_auth_manager()
    
    # Verify security answer
    if not auth_manager.verify_security_answer(username, answer):
        return False
    
    # Change password
    return auth_manager.change_password(username, new_password)


# Global auth manager instance
_auth_manager = None


def get_auth_manager() -> AuthManager:
    """Get the global authentication manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
