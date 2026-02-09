"""
Authentication Configuration

This module manages user credentials and authentication setup.
Passwords are hashed using bcrypt for security.
"""

import yaml
import streamlit_authenticator as stauth
from pathlib import Path
import secrets
import hashlib


def init_credentials_file(filepath: str = "credentials.yaml"):
    """
    Create initial credentials file if it doesn't exist.
    
    Default admin account:
    - Username: admin
    - Password: admin (CHANGE THIS IMMEDIATELY!)
    """
    if Path(filepath).exists():
        return
    
    # Create hashed password for default admin account
    hashed_password = stauth.Hasher.hash('admin')
    
    credentials = {
        'credentials': {
            'usernames': {
                'admin': {
                    'name': 'Administrator',
                    'password': hashed_password,
                    'email': 'admin@example.com'
                }
            }
        },
        'cookie': {
            'name': 'retirement_planner_auth',
            'key': 'retirement_planning_secret_key_change_this',
            'expiry_days': 30
        },
        'preauthorized': {
            'emails': []
        }
    }
    
    with open(filepath, 'w') as file:
        yaml.dump(credentials, file, default_flow_style=False)
    
    print(f"Created {filepath} with default admin account.")
    print("⚠️  IMPORTANT: Change the admin password immediately!")


def load_credentials(filepath: str = "credentials.yaml"):
    """Load credentials from YAML file."""
    init_credentials_file(filepath)
    
    with open(filepath, 'r') as file:
        config = yaml.safe_load(file)
    
    return config


def save_credentials(config: dict, filepath: str = "credentials.yaml"):
    """Save credentials to YAML file."""
    with open(filepath, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)


def register_new_user(username: str, name: str, password: str, email: str, filepath: str = "credentials.yaml"):
    """
    Register a new user in the credentials file.
    
    Args:
        username: Unique username for login
        name: Full name of the user
        password: Plain text password (will be hashed)
        email: User's email address
        filepath: Path to credentials file
    
    Returns:
        bool: True if successful, False if username already exists
    """
    config = load_credentials(filepath)
    
    # Check if username already exists
    if username in config['credentials']['usernames']:
        return False
    
    # Hash the password
    hashed_password = stauth.Hasher.hash(password)
    
    # Add new user
    config['credentials']['usernames'][username] = {
        'name': name,
        'password': hashed_password,
        'email': email
    }
    
    # Save updated credentials
    save_credentials(config, filepath)
    
    return True


def change_password(username: str, new_password: str, filepath: str = "credentials.yaml"):
    """
    Change a user's password.
    
    Args:
        username: Username to change password for
        new_password: New plain text password (will be hashed)
        filepath: Path to credentials file
    
    Returns:
        bool: True if successful, False if user doesn't exist
    """
    config = load_credentials(filepath)
    
    if username not in config['credentials']['usernames']:
        return False
    
    # Hash the new password
    hashed_password = stauth.Hasher.hash(new_password)
    
    # Update password
    config['credentials']['usernames'][username]['password'] = hashed_password
    
    # Save updated credentials
    save_credentials(config, filepath)
    
    return True


def generate_recovery_code():
    """Generate a secure 16-character recovery code."""
    return secrets.token_urlsafe(12)[:16].upper()


def hash_recovery_code(code: str) -> str:
    """Hash a recovery code for secure storage."""
    return hashlib.sha256(code.encode()).hexdigest()


def add_recovery_code(username: str, recovery_code: str, filepath: str = "credentials.yaml"):
    """
    Add a hashed recovery code to a user's account.
    
    Args:
        username: Username to add recovery code for
        recovery_code: Plain text recovery code (will be hashed)
        filepath: Path to credentials file
    
    Returns:
        bool: True if successful, False if user doesn't exist
    """
    config = load_credentials(filepath)
    
    if username not in config['credentials']['usernames']:
        return False
    
    # Hash and store the recovery code
    hashed_code = hash_recovery_code(recovery_code)
    config['credentials']['usernames'][username]['recovery_code'] = hashed_code
    
    save_credentials(config, filepath)
    return True


def verify_recovery_code(username: str, recovery_code: str, filepath: str = "credentials.yaml") -> bool:
    """
    Verify a recovery code for a user.
    
    Args:
        username: Username to verify recovery code for
        recovery_code: Plain text recovery code to verify
        filepath: Path to credentials file
    
    Returns:
        bool: True if code matches, False otherwise
    """
    config = load_credentials(filepath)
    
    if username not in config['credentials']['usernames']:
        return False
    
    stored_hash = config['credentials']['usernames'][username].get('recovery_code')
    if not stored_hash:
        return False
    
    return hash_recovery_code(recovery_code) == stored_hash


def add_security_question(username: str, question: str, answer: str, filepath: str = "credentials.yaml"):
    """
    Add a security question and answer to a user's account.
    
    Args:
        username: Username to add security question for
        question: Security question text
        answer: Answer to security question (will be hashed)
        filepath: Path to credentials file
    
    Returns:
        bool: True if successful, False if user doesn't exist
    """
    config = load_credentials(filepath)
    
    if username not in config['credentials']['usernames']:
        return False
    
    # Hash the answer (case-insensitive)
    hashed_answer = hashlib.sha256(answer.lower().strip().encode()).hexdigest()
    
    config['credentials']['usernames'][username]['security_question'] = question
    config['credentials']['usernames'][username]['security_answer'] = hashed_answer
    
    save_credentials(config, filepath)
    return True


def verify_security_answer(username: str, answer: str, filepath: str = "credentials.yaml") -> bool:
    """
    Verify a security question answer for a user.
    
    Args:
        username: Username to verify answer for
        answer: Answer to verify
        filepath: Path to credentials file
    
    Returns:
        bool: True if answer matches, False otherwise
    """
    config = load_credentials(filepath)
    
    if username not in config['credentials']['usernames']:
        return False
    
    stored_hash = config['credentials']['usernames'][username].get('security_answer')
    if not stored_hash:
        return False
    
    return hashlib.sha256(answer.lower().strip().encode()).hexdigest() == stored_hash


def get_security_question(username: str, filepath: str = "credentials.yaml") -> str:
    """
    Get the security question for a user.
    
    Args:
        username: Username to get security question for
        filepath: Path to credentials file
    
    Returns:
        str: Security question or empty string if not found
    """
    config = load_credentials(filepath)
    
    if username not in config['credentials']['usernames']:
        return ""
    
    return config['credentials']['usernames'][username].get('security_question', '')


def reset_password_with_recovery(username: str, recovery_code: str, new_password: str, filepath: str = "credentials.yaml") -> bool:
    """
    Reset a user's password using their recovery code.
    
    Args:
        username: Username to reset password for
        recovery_code: Recovery code for verification
        new_password: New password to set
        filepath: Path to credentials file
    
    Returns:
        bool: True if successful, False if verification failed
    """
    if verify_recovery_code(username, recovery_code, filepath):
        return change_password(username, new_password, filepath)
    return False


def reset_password_with_security_question(username: str, answer: str, new_password: str, filepath: str = "credentials.yaml") -> bool:
    """
    Reset a user's password using their security question answer.
    
    Args:
        username: Username to reset password for
        answer: Answer to security question
        new_password: New password to set
        filepath: Path to credentials file
    
    Returns:
        bool: True if successful, False if verification failed
    """
    if verify_security_answer(username, answer, filepath):
        return change_password(username, new_password, filepath)
    return False
