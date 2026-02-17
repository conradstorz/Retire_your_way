"""
Migration Utility: YAML to Database

This script migrates user credentials from credentials.yaml to the database.
Run this once when upgrading to version 1.0.0.

Usage:
    python migrate_to_db.py
"""

import yaml
from pathlib import Path
from auth_db import get_auth_manager
from db_connection import get_db


def migrate_credentials_from_yaml():
    """Migrate credentials from YAML file to database."""
    
    yaml_path = Path("credentials.yaml")
    
    if not yaml_path.exists():
        print("✓ No credentials.yaml file found - starting fresh with database.")
        return
    
    print("Found credentials.yaml - migrating to database...")
    
    try:
        with open(yaml_path, 'r') as file:
            config = yaml.safe_load(file)
        
        auth_manager = get_auth_manager()
        db = get_db()
        
        # Migrate users
        usernames = config.get('credentials', {}).get('usernames', {})
        migrated_count = 0
        
        for username, user_data in usernames.items():
            # Check if user already exists in database
            rows = db.execute_query(
                "SELECT COUNT(*) FROM users WHERE username = ?",
                (username,)
            )
            
            if rows and rows[0][0] > 0:
                print(f"  ⚠ User '{username}' already exists in database - skipping")
                continue
            
            # Insert user with existing password hash
            db.execute_update("""
                INSERT INTO users (username, name, email, password_hash)
                VALUES (?, ?, ?, ?)
            """, (
                username,
                user_data.get('name', username),
                user_data.get('email', f'{username}@example.com'),
                user_data.get('password', '')
            ))
            
            # Migrate recovery code if exists
            if 'recovery_code' in user_data:
                db.execute_update("""
                    UPDATE users SET recovery_code_hash = ?
                    WHERE username = ?
                """, (user_data['recovery_code'], username))
            
            # Migrate security question if exists
            if 'security_question' in user_data and 'security_answer' in user_data:
                db.execute_update("""
                    UPDATE users 
                    SET security_question = ?, security_answer_hash = ?
                    WHERE username = ?
                """, (
                    user_data['security_question'],
                    user_data['security_answer'],
                    username
                ))
            
            migrated_count += 1
            print(f"  ✓ Migrated user: {username}")
        
        # Migrate cookie configuration
        cookie_config = config.get('cookie', {})
        if cookie_config:
            db.execute_update("""
                UPDATE auth_config 
                SET cookie_name = ?, cookie_key = ?, cookie_expiry_days = ?
                WHERE id = 1
            """, (
                cookie_config.get('name', 'retirement_planner_auth'),
                cookie_config.get('key', 'retirement_planning_secret_key_change_this'),
                cookie_config.get('expiry_days', 30)
            ))
            print("  ✓ Migrated cookie configuration")
        
        print(f"\n✓ Migration complete! Migrated {migrated_count} user(s).")
        print(f"\nYou can now safely rename or delete credentials.yaml")
        print(f"Consider keeping a backup until you verify everything works.")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("Retirement Planner - Credential Migration")
    print("=" * 60)
    print()
    migrate_credentials_from_yaml()
    print()
    print("=" * 60)
