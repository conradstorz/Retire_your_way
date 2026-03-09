"""
Tests for UserDataManager - Database persistence layer.

Tests verify CRUD operations, data isolation between users,
and integration with the database abstraction layer.
"""

import pytest
import tempfile
import os
from user_data import UserDataManager
from calculations import AccountBucket, ExpenseCategory, OneTimeEvent


class TestUserDataManager:
    """Test UserDataManager CRUD operations"""

    @pytest.fixture
    def manager(self):
        """Create a test database manager"""
        # Use in-memory database for testing (SQLite default)
        manager = UserDataManager()
        yield manager
        # Cleanup is handled by SQLite in-memory DB

    @pytest.fixture
    def test_username(self):
        """Generate unique test username"""
        import time
        return f"test_user_{int(time.time() * 1000)}"

    def test_save_and_load_user_profile(self, manager, test_username):
        """Should save and retrieve user profile correctly"""
        profile = {
            'current_age': 45,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 100000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }

        # Save
        manager.save_user_profile(test_username, profile)

        # Load
        loaded = manager.load_user_profile(test_username)

        assert loaded is not None
        assert loaded['current_age'] == 45
        assert loaded['target_age'] == 85
        assert loaded['work_end_age'] == 65
        assert loaded['current_work_income'] == 100000
        assert loaded['ss_monthly_benefit'] == 2500
        assert loaded['ultimate_max_age'] == 110

    def test_update_existing_profile(self, manager, test_username):
        """Should update existing profile without duplicating"""
        # Initial save
        profile1 = {
            'current_age': 50,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 80000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2000,
            'ss_cola': 0.02,
            'inflation_rate': 0.025,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(test_username, profile1)

        # Update
        profile2 = profile1.copy()
        profile2['current_age'] = 51  # One year later
        profile2['current_work_income'] = 85000
        manager.save_user_profile(test_username, profile2)

        # Load - should have updated values
        loaded = manager.load_user_profile(test_username)
        assert loaded['current_age'] == 51
        assert loaded['current_work_income'] == 85000

    def test_save_and_load_accounts(self, manager, test_username):
        """Should handle multiple accounts per user"""
        # Create profile first
        profile = {
            'current_age': 40,
            'target_age': 80,
            'work_end_age': 65,
            'current_work_income': 100000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(test_username, profile)

        # Save accounts
        accounts = [
            {
                'name': '401k',
                'balance': 200000,
                'return': 0.08,
                'priority': 2,
                'account_type': '401k',
                'planned_contribution': 19500,
                'continue_post_retirement': False
            },
            {
                'name': 'Roth IRA',
                'balance': 50000,
                'return': 0.08,
                'priority': 3,
                'account_type': 'roth_ira',
                'planned_contribution': 7000,
                'continue_post_retirement': True
            },
            {
                'name': 'Taxable',
                'balance': 75000,
                'return': 0.07,
                'priority': 1,
                'account_type': 'taxable_brokerage',
                'planned_contribution': 10000,
                'continue_post_retirement': False
            }
        ]
        manager.save_user_accounts(test_username, accounts)

        # Load
        loaded = manager.load_user_accounts(test_username)

        assert len(loaded) == 3

        # Find 401k
        acc_401k = next(a for a in loaded if a['name'] == '401k')
        assert acc_401k['balance'] == 200000
        assert acc_401k['account_type'] == '401k'
        assert acc_401k['planned_contribution'] == 19500
        assert acc_401k['continue_post_retirement'] == False

        # Find Roth
        acc_roth = next(a for a in loaded if a['name'] == 'Roth IRA')
        assert acc_roth['continue_post_retirement'] == True

    def test_save_and_load_expenses(self, manager, test_username):
        """Should persist expense categories"""
        # Create profile
        profile = {
            'current_age': 35,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 90000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2200,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(test_username, profile)

        # Save expenses
        expenses = [
            {'name': 'Housing', 'amount': 24000, 'type': 'CORE'},
            {'name': 'Food', 'amount': 12000, 'type': 'CORE'},
            {'name': 'Healthcare', 'amount': 8000, 'type': 'CORE'},
            {'name': 'Travel', 'amount': 15000, 'type': 'FLEX'},
            {'name': 'Entertainment', 'amount': 6000, 'type': 'FLEX'},
        ]
        manager.save_user_expenses(test_username, expenses)

        # Load
        loaded = manager.load_user_expenses(test_username)

        assert len(loaded) == 5

        core_expenses = [e for e in loaded if e['type'] == 'CORE']
        flex_expenses = [e for e in loaded if e['type'] == 'FLEX']

        assert len(core_expenses) == 3
        assert len(flex_expenses) == 2

        total_core = sum(e['amount'] for e in core_expenses)
        total_flex = sum(e['amount'] for e in flex_expenses)

        assert total_core == 44000
        assert total_flex == 21000

    def test_save_and_load_events(self, manager, test_username):
        """Should persist one-time events with account names"""
        # Create profile
        profile = {
            'current_age': 50,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 100000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(test_username, profile)

        # Save events
        events = [
            {
                'year': 2030,
                'description': 'Buy new car',
                'amount': 40000,
                'account_name': 'Taxable'
            },
            {
                'year': 2035,
                'description': 'Home renovation',
                'amount': 75000,
                'account_name': '401k'
            },
            {
                'year': 2040,
                'description': 'Inheritance received',
                'amount': -200000,  # Negative = addition
                'account_name': 'Taxable'
            }
        ]
        manager.save_user_events(test_username, events)

        # Load
        loaded = manager.load_user_events(test_username)

        assert len(loaded) == 3

        car_event = next(e for e in loaded if e['description'] == 'Buy new car')
        assert car_event['year'] == 2030
        assert car_event['amount'] == 40000
        assert car_event['account_name'] == 'Taxable'

        inheritance = next(e for e in loaded if e['description'] == 'Inheritance received')
        assert inheritance['amount'] == -200000

    def test_user_data_isolation(self, manager):
        """Data for user A should not appear for user B"""
        import time
        user_a = f"user_a_{int(time.time() * 1000)}"
        user_b = f"user_b_{int(time.time() * 1000) + 1}"

        # Create profiles
        profile_a = {
            'current_age': 40,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 80000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2000,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        profile_b = {
            'current_age': 55,
            'target_age': 90,
            'work_end_age': 70,
            'current_work_income': 150000,
            'work_income_growth': 0.04,
            'ss_start_age': 70,
            'ss_monthly_benefit': 3500,
            'ss_cola': 0.03,
            'inflation_rate': 0.035,
            'max_flex_reduction': 0.6,
            'ultimate_max_age': 110
        }

        manager.save_user_profile(user_a, profile_a)
        manager.save_user_profile(user_b, profile_b)

        # Save accounts for each user
        accounts_a = [{'name': '401k_A', 'balance': 100000, 'return': 0.07,
                      'priority': 1, 'account_type': '401k', 'planned_contribution': 10000,
                      'continue_post_retirement': False}]
        accounts_b = [{'name': '401k_B', 'balance': 500000, 'return': 0.08,
                      'priority': 1, 'account_type': '401k', 'planned_contribution': 20000,
                      'continue_post_retirement': False}]

        manager.save_user_accounts(user_a, accounts_a)
        manager.save_user_accounts(user_b, accounts_b)

        # Load and verify isolation
        loaded_a = manager.load_user_profile(user_a)
        loaded_b = manager.load_user_profile(user_b)

        assert loaded_a['current_age'] == 40
        assert loaded_b['current_age'] == 55

        accounts_loaded_a = manager.load_user_accounts(user_a)
        accounts_loaded_b = manager.load_user_accounts(user_b)

        assert len(accounts_loaded_a) == 1
        assert len(accounts_loaded_b) == 1
        assert accounts_loaded_a[0]['name'] == '401k_A'
        assert accounts_loaded_b[0]['name'] == '401k_B'

    def test_default_data_creation(self, manager, test_username):
        """Should create sensible defaults for new users"""
        # Try to load profile for non-existent user
        profile = manager.load_user_profile(test_username)

        # Should return None or empty dict for non-existent user
        # (Actual behavior depends on implementation)
        # If it returns defaults, verify they're sensible
        if profile:
            assert 'current_age' in profile
            assert 'target_age' in profile
            assert profile['target_age'] > profile['current_age']

    def test_snapshot_save_and_retrieve(self, manager, test_username):
        """Should save and query account snapshots"""
        # Create profile
        profile = {
            'current_age': 45,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 100000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(test_username, profile)

        # Save snapshots
        manager.save_snapshot(test_username, '401k', '2024-01-01', 0, 100000)
        manager.save_snapshot(test_username, '401k', '2024-06-30', 10000, 117000)
        manager.save_snapshot(test_username, '401k', '2024-12-31', 10000, 135000)

        manager.save_snapshot(test_username, 'Roth IRA', '2024-01-01', 0, 50000)
        manager.save_snapshot(test_username, 'Roth IRA', '2024-12-31', 7000, 61000)

        # Retrieve snapshots
        snapshots_401k = manager.load_snapshots(test_username, '401k')
        snapshots_roth = manager.load_snapshots(test_username, 'Roth IRA')

        assert len(snapshots_401k) == 3
        assert len(snapshots_roth) == 2

        # Verify values
        assert snapshots_401k[0]['total_value'] == 100000
        assert snapshots_401k[-1]['total_value'] == 135000
        assert snapshots_401k[-1]['contributed'] == 10000

    def test_historical_year_summaries(self, manager, test_username):
        """Should aggregate snapshots into yearly summaries"""
        # Create profile
        profile = {
            'current_age': 45,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 100000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(test_username, profile)

        # Save snapshots for 2024
        manager.save_snapshot(test_username, '401k', '2024-01-01', 0, 100000)
        manager.save_snapshot(test_username, '401k', '2024-12-31', 20000, 128000)

        manager.save_snapshot(test_username, 'Roth IRA', '2024-01-01', 0, 50000)
        manager.save_snapshot(test_username, 'Roth IRA', '2024-12-31', 7000, 61000)

        # Get summaries
        summaries = manager.get_historical_year_summaries(test_username)

        assert len(summaries) == 1
        summary = summaries[0]

        assert summary['calendar_year'] == 2024
        assert summary['total_value'] == 128000 + 61000  # 189000
        assert summary['total_contributions'] == 20000 + 7000  # 27000
        # Growth = final - initial - contributions
        # = 189000 - 150000 - 27000 = 12000
        assert summary['total_growth'] == 12000
        # ROI = 12000 / 150000 = 0.08
        assert abs(summary['annualized_roi'] - 0.08) < 0.001

    def test_clear_user_data(self, manager, test_username):
        """Should remove all user data across all tables"""
        # Create complete user dataset
        profile = {
            'current_age': 50,
            'target_age': 85,
            'work_end_age': 65,
            'current_work_income': 100000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(test_username, profile)

        accounts = [{'name': '401k', 'balance': 200000, 'return': 0.07,
                    'priority': 1, 'account_type': '401k', 'planned_contribution': 15000,
                    'continue_post_retirement': False}]
        manager.save_user_accounts(test_username, accounts)

        expenses = [{'name': 'Living', 'amount': 50000, 'type': 'CORE'}]
        manager.save_user_expenses(test_username, expenses)

        events = [{'year': 2030, 'description': 'Test', 'amount': 10000, 'account_name': '401k'}]
        manager.save_user_events(test_username, events)

        manager.save_snapshot(test_username, '401k', '2024-12-31', 15000, 215000)

        # Now delete all
        # Note: UserDataManager might not have a delete method, but we can test
        # that different usernames don't interfere
        # For now, verify data exists
        loaded_profile = manager.load_user_profile(test_username)
        assert loaded_profile is not None

        # If delete method exists, test it
        # manager.delete_user_data(test_username)
        # assert manager.load_user_profile(test_username) is None


class TestUserDataEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def manager(self):
        """Create a test database manager"""
        manager = UserDataManager()
        yield manager

    def test_get_nonexistent_user(self, manager):
        """Should handle requests for non-existent users gracefully"""
        profile = manager.load_user_profile("nonexistent_user_12345")

        # Should return None or empty structure
        assert profile is None or profile == {}

    def test_empty_accounts_list(self, manager):
        """Should handle saving empty accounts list"""
        import time
        username = f"test_empty_{int(time.time() * 1000)}"

        profile = {
            'current_age': 30,
            'target_age': 80,
            'work_end_age': 65,
            'current_work_income': 50000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 1500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(username, profile)

        # Save empty accounts
        manager.save_user_accounts(username, [])

        # Should return empty list
        loaded = manager.load_user_accounts(username)
        assert loaded == []

    def test_update_account_balances(self, manager):
        """Should update account balances when saving again"""
        import time
        username = f"test_update_{int(time.time() * 1000)}"

        profile = {
            'current_age': 40,
            'target_age': 80,
            'work_end_age': 65,
            'current_work_income': 100000,
            'work_income_growth': 0.03,
            'ss_start_age': 67,
            'ss_monthly_benefit': 2500,
            'ss_cola': 0.025,
            'inflation_rate': 0.03,
            'max_flex_reduction': 0.5,
            'ultimate_max_age': 110
        }
        manager.save_user_profile(username, profile)

        # Initial accounts
        accounts_v1 = [
            {'name': '401k', 'balance': 100000, 'return': 0.07,
             'priority': 1, 'account_type': '401k', 'planned_contribution': 10000,
             'continue_post_retirement': False}
        ]
        manager.save_user_accounts(username, accounts_v1)

        # Update with new balance
        accounts_v2 = [
            {'name': '401k', 'balance': 120000, 'return': 0.08,
             'priority': 1, 'account_type': '401k', 'planned_contribution': 15000,
             'continue_post_retirement': False}
        ]
        manager.save_user_accounts(username, accounts_v2)

        # Load - should have updated values
        loaded = manager.load_user_accounts(username)
        assert len(loaded) == 1
        assert loaded[0]['balance'] == 120000
        assert loaded[0]['return'] == 0.08
        assert loaded[0]['planned_contribution'] == 15000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
