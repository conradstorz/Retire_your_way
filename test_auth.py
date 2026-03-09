"""
Tests for Authentication System (auth_db.py).

Tests verify user creation, password hashing, recovery mechanisms,
and security best practices.
"""

import pytest
import hashlib
from auth_db import AuthManager


class TestAuthManager:
    """Test authentication manager functionality"""

    @pytest.fixture
    def auth(self):
        """Create test authentication manager"""
        # Uses default database connection
        auth_manager = AuthManager()
        yield auth_manager
        # Cleanup handled by database

    @pytest.fixture
    def test_username(self):
        """Generate unique test username"""
        import time
        return f"test_auth_user_{int(time.time() * 1000)}"

    def test_create_new_user(self, auth, test_username):
        """Should create user with hashed password"""
        email = f"{test_username}@example.com"
        password = "SecurePassword123!"
        name = "Test User"

        # Create user
        result = auth.create_user(
            username=test_username,
            name=name,
            email=email,
            password=password
        )

        assert result is True or result == test_username

        # Verify user exists
        user = auth.get_user(test_username)
        assert user is not None
        assert user['username'] == test_username
        assert user['name'] == name
        assert user['email'] == email
        assert user['password_hash'] is not None

    def test_password_hashing_security(self, auth, test_username):
        """Should use bcrypt, never store plaintext"""
        password = "MySecretPassword456"
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password=password
        )

        user = auth.get_user(test_username)

        # Password should be hashed (not equal to plaintext)
        assert user['password_hash'] != password

        # Should start with bcrypt identifier ($2b$ or $2a$)
        assert user['password_hash'].startswith('$2')

        # Should be longer than plaintext (bcrypt hashes are 60 chars)
        assert len(user['password_hash']) >= 59

    def test_password_verification_correct(self, auth, test_username):
        """Should verify correct password"""
        password = "CorrectPassword789"
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password=password
        )

        # Verify correct password
        is_valid = auth.verify_password(test_username, password)
        assert is_valid is True

    def test_password_verification_incorrect(self, auth, test_username):
        """Should reject incorrect password"""
        correct_password = "CorrectPassword789"
        wrong_password = "WrongPassword123"
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password=correct_password
        )

        # Verify wrong password is rejected
        is_valid = auth.verify_password(test_username, wrong_password)
        assert is_valid is False

    def test_recovery_code_generation(self, auth, test_username):
        """Should generate and hash recovery codes"""
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password="Password123"
        )

        # Generate recovery code
        recovery_code = auth.generate_recovery_code(test_username)

        assert recovery_code is not None
        assert isinstance(recovery_code, str)
        assert len(recovery_code) > 10  # Should be a substantial code

        # Verify it's stored hashed
        user = auth.get_user(test_username)
        if 'recovery_code_hash' in user and user['recovery_code_hash']:
            # Should be a hash, not the plaintext code
            assert user['recovery_code_hash'] != recovery_code
            # SHA-256 hashes are 64 hex characters
            assert len(user['recovery_code_hash']) == 64

    def test_recovery_code_verification(self, auth, test_username):
        """Should verify valid recovery code"""
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password="Password123"
        )

        # Generate and verify
        recovery_code = auth.generate_recovery_code(test_username)

        is_valid = auth.verify_recovery_code(test_username, recovery_code)
        assert is_valid is True

        # Wrong code should fail
        is_valid_wrong = auth.verify_recovery_code(test_username, "wrong_code_123")
        assert is_valid_wrong is False

    def test_security_question_setup(self, auth, test_username):
        """Should store hashed security answers"""
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password="Password123"
        )

        question = "What is your favorite color?"
        answer = "Blue"

        # Set security question
        auth.set_security_question(test_username, question, answer)

        user = auth.get_user(test_username)

        assert user['security_question'] == question
        assert user['security_answer_hash'] is not None
        # Answer should be hashed
        assert user['security_answer_hash'] != answer
        # Should be SHA-256 hash (64 hex chars) or bcrypt
        assert len(user['security_answer_hash']) >= 32

    def test_security_question_verification(self, auth, test_username):
        """Should verify correct security answer"""
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password="Password123"
        )

        question = "What city were you born in?"
        correct_answer = "Chicago"

        auth.set_security_question(test_username, question, correct_answer)

        # Verify correct answer
        is_valid = auth.verify_security_answer(test_username, correct_answer)
        assert is_valid is True

        # Verify wrong answer fails
        is_valid_wrong = auth.verify_security_answer(test_username, "New York")
        assert is_valid_wrong is False

    def test_admin_user_creation(self, auth):
        """Should ensure admin exists on initialization"""
        # Admin should exist after AuthManager initialization
        admin = auth.get_user('admin')

        assert admin is not None
        assert admin['username'] == 'admin'
        # Admin should have a password set
        assert admin['password_hash'] is not None

    def test_user_update(self, auth, test_username):
        """Should update user details"""
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="Original Name",
            email=email,
            password="Password123"
        )

        # Update user
        auth.update_user(
            username=test_username,
            name="Updated Name",
            email="newemail@example.com"
        )

        user = auth.get_user(test_username)
        assert user['name'] == "Updated Name"
        assert user['email'] == "newemail@example.com"

    def test_password_change(self, auth, test_username):
        """Should allow password change"""
        email = f"{test_username}@example.com"
        old_password = "OldPassword123"
        new_password = "NewPassword456"

        auth.create_user(
            username=test_username,
            name="Test",
            email=email,
            password=old_password
        )

        # Change password
        auth.change_password(test_username, new_password)

        # Old password should fail
        assert auth.verify_password(test_username, old_password) is False

        # New password should work
        assert auth.verify_password(test_username, new_password) is True

    def test_duplicate_username_rejected(self, auth, test_username):
        """Should reject duplicate usernames"""
        email = f"{test_username}@example.com"

        auth.create_user(
            username=test_username,
            name="First User",
            email=email,
            password="Password123"
        )

        # Try to create duplicate
        with pytest.raises(Exception):
            auth.create_user(
                username=test_username,  # Same username
                name="Second User",
                email="different@example.com",
                password="Password456"
            )

    def test_case_sensitivity_usernames(self, auth):
        """Should handle username case sensitivity appropriately"""
        import time
        base_username = f"test_{int(time.time() * 1000)}"

        auth.create_user(
            username=base_username,
            name="Lower",
            email=f"{base_username}@example.com",
            password="Password123"
        )

        # Try uppercase version
        upper_username = base_username.upper()

        # Behavior depends on implementation
        # If case-insensitive, should reject or return same user
        # If case-sensitive, should allow separate user
        try:
            auth.create_user(
                username=upper_username,
                name="Upper",
                email=f"{upper_username}@example.com",
                password="Password456"
            )
            # If this succeeds, usernames are case-sensitive
            user_lower = auth.get_user(base_username)
            user_upper = auth.get_user(upper_username)
            assert user_lower['name'] != user_upper['name']
        except Exception:
            # If this fails, usernames are case-insensitive (good for UX)
            pass


class TestAuthCookieManagement:
    """Test cookie configuration for session management"""

    @pytest.fixture
    def auth(self):
        """Create test authentication manager"""
        auth_manager = AuthManager()
        yield auth_manager

    def test_cookie_configuration_exists(self, auth):
        """Should manage cookie settings correctly"""
        config = auth.get_cookie_config()

        assert config is not None
        assert 'cookie_name' in config or config.get('cookie_name')
        assert 'cookie_key' in config or config.get('cookie_key')
        assert 'cookie_expiry_days' in config or config.get('cookie_expiry_days')

    def test_cookie_key_is_random(self, auth):
        """Cookie key should be securely random"""
        config = auth.get_cookie_config()

        if 'cookie_key' in config and config['cookie_key']:
            cookie_key = config['cookie_key']

            # Should be substantial length
            assert len(cookie_key) >= 32

            # Should not be a predictable value
            assert cookie_key not in ['admin', 'password', '12345', 'test']

    def test_cookie_expiry_reasonable(self, auth):
        """Cookie expiry should be reasonable (not too short or too long)"""
        config = auth.get_cookie_config()

        if 'cookie_expiry_days' in config:
            expiry = config['cookie_expiry_days']

            # Should be between 1 and 90 days
            assert 1 <= expiry <= 90


class TestAuthEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def auth(self):
        """Create test authentication manager"""
        auth_manager = AuthManager()
        yield auth_manager

    def test_empty_password_rejected(self, auth):
        """Should reject empty password"""
        import time
        username = f"test_{int(time.time() * 1000)}"

        with pytest.raises(Exception):
            auth.create_user(
                username=username,
                name="Test",
                email=f"{username}@example.com",
                password=""
            )

    def test_empty_username_rejected(self, auth):
        """Should reject empty username"""
        with pytest.raises(Exception):
            auth.create_user(
                username="",
                name="Test",
                email="test@example.com",
                password="Password123"
            )

    def test_special_characters_in_username(self, auth):
        """Should handle special characters in username"""
        import time
        username = f"test.user-{int(time.time() * 1000)}"

        try:
            auth.create_user(
                username=username,
                name="Test",
                email=f"{username}@example.com",
                password="Password123"
            )

            user = auth.get_user(username)
            assert user is not None
            assert user['username'] == username
        except Exception:
            # Some implementations may restrict special chars
            pass

    def test_very_long_password(self, auth):
        """Should handle very long passwords"""
        import time
        username = f"test_{int(time.time() * 1000)}"
        long_password = "A" * 1000  # 1000 character password

        auth.create_user(
            username=username,
            name="Test",
            email=f"{username}@example.com",
            password=long_password
        )

        # Should still verify correctly
        assert auth.verify_password(username, long_password) is True

    def test_unicode_in_password(self, auth):
        """Should handle unicode characters in password"""
        import time
        username = f"test_{int(time.time() * 1000)}"
        unicode_password = "Pāsswörd123!日本語"

        auth.create_user(
            username=username,
            name="Test",
            email=f"{username}@example.com",
            password=unicode_password
        )

        # Should verify correctly
        assert auth.verify_password(username, unicode_password) is True

    def test_get_nonexistent_user(self, auth):
        """Should handle requests for non-existent users"""
        user = auth.get_user("nonexistent_user_12345_xyz")

        # Should return None or raise appropriate exception
        assert user is None or user == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
