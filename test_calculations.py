"""
Comprehensive tests for retirement projection calculations.

Tests verify year-by-year projection accuracy across multiple scenarios including:
- Work income growth and cessation
- Social Security benefits with COLA
- Expense inflation and FLEX spending reduction
- Account contribution rules and funding
- Withdrawal ordering by priority
- Investment returns
- Required Minimum Distributions (RMDs)
- One-time events

Uses both specific scenario tests and property-based testing with hypothesis.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pandas as pd
from calculations import (
    run_comprehensive_projection,
    analyze_retirement_plan,
    AccountBucket,
    ExpenseCategory,
    OneTimeEvent,
    can_contribute,
    calculate_rmd_amount,
    get_rmd_starting_age,
    calculate_conservative_retirement_balance,
)


# ============================================================================
# UNIT TESTS - Basic Component Validation
# ============================================================================


class TestWorkIncome:
    """Test work income calculations"""
    
    def test_work_income_grows_at_inflation_rate(self):
        """Work income should grow at the specified inflation rate"""
        result = run_comprehensive_projection(
            current_age=30,
            target_age=35,
            current_work_income=100000,
            work_end_age=40,  # Still working during projection
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("401k", 50000, 0.07, 1, "401k", 0)],
            expense_categories=[ExpenseCategory("Food", 30000, "CORE")],
            inflation_rate=0.03,
        )
        
        # Year 0: $100,000
        # Year 1: $100,000 * 1.03 = $103,000
        # Year 2: $100,000 * 1.03^2 = $106,090
        # Year 3: $100,000 * 1.03^3 = $109,272.70
        # Year 4: $100,000 * 1.03^4 = $112,550.88
        # Year 5: $100,000 * 1.03^5 = $115,927.41
        
        assert abs(result.iloc[0]['work_income'] - 100000) < 1
        assert abs(result.iloc[1]['work_income'] - 103000) < 1
        assert abs(result.iloc[2]['work_income'] - 106090) < 1
        assert abs(result.iloc[3]['work_income'] - 109272.70) < 1
        assert abs(result.iloc[4]['work_income'] - 112550.88) < 1
        assert abs(result.iloc[5]['work_income'] - 115927.41) < 1
    
    def test_work_income_stops_at_work_end_age(self):
        """Work income should stop at work_end_age"""
        result = run_comprehensive_projection(
            current_age=64,
            target_age=68,
            current_work_income=100000,
            work_end_age=66,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("IRA", 500000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 50000, "CORE")],
        )
        
        # Age 64: working ($100,000)
        # Age 65: working ($103,000)
        # Age 66: NOT working (turned 66, work stops)
        # Age 67: NOT working
        # Age 68: NOT working
        
        assert result.iloc[0]['work_income'] > 0  # Age 64
        assert result.iloc[1]['work_income'] > 0  # Age 65
        assert result.iloc[2]['work_income'] == 0  # Age 66
        assert result.iloc[3]['work_income'] == 0  # Age 67
        assert result.iloc[4]['work_income'] == 0  # Age 68


class TestSocialSecurity:
    """Test Social Security benefit calculations"""
    
    def test_ss_starts_at_correct_age(self):
        """Social Security should start at ss_start_age"""
        result = run_comprehensive_projection(
            current_age=65,
            target_age=70,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2500,
            accounts=[AccountBucket("IRA", 500000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 50000, "CORE")],
        )
        
        # Age 65: No SS
        # Age 66: No SS
        # Age 67: SS starts ($2500 * 12 = $30,000)
        # Age 68: SS with 1 year COLA
        # Age 69: SS with 2 years COLA
        # Age 70: SS with 3 years COLA
        
        assert result.iloc[0]['ss_income'] == 0  # Age 65
        assert result.iloc[1]['ss_income'] == 0  # Age 66
        assert abs(result.iloc[2]['ss_income'] - 30000) < 1  # Age 67
        assert result.iloc[3]['ss_income'] > 30000  # Age 68 (COLA)
        assert result.iloc[4]['ss_income'] > result.iloc[3]['ss_income']  # Age 69
    
    def test_ss_cola_adjustment(self):
        """Social Security should increase by COLA each year"""
        result = run_comprehensive_projection(
            current_age=67,
            target_age=70,
            current_work_income=0,
            work_end_age=67,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("IRA", 500000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
            ss_cola=0.025,
        )
        
        # Age 67: $2000 * 12 * (1.025^0) = $24,000
        # Age 68: $2000 * 12 * (1.025^1) = $24,600
        # Age 69: $2000 * 12 * (1.025^2) = $25,215
        # Age 70: $2000 * 12 * (1.025^3) = $25,845.375
        
        assert abs(result.iloc[0]['ss_income'] - 24000) < 1
        assert abs(result.iloc[1]['ss_income'] - 24600) < 1
        assert abs(result.iloc[2]['ss_income'] - 25215) < 1
        assert abs(result.iloc[3]['ss_income'] - 25845.375) < 1


class TestExpenseInflation:
    """Test expense inflation and FLEX spending reduction"""
    
    def test_core_expenses_inflate(self):
        """Core expenses should inflate at the specified rate"""
        result = run_comprehensive_projection(
            current_age=30,
            target_age=33,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("401k", 100000, 0.07, 1, "401k", 0)],
            expense_categories=[ExpenseCategory("Housing", 20000, "CORE")],
            inflation_rate=0.03,
        )
        
        # Year 0: $20,000
        # Year 1: $20,000 * 1.03 = $20,600
        # Year 2: $20,000 * 1.03^2 = $21,218
        # Year 3: $20,000 * 1.03^3 = $21,854.54
        
        assert abs(result.iloc[0]['core_expenses'] - 20000) < 1
        assert abs(result.iloc[1]['core_expenses'] - 20600) < 1
        assert abs(result.iloc[2]['core_expenses'] - 21218) < 1
        assert abs(result.iloc[3]['core_expenses'] - 21854.54) < 1
    
    def test_flex_expenses_inflate(self):
        """FLEX expenses should inflate at the specified rate when not reduced"""
        result = run_comprehensive_projection(
            current_age=30,
            target_age=33,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Taxable", 100000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[
                ExpenseCategory("Food", 30000, "CORE"),
                ExpenseCategory("Travel", 15000, "FLEX"),
            ],
            inflation_rate=0.03,
        )
        
        # Year 0: $15,000
        # Year 1: $15,000 * 1.03 = $15,450
        # Year 2: $15,000 * 1.03^2 = $15,913.50
        # Year 3: $15,000 * 1.03^3 = $16,390.91
        
        assert abs(result.iloc[0]['flex_expenses_full'] - 15000) < 1
        assert abs(result.iloc[1]['flex_expenses_full'] - 15450) < 1
        assert abs(result.iloc[2]['flex_expenses_full'] - 15913.50) < 1
        assert abs(result.iloc[3]['flex_expenses_full'] - 16390.91) < 1
    
    def test_flex_expenses_reduced_during_deficit(self):
        """FLEX expenses should be reduced (up to max_flex_reduction) during deficit"""
        result = run_comprehensive_projection(
            current_age=68,
            target_age=70,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=1500,  # Only $18k/year
            accounts=[AccountBucket("IRA", 50000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[
                ExpenseCategory("Food", 15000, "CORE"),
                ExpenseCategory("Travel", 20000, "FLEX"),
            ],
            max_flex_reduction=0.50,
        )
        
        # Income: $1500 * 12 = $18,000
        # Core expenses: ~$15,000 (inflated)
        # FLEX expenses full: ~$20,000 (inflated)
        # Total needed: ~$35,000, but only have ~$18,000
        # Available after core: $18,000 - $15,000 = $3,000
        # Min FLEX required: $20,000 * 0.5 = $10,000
        # Since $3,000 < $10,000, FLEX should be at minimum (50% of full)
        
        for i in range(len(result)):
            flex_multiplier = result.iloc[i]['flex_multiplier']
            # FLEX should be reduced significantly (at minimum)
            assert flex_multiplier <= 0.5, f"Row {i}: flex_multiplier={flex_multiplier}"
    
    def test_flex_expenses_not_reduced_when_surplus(self):
        """FLEX expenses should not be reduced when income covers everything"""
        result = run_comprehensive_projection(
            current_age=68,
            target_age=70,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=5000,  # $60k/year - plenty
            accounts=[AccountBucket("IRA", 500000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[
                ExpenseCategory("Food", 15000, "CORE"),
                ExpenseCategory("Travel", 20000, "FLEX"),
            ],
        )
        
        # Income: $5000 * 12 = $60,000
        # Total expenses: ~$35,000 (inflated)
        # Should have surplus, no need to reduce FLEX
        
        for i in range(len(result)):
            flex_multiplier = result.iloc[i]['flex_multiplier']
            assert flex_multiplier == 1.0, f"Row {i}: flex_multiplier={flex_multiplier}"


class TestAccountContributions:
    """Test account contribution rules and logic"""
    
    def test_401k_contributions_stop_at_work_end_age(self):
        """401k contributions should stop at work_end_age"""
        result = run_comprehensive_projection(
            current_age=63,
            target_age=68,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("401k", 300000, 0.07, 1, "401k", 10000, False)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Age 63: working, should contribute $10,000
        # Age 64: working, should contribute $10,000
        # Age 65: NOT working (age = work_end_age), NO contribution
        # Age 66+: NOT working, NO contribution
        
        assert abs(result.iloc[0]['401k_contribution'] - 10000) < 1  # Age 63
        assert abs(result.iloc[1]['401k_contribution'] - 10000) < 1  # Age 64
        assert result.iloc[2]['401k_contribution'] == 0  # Age 65
        assert result.iloc[3]['401k_contribution'] == 0  # Age 66
        assert result.iloc[4]['401k_contribution'] == 0  # Age 67
        assert result.iloc[5]['401k_contribution'] == 0  # Age 68
    
    def test_traditional_ira_contributions_stop_at_73(self):
        """Traditional IRA contributions should stop at age 73"""
        result = run_comprehensive_projection(
            current_age=70,
            target_age=75,
            current_work_income=50000,
            work_end_age=75,  # Still working
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("IRA", 200000, 0.07, 1, "traditional_ira", 7000, False)],
            expense_categories=[ExpenseCategory("Living", 30000, "CORE")],
        )
        
        # Age 70: can contribute (< 73)
        # Age 71: can contribute (< 73)
        # Age 72: can contribute (< 73)
        # Age 73: CANNOT contribute (= 73)
        # Age 74: CANNOT contribute (> 73)
        # Age 75: CANNOT contribute (> 73)
        
        assert abs(result.iloc[0]['IRA_contribution'] - 7000) < 1  # Age 70
        assert abs(result.iloc[1]['IRA_contribution'] - 7000) < 1  # Age 71
        assert abs(result.iloc[2]['IRA_contribution'] - 7000) < 1  # Age 72
        assert result.iloc[3]['IRA_contribution'] == 0  # Age 73
        assert result.iloc[4]['IRA_contribution'] == 0  # Age 74
        assert result.iloc[5]['IRA_contribution'] == 0  # Age 75
    
    def test_roth_ira_contributions_continue_indefinitely_when_working(self):
        """Roth IRA contributions should continue as long as there's income"""
        result = run_comprehensive_projection(
            current_age=70,
            target_age=80,
            current_work_income=50000,
            work_end_age=80,  # Working until age 80
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Roth", 200000, 0.07, 1, "roth_ira", 7000, False)],
            expense_categories=[ExpenseCategory("Living", 30000, "CORE")],
        )
        
        # Roth IRA has no age limit, but without continue_post_retirement,
        # contributions should stop when work income stops.
        # Since work_end_age=80 and we're projecting to 80, all years should have contributions
        
        for i in range(len(result)):
            age = result.iloc[i]['age']
            if age < 80:  # Before work ends
                assert result.iloc[i]['Roth_contribution'] > 0, f"Age {age} should have Roth contribution"
    
    def test_roth_ira_continue_post_retirement(self):
        """Roth IRA with continue_post_retirement should continue after work ends"""
        result = run_comprehensive_projection(
            current_age=64,
            target_age=70,
            current_work_income=100000,
            work_end_age=67,  # Realistic: work until SS starts
            ss_start_age=67,
            ss_monthly_benefit=3000,  # Sufficient income
            accounts=[AccountBucket("Roth", 300000, 0.07, 1, "roth_ira", 7000, True)],  # continue_post_retirement=True
            expense_categories=[ExpenseCategory("Living", 30000, "CORE")],
        )
        
        # Age 64-66: working, contributions
        # Age 67+: SS income begins when work ends, Roth IRA should continue (continue_post_retirement=True)
        # With $36k SS income and $30k expenses, should have surplus for contributions
        
        assert result.iloc[0]['Roth_contribution'] > 0  # Age 64
        assert result.iloc[1]['Roth_contribution'] > 0  # Age 65
        assert result.iloc[2]['Roth_contribution'] > 0  # Age 66
        # After retirement, contributions continue if income allows
        assert result.iloc[3]['Roth_contribution'] > 0  # Age 67 - SS income now active
    
    def test_contributions_funded_from_income_surplus(self):
        """Contributions should be funded from income surplus first"""
        result = run_comprehensive_projection(
            current_age=50,
            target_age=51,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("401k", 50000, 0.07, 1, "401k", 10000)],
            expense_categories=[
                ExpenseCategory("Living", 40000, "CORE"),
                ExpenseCategory("Travel", 20000, "FLEX"),
            ],
        )
        
        # Income: $100,000
        # Core: $40,000
        # FLEX: $20,000
        # Contribution: $10,000
        # Total needed: $70,000
        # Surplus: $30,000 - plenty to cover everything
        # No withdrawals should occur
        
        assert result.iloc[0]['total_contributions'] == 10000
        assert result.iloc[0]['total_withdrawals'] == 0
        assert result.iloc[0]['flex_multiplier'] == 1.0
    
    def test_contributions_prioritized_over_flex_spending(self):
        """When income is tight, contributions should be funded by reducing FLEX"""
        result = run_comprehensive_projection(
            current_age=50,
            target_age=51,
            current_work_income=60000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("401k", 50000, 0.07, 1, "401k", 10000)],
            expense_categories=[
                ExpenseCategory("Living", 40000, "CORE"),
                ExpenseCategory("Travel", 20000, "FLEX"),
            ],
        )
        
        # Income: $60,000
        # Core: $40,000
        # FLEX full: $20,000
        # Contribution: $10,000
        # Available after core: $60,000 - $40,000 = $20,000
        # Need: $20,000 (FLEX) + $10,000 (contrib) = $30,000
        # Strategy: Reduce FLEX to make room for contributions
        # Can spend: $20,000 - $10,000 = $10,000 on FLEX
        # FLEX multiplier should be 0.5 (50% of planned)
        
        assert abs(result.iloc[0]['total_contributions'] - 10000) < 1
        assert abs(result.iloc[0]['flex_multiplier'] - 0.5) < 0.01
        assert result.iloc[0]['total_withdrawals'] == 0  # No portfolio withdrawals


class TestWithdrawalOrdering:
    """Test account withdrawal ordering by priority"""
    
    def test_withdrawals_follow_priority_order(self):
        """Withdrawals should occur in priority order (lower number first)"""
        result = run_comprehensive_projection(
            current_age=68,
            target_age=69,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=1000,  # Only $12k/year - insufficient
            accounts=[
                AccountBucket("Taxable", 100000, 0.07, 1, "taxable_brokerage", 0),  # Priority 1
                AccountBucket("Roth", 150000, 0.07, 2, "roth_ira", 0),  # Priority 2
                AccountBucket("IRA", 200000, 0.07, 3, "traditional_ira", 0),  # Priority 3
            ],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Income: $12,000
        # Expenses: ~$40,000
        # Deficit: ~$28,000
        # Should withdraw from Taxable first (priority 1)
        
        assert result.iloc[0]['Taxable_withdrawal'] > 0  # Should withdraw from priority 1
        # Roth and IRA shouldn't be touched if Taxable covers the deficit
        if result.iloc[0]['Taxable_withdrawal'] >= 28000:
            assert result.iloc[0]['Roth_withdrawal'] == 0
            assert result.iloc[0]['IRA_withdrawal'] == 0
    
    def test_withdrawals_cascade_when_account_insufficient(self):
        """When one account is insufficient, should move to next priority"""
        result = run_comprehensive_projection(
            current_age=68,
            target_age=69,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=1000,  # Only $12k/year
            accounts=[
                AccountBucket("Taxable", 10000, 0.07, 1, "taxable_brokerage", 0),  # Priority 1 - small
                AccountBucket("Roth", 150000, 0.07, 2, "roth_ira", 0),  # Priority 2
                AccountBucket("IRA", 200000, 0.07, 3, "traditional_ira", 0),  # Priority 3
            ],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Income: $12,000
        # Expenses: ~$40,000
        # Deficit: ~$28,000
        # Taxable only has $10,000, so should withdraw all of it
        # Then move to Roth for remaining ~$18,000
        
        taxable_withdrawal = result.iloc[0]['Taxable_withdrawal']
        roth_withdrawal = result.iloc[0]['Roth_withdrawal']
        
        assert abs(taxable_withdrawal - 10000) < 100  # Should drain Taxable (adjusted for returns)
        assert roth_withdrawal > 15000  # Should then take from Roth
        assert result.iloc[0]['IRA_withdrawal'] == 0  # Shouldn't need IRA


class TestInvestmentReturns:
    """Test investment return calculations"""
    
    def test_returns_applied_to_ending_balance(self):
        """Investment returns should be applied to the balance remaining after all transactions"""
        result = run_comprehensive_projection(
            current_age=50,
            target_age=51,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("401k", 100000, 0.10, 1, "401k", 10000)],  # 10% return
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Starting balance: $100,000
        # Contribution: $10,000
        # Balance after contribution: $110,000
        # No withdrawals (income > expenses)
        # Return: $110,000 * 0.10 = $11,000
        # Ending balance: $121,000
        
        assert abs(result.iloc[0]['401k_contribution'] - 10000) < 1
        assert abs(result.iloc[0]['401k_return'] - 11000) < 10  # Small tolerance for timing
        assert abs(result.iloc[0]['401k_balance'] - 121000) < 10
    
    def test_returns_applied_after_withdrawals(self):
        """Returns should be applied to the balance after withdrawals"""
        result = run_comprehensive_projection(
            current_age=68,
            target_age=69,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=1000,  # Only $12k/year
            accounts=[AccountBucket("IRA", 100000, 0.10, 1, "traditional_ira", 0)],  # 10% return
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Starting balance: $100,000
        # Income: $12,000
        # Expenses: ~$40,000
        # Deficit: ~$28,000
        # Withdrawal: ~$28,000
        # Balance after withdrawal: ~$72,000
        # Return: ~$72,000 * 0.10 = ~$7,200
        # Ending balance: ~$79,200
        
        withdrawal = result.iloc[0]['IRA_withdrawal']
        returns = result.iloc[0]['IRA_return']
        ending_balance = result.iloc[0]['IRA_balance']
        
        # Calculate expected return: (starting - withdrawal) * rate
        expected_return = (100000 - withdrawal) * 0.10
        
        assert abs(returns - expected_return) < 50  # Tolerance for RMDs
        assert abs(ending_balance - (100000 - withdrawal + returns)) < 50
    
    def test_different_return_rates_per_account(self):
        """Each account should have its own return rate"""
        result = run_comprehensive_projection(
            current_age=50,
            target_age=51,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[
                AccountBucket("Conservative", 100000, 0.05, 1, "traditional_ira", 0),  # 5%
                AccountBucket("Aggressive", 100000, 0.12, 2, "roth_ira", 0),  # 12%
            ],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Conservative: $100,000 * 0.05 = $5,000
        # Aggressive: $100,000 * 0.12 = $12,000
        
        assert abs(result.iloc[0]['Conservative_return'] - 5000) < 1
        assert abs(result.iloc[0]['Aggressive_return'] - 12000) < 1


class TestRMDs:
    """Test Required Minimum Distribution calculations"""
    
    def test_rmd_starting_age_varies_by_birth_year(self):
        """RMD starting age should vary based on birth year (SECURE Act)"""
        # Birth year 1948 (before 1949): RMD at 70
        assert get_rmd_starting_age(1948) == 70
        
        # Birth year 1950 (1949-1950): RMD at 72
        assert get_rmd_starting_age(1950) == 72
        
        # Birth year 1955 (1951-1959): RMD at 73
        assert get_rmd_starting_age(1955) == 73
        
        # Birth year 1960+ : RMD at 75
        assert get_rmd_starting_age(1960) == 75
        assert get_rmd_starting_age(1970) == 75
    
    def test_rmd_calculation_uses_irs_table(self):
        """RMD should be calculated using IRS Uniform Lifetime Table"""
        # Age 75, divisor 24.6
        rmd_75 = calculate_rmd_amount(246000, 75, 73)
        assert abs(rmd_75 - 10000) < 1  # 246000 / 24.6 = 10000
        
        # Age 80, divisor 20.2
        rmd_80 = calculate_rmd_amount(202000, 80, 73)
        assert abs(rmd_80 - 10000) < 1  # 202000 / 20.2 = 10000
        
        # Age 90, divisor 12.2
        rmd_90 = calculate_rmd_amount(122000, 90, 73)
        assert abs(rmd_90 - 10000) < 1  # 122000 / 12.2 = 10000
    
    def test_no_rmd_before_starting_age(self):
        """RMDs should not occur before the starting age"""
        # Age 72, but RMD starts at 73
        rmd = calculate_rmd_amount(100000, 72, 73)
        assert rmd == 0
    
    def test_rmd_applied_to_traditional_accounts(self):
        """RMDs should only apply to Traditional IRA and 401k"""
        # Person born in 1951, age 75 in 2026, RMD starts at 73
        result = run_comprehensive_projection(
            current_age=75,
            target_age=76,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[
                AccountBucket("IRA", 246000, 0.07, 1, "traditional_ira", 0),  # Subject to RMD
                AccountBucket("Roth", 200000, 0.07, 2, "roth_ira", 0),  # NOT subject to RMD
                AccountBucket("401k", 246000, 0.07, 3, "401k", 0),  # Subject to RMD
            ],
            expense_categories=[ExpenseCategory("Living", 30000, "CORE")],
        )
        
        # Age 75, divisor 24.6
        # IRA: 246000 / 24.6 ≈ 10000
        # Roth: 0 (not subject to RMD)
        # 401k: 246000 / 24.6 ≈ 10000
        
        assert abs(result.iloc[0]['IRA_rmd'] - 10000) < 100
        assert result.iloc[0]['Roth_rmd'] == 0
        assert abs(result.iloc[0]['401k_rmd'] - 10000) < 100
        assert abs(result.iloc[0]['total_rmds'] - 20000) < 200
    
    def test_rmd_reduces_account_balance(self):
        """RMD should reduce the account balance"""
        result = run_comprehensive_projection(
            current_age=75,
            target_age=76,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("IRA", 246000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 30000, "CORE")],
        )
        
        # Starting: $246,000
        # RMD: $10,000 (246000 / 24.6)
        # After RMD: $236,000
        # RMD covers part of expenses ($30k), so deficit = $30k - $24k (SS) - $10k (RMD) = -$4k (surplus)
        # Returns: $236,000 * 0.07 = $16,520
        # Ending: $236,000 + $16,520 = $252,520
        
        starting_balance = 246000
        rmd = result.iloc[0]['IRA_rmd']
        returns = result.iloc[0]['IRA_return']
        withdrawals = result.iloc[0]['IRA_withdrawal']
        ending_balance = result.iloc[0]['IRA_balance']
        
        # Balance should = starting - RMD - withdrawals + returns
        expected = starting_balance - rmd - withdrawals + returns
        assert abs(ending_balance - expected) < 1
    
    def test_rmd_adds_to_available_cash(self):
        """RMDs should count as income for covering expenses"""
        result = run_comprehensive_projection(
            current_age=75,
            target_age=76,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=1000,  # Only $12k/year
            accounts=[AccountBucket("IRA", 246000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 20000, "CORE")],
        )
        
        # Income: $12,000 (SS)
        # RMD: ~$10,000
        # Total available: $22,000
        # Expenses: ~$20,000
        # Should have small surplus, no additional withdrawals needed
        
        assert result.iloc[0]['total_rmds'] > 9000
        assert result.iloc[0]['total_withdrawals'] == 0  # RMD should cover the gap


class TestOneTimeEvents:
    """Test one-time event handling"""
    
    def test_one_time_withdrawal_reduces_account_balance(self):
        """A one-time withdrawal event should reduce the specified account"""
        events = [OneTimeEvent(2026, "Car purchase", 30000, "Taxable")]
        
        result = run_comprehensive_projection(
            current_age=50,
            target_age=52,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Taxable", 200000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
            events=events,
        )
        
        # Year 2026 (age 50): event occurs
        # Starting: $200,000
        # Event: -$30,000
        # Return: ($200,000 - $30,000) * 0.07 = $11,900
        # Ending: $200,000 - $30,000 + $11,900 = $181,900
        
        assert result.iloc[0]['event_amount'] == 30000
        assert result.iloc[0]['event_description'] == "Car purchase"
        # Balance after event and returns
        assert abs(result.iloc[0]['Taxable_balance'] - 181900) < 100
        
        # Year 2027 (age 51): no event
        assert result.iloc[1]['event_amount'] == 0
    
    def test_one_time_addition_increases_account_balance(self):
        """A one-time addition event (negative amount) should increase the account"""
        events = [OneTimeEvent(2027, "Inheritance", -100000, "Roth")]
        
        result = run_comprehensive_projection(
            current_age=50,
            target_age=52,
            current_work_income=100000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Roth", 150000, 0.07, 1, "roth_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
            events=events,
        )
        
        # Year 2026 (age 50): no event
        # Year 2027 (age 51): +$100,000 (negative amount = addition)
        
        assert result.iloc[0]['event_amount'] == 0  # Age 50
        assert result.iloc[1]['event_amount'] == -100000  # Age 51
        assert result.iloc[1]['event_description'] == "Inheritance"
        
        # Balance should be significantly higher in year 1 due to inheritance
        assert result.iloc[1]['Roth_balance'] > 250000


# ============================================================================
# INTEGRATION TESTS - Comprehensive Scenarios
# ============================================================================


class TestCompleteScenarios:
    """Test complete retirement scenarios end-to-end"""
    
    def test_simple_retirement_scenario(self):
        """Test a straightforward retirement with SS covering expenses"""
        result = run_comprehensive_projection(
            current_age=65,
            target_age=75,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=3000,  # $36k/year
            accounts=[AccountBucket("IRA", 500000, 0.07, 1, "traditional_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 35000, "CORE")],
            inflation_rate=0.025,
            ss_cola=0.025,
            max_age=75,  # Set max_age to stop at 75
        )
        
        # SS should roughly keep pace with expenses due to COLA matching inflation
        # Portfolio should grow due to minimal/no withdrawals
        
        assert len(result) == 11  # Ages 65-75
        assert not result['portfolio_depleted'].any()
        assert result.iloc[-1]['total_portfolio'] > 400000  # Should still be well-funded
    
    def test_portfolio_depletion_scenario(self):
        """Test scenario where portfolio runs out"""
        result = run_comprehensive_projection(
            current_age=65,
            target_age=85,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=1000,  # Only $12k/year
            accounts=[AccountBucket("IRA", 100000, 0.05, 1, "traditional_ira", 0)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Income: $12k, Expenses: $40k → deficit of $28k/year
        # Portfolio: $100k with 5% return
        # Should deplete within a few years
        
        depleted_rows = result[result['portfolio_depleted'] == True]
        assert len(depleted_rows) > 0, "Portfolio should deplete"
        
        depletion_age = depleted_rows.iloc[0]['age']
        assert depletion_age < 75, "Should deplete well before age 75"
    
    def test_working_years_to_retirement_transition(self):
        """Test transition from working years through retirement"""
        result = run_comprehensive_projection(
            current_age=63,
            target_age=70,
            current_work_income=80000,
            work_end_age=66,
            ss_start_age=67,
            ss_monthly_benefit=2500,
            accounts=[
                AccountBucket("401k", 400000, 0.07, 1, "401k", 15000, False),
                AccountBucket("Roth", 200000, 0.07, 2, "roth_ira", 7000, False),
            ],
            expense_categories=[
                ExpenseCategory("Living", 45000, "CORE"),
                ExpenseCategory("Travel", 15000, "FLEX"),
            ],
        )
        
        # Ages 63-65: Working with income and contributions
        # Age 66: Work stops, no more 401k contributions
        # Age 67: SS starts
        
        # Verify work income phases out
        assert result.iloc[0]['work_income'] > 0  # Age 63
        assert result.iloc[1]['work_income'] > 0  # Age 64
        assert result.iloc[2]['work_income'] > 0  # Age 65
        assert result.iloc[3]['work_income'] == 0  # Age 66
        
        # Verify SS starts
        assert result.iloc[0]['ss_income'] == 0  # Age 63
        assert result.iloc[1]['ss_income'] == 0  # Age 64
        assert result.iloc[2]['ss_income'] == 0  # Age 65
        assert result.iloc[3]['ss_income'] == 0  # Age 66
        assert result.iloc[4]['ss_income'] > 0  # Age 67
        
        # Verify 401k contributions stop at retirement
        assert result.iloc[0]['401k_contribution'] > 0  # Age 63
        assert result.iloc[1]['401k_contribution'] > 0  # Age 64
        assert result.iloc[2]['401k_contribution'] > 0  # Age 65
        assert result.iloc[3]['401k_contribution'] == 0  # Age 66 (retirement)
    
    def test_multiple_account_types_withdrawal_ordering(self):
        """Test complex scenario with multiple account types"""
        result = run_comprehensive_projection(
            current_age=75,  # Age 75 (born 1951) triggers RMDs at 73
            target_age=77,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=1500,
            accounts=[
                AccountBucket("Taxable", 50000, 0.06, 1, "taxable_brokerage", 0),
                AccountBucket("Roth", 100000, 0.07, 2, "roth_ira", 0),
                AccountBucket("401k", 200000, 0.07, 3, "401k", 0),
                AccountBucket("IRA", 150000, 0.07, 4, "traditional_ira", 0),
            ],
            expense_categories=[ExpenseCategory("Living", 50000, "CORE")],
        )
        
        # Should see withdrawals prioritized: Taxable → Roth → 401k → IRA
        # Also should see RMDs from 401k and IRA (age 75, born 1951, RMD starts at 73)
        
        assert result.iloc[0]['total_rmds'] > 0  # Should have RMDs at age 75
        assert result.iloc[0]['total_withdrawals'] > 0  # Should have deficit withdrawals
        
        # Priority 1 (Taxable) should be depleted first
        if result.iloc[0]['Taxable_withdrawal'] > 0:
            assert result.iloc[0]['Taxable_withdrawal'] <= 50000


# ============================================================================
# PROPERTY-BASED TESTS - Using Hypothesis
# ============================================================================


@composite
def account_strategy(draw):
    """Generate random but valid AccountBucket"""
    name = draw(st.sampled_from(["401k", "IRA", "Roth", "Taxable", "Savings"]))
    balance = draw(st.floats(min_value=0, max_value=2000000))
    annual_return = draw(st.floats(min_value=0.00, max_value=0.15))
    priority = draw(st.integers(min_value=1, max_value=5))
    account_type = draw(st.sampled_from(["401k", "traditional_ira", "roth_ira", "taxable_brokerage"]))
    planned_contribution = draw(st.floats(min_value=0, max_value=25000))
    continue_post_retirement = draw(st.booleans())
    
    return AccountBucket(name, balance, annual_return, priority, account_type, 
                         planned_contribution, continue_post_retirement)


@composite
def expense_strategy(draw):
    """Generate random but valid ExpenseCategory"""
    name = draw(st.sampled_from(["Housing", "Food", "Travel", "Healthcare", "Entertainment"]))
    annual_amount = draw(st.floats(min_value=1000, max_value=100000))
    category_type = draw(st.sampled_from(["CORE", "FLEX"]))
    
    return ExpenseCategory(name, annual_amount, category_type)


class TestPropertyBasedInvariants:
    """Property-based tests using hypothesis to verify invariants hold across random scenarios"""
    
    @given(
        current_age=st.integers(min_value=25, max_value=75),
        work_end_age_offset=st.integers(min_value=0, max_value=30),
        current_work_income=st.floats(min_value=0, max_value=300000),
        ss_monthly_benefit=st.floats(min_value=0, max_value=5000),
        initial_balance=st.floats(min_value=10000, max_value=2000000),
        annual_return=st.floats(min_value=0.00, max_value=0.15),
        annual_expenses=st.floats(min_value=10000, max_value=150000),
    )
    @settings(max_examples=100, deadline=2000)
    def test_portfolio_balance_never_negative(
        self, current_age, work_end_age_offset, current_work_income,
        ss_monthly_benefit, initial_balance, annual_return, annual_expenses
    ):
        """Portfolio balance should never go negative (will hit zero and stop)"""
        work_end_age = current_age + work_end_age_offset
        ss_start_age = min(work_end_age, current_age + 2)  # Start SS soon
        target_age = min(current_age + 5, 95)  # Short projection
        
        result = run_comprehensive_projection(
            current_age=current_age,
            target_age=target_age,
            current_work_income=current_work_income,
            work_end_age=work_end_age,
            ss_start_age=ss_start_age,
            ss_monthly_benefit=ss_monthly_benefit,
            accounts=[AccountBucket("Test", initial_balance, annual_return, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", annual_expenses, "CORE")],
        )
        
        # All portfolio values should be >= 0
        assert (result['total_portfolio'] >= 0).all(), "Portfolio balance went negative"
        assert (result['Test_balance'] >= -0.01).all(), "Account balance went negative (beyond rounding)"
    
    @given(
        current_age=st.integers(min_value=25, max_value=70),
        initial_balance=st.floats(min_value=50000, max_value=1000000),
        annual_expenses=st.floats(min_value=20000, max_value=80000),
        annual_return=st.floats(min_value=0.02, max_value=0.12),
    )
    @settings(max_examples=100, deadline=2000)
    def test_high_income_means_no_withdrawals_during_work(
        self, current_age, initial_balance, annual_expenses, annual_return
    ):
        """With income significantly exceeding expenses, should never withdraw during working years"""
        work_income = annual_expenses * 2  # Double expenses
        
        # Limit age to avoid RMD complications
        assume(current_age < 70)
        
        result = run_comprehensive_projection(
            current_age=current_age,
            target_age=current_age + 5,
            current_work_income=work_income,
            work_end_age=current_age + 10,  # Still working throughout
            ss_start_age=67,
            ss_monthly_benefit=0,
            accounts=[AccountBucket("Test", initial_balance, annual_return, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", annual_expenses, "CORE")],
            max_age=current_age + 6,  # Ensure projection completes
        )
        
        # With income = 2x expenses, should never need to withdraw
        assert (result['total_withdrawals'] == 0).all(), "Should not withdraw when income >> expenses"
    
    @given(
        current_age=st.integers(min_value=30, max_value=60),
        inflation_rate=st.floats(min_value=0.00, max_value=0.10),
        base_expenses=st.floats(min_value=20000, max_value=80000),
    )
    @settings(max_examples=100, deadline=2000)
    def test_expenses_grow_monotonically_with_inflation(
        self, current_age, inflation_rate, base_expenses
    ):
        """Expenses should grow monotonically at the inflation rate"""
        assume(inflation_rate > 0)  # Only test positive inflation
        
        result = run_comprehensive_projection(
            current_age=current_age,
            target_age=current_age + 10,
            current_work_income=base_expenses * 2,
            work_end_age=current_age + 20,
            ss_start_age=67,
            ss_monthly_benefit=0,
            accounts=[AccountBucket("Test", 500000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", base_expenses, "CORE")],
            inflation_rate=inflation_rate,
        )
        
        # Core expenses should increase each year
        core_expenses = result['core_expenses'].values
        for i in range(1, len(core_expenses)):
            ratio = core_expenses[i] / core_expenses[i-1]
            expected_ratio = 1 + inflation_rate
            assert abs(ratio - expected_ratio) < 0.01, f"Expense growth rate mismatch: {ratio} vs {expected_ratio}"
    
    @given(
        current_age=st.integers(min_value=30, max_value=60),
        work_income=st.floats(min_value=50000, max_value=200000),
        inflation_rate=st.floats(min_value=0.00, max_value=0.10),
    )
    @settings(max_examples=100, deadline=2000)
    def test_work_income_grows_monotonically_while_working(
        self, current_age, work_income, inflation_rate
    ):
        """Work income should grow monotonically at inflation rate while working"""
        assume(inflation_rate > 0)
        assume(current_age < 95)  # Ensure we don't hit max_age issues
        
        result = run_comprehensive_projection(
            current_age=current_age,
            target_age=current_age + 10,
            current_work_income=work_income,
            work_end_age=current_age + 15,  # Working throughout projection
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Test", 500000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
            inflation_rate=inflation_rate,
            max_age=current_age + 20,  # Ensure projection doesn't stop early
        )
        
        # Work income should increase each year (only for years where still working)
        work_incomes = result[result['work_income'] > 0]['work_income'].values
        for i in range(1, len(work_incomes)):
            ratio = work_incomes[i] / work_incomes[i-1]
            expected_ratio = 1 + inflation_rate
            assert abs(ratio - expected_ratio) < 0.01, f"Income growth rate mismatch"
    
    @given(
        current_age=st.integers(min_value=25, max_value=70),
        initial_balance=st.floats(min_value=100000, max_value=1000000),
        annual_return=st.floats(min_value=0.03, max_value=0.12),
    )
    @settings(max_examples=100, deadline=2000)
    def test_no_transactions_means_compound_growth(
        self, current_age, initial_balance, annual_return
    ):
        """With no transactions (income=expenses), balance should grow purely by returns"""
        annual_income = 50000
        annual_expenses = 50000  # Exactly balanced
        
        # Avoid ages where RMDs would kick in
        assume(current_age < 70)
        
        result = run_comprehensive_projection(
            current_age=current_age,
            target_age=current_age + 3,
            current_work_income=annual_income,
            work_end_age=current_age + 10,
            ss_start_age=67,
            ss_monthly_benefit=0,
            accounts=[AccountBucket("Test", initial_balance, annual_return, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", annual_expenses, "CORE")],
            inflation_rate=0,  # No inflation to keep it simple
            max_age=current_age + 5,  # Ensure projection completes
        )
        
        # Each year, balance should grow by return rate (with no net transactions)
        # Year 0: initial_balance * (1 + return)
        # Year 1: initial_balance * (1 + return)^2
        # Year 2: initial_balance * (1 + return)^3
        
        for i in range(len(result)):
            expected = initial_balance * ((1 + annual_return) ** (i + 1))
            actual = result.iloc[i]['Test_balance']
            # Allow 2% tolerance due to timing of transactions
            assert abs(actual - expected) / expected < 0.02, \
                f"Year {i}: Expected {expected}, got {actual}"
    
    @given(
        ss_monthly_benefit=st.floats(min_value=1000, max_value=4000),
        ss_cola=st.floats(min_value=0.00, max_value=0.05),
    )
    @settings(max_examples=100, deadline=2000)
    def test_ss_grows_monotonically_with_cola(self, ss_monthly_benefit, ss_cola):
        """Social Security should grow monotonically at COLA rate"""
        assume(ss_cola > 0)
        
        result = run_comprehensive_projection(
            current_age=67,
            target_age=72,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=ss_monthly_benefit,
            accounts=[AccountBucket("Test", 500000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", 30000, "CORE")],
            ss_cola=ss_cola,
        )
        
        ss_incomes = result['ss_income'].values
        for i in range(1, len(ss_incomes)):
            ratio = ss_incomes[i] / ss_incomes[i-1]
            expected_ratio = 1 + ss_cola
            assert abs(ratio - expected_ratio) < 0.01, f"SS COLA growth rate mismatch"
    
    @given(
        current_age=st.integers(min_value=30, max_value=60),
        work_end_age_offset=st.integers(min_value=5, max_value=35),
    )
    @settings(max_examples=100, deadline=2000)
    def test_work_income_zero_after_work_end_age(self, current_age, work_end_age_offset):
        """Work income should be exactly zero after work_end_age"""
        work_end_age = current_age + work_end_age_offset
        target_age = min(work_end_age + 5, 95)
        
        result = run_comprehensive_projection(
            current_age=current_age,
            target_age=target_age,
            current_work_income=80000,
            work_end_age=work_end_age,
            ss_start_age=max(work_end_age, 67),
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Test", 500000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        for i in range(len(result)):
            age = result.iloc[i]['age']
            work_income = result.iloc[i]['work_income']
            if age >= work_end_age:
                assert work_income == 0, f"Age {age}: work_income should be 0 but was {work_income}"
    
    @given(
        flex_reduction=st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, deadline=2000)
    def test_flex_multiplier_respects_max_reduction(self, flex_reduction):
        """FLEX multiplier should never go below (1 - max_flex_reduction)"""
        result = run_comprehensive_projection(
            current_age=68,
            target_age=70,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=500,  # Very low to force reduction
            accounts=[AccountBucket("Test", 100000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[
                ExpenseCategory("Core", 10000, "CORE"),
                ExpenseCategory("Flex", 50000, "FLEX"),
            ],
            max_flex_reduction=flex_reduction,
        )
        
        min_allowed_multiplier = 1 - flex_reduction
        for i in range(len(result)):
            actual_multiplier = result.iloc[i]['flex_multiplier']
            assert actual_multiplier >= min_allowed_multiplier - 0.001, \
                f"FLEX multiplier {actual_multiplier} below minimum {min_allowed_multiplier}"
            assert actual_multiplier <= 1.0, f"FLEX multiplier {actual_multiplier} above 1.0"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_initial_balance(self):
        """Test with zero initial portfolio balance"""
        result = run_comprehensive_projection(
            current_age=30,
            target_age=35,
            current_work_income=60000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Empty", 0, 0.07, 1, "taxable_brokerage", 5000)],  # Contributions
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Should build up balance through contributions
        assert result.iloc[0]['Empty_balance'] > 0  # Should have contribution + returns
        assert result.iloc[-1]['Empty_balance'] > 25000  # 5 years * $5k
    
    def test_zero_return_rate(self):
        """Test with zero investment returns"""
        result = run_comprehensive_projection(
            current_age=30,
            target_age=32,
            current_work_income=80000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("NoGrowth", 100000, 0.0, 1, "taxable_brokerage", 0)],  # 0% return
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # All returns should be zero
        assert result.iloc[0]['NoGrowth_return'] == 0
        assert result.iloc[1]['NoGrowth_return'] == 0
        assert result.iloc[2]['NoGrowth_return'] == 0
    
    def test_negative_return_rate(self):
        """Test with negative investment returns (market loss)"""
        result = run_comprehensive_projection(
            current_age=30,
            target_age=31,
            current_work_income=80000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Losing", 100000, -0.10, 1, "taxable_brokerage", 0)],  # -10% return
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
        )
        
        # Should lose money
        assert result.iloc[0]['Losing_return'] < 0
        assert result.iloc[0]['Losing_balance'] < 100000
    
    def test_max_age_cutoff(self):
        """Test projection stops at max_age"""
        result = run_comprehensive_projection(
            current_age=30,
            target_age=120,  # Beyond max_age
            current_work_income=80000,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Test", 500000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
            max_age=110,
        )
        
        # Should stop at max_age
        assert result.iloc[-1]['age'] <= 110
    
    def test_very_high_expenses(self):
        """Test with expenses far exceeding income and portfolio"""
        result = run_comprehensive_projection(
            current_age=68,
            target_age=75,
            current_work_income=0,
            work_end_age=65,
            ss_start_age=67,
            ss_monthly_benefit=2000,
            accounts=[AccountBucket("Small", 50000, 0.07, 1, "taxable_brokerage", 0)],
            expense_categories=[ExpenseCategory("Living", 200000, "CORE")],  # Unrealistically high
        )
        
        # Should deplete very quickly
        assert result['portfolio_depleted'].any()
        depleted_age = result[result['portfolio_depleted'] == True].iloc[0]['age']
        assert depleted_age <= 69  # Should run out within a year or two


class TestCanContributeFunction:
    """Test the can_contribute helper function in isolation"""
    
    def test_401k_stops_at_work_end_age(self):
        """401k contributions stop at work_end_age regardless of continue_post_retirement"""
        assert can_contribute("401k", 64, 65, False) == True
        assert can_contribute("401k", 65, 65, False) == False
        assert can_contribute("401k", 65, 65, True) == False  # Still stops for 401k
        assert can_contribute("401k", 66, 65, True) == False
    
    def test_traditional_ira_stops_at_73(self):
        """Traditional IRA stops at 73 if working, earlier if retired without continue flag"""
        # Working, before 73
        assert can_contribute("traditional_ira", 70, 75, False) == True
        assert can_contribute("traditional_ira", 72, 75, False) == True
        
        # At or after 73
        assert can_contribute("traditional_ira", 73, 75, False) == False
        assert can_contribute("traditional_ira", 74, 75, False) == False
        
        # Retired, without continue flag
        assert can_contribute("traditional_ira", 70, 65, False) == False
        
        # Retired, with continue flag
        assert can_contribute("traditional_ira", 70, 65, True) == True
        assert can_contribute("traditional_ira", 72, 65, True) == True
        assert can_contribute("traditional_ira", 73, 65, True) == False  # Age limit
    
    def test_roth_ira_no_age_limit(self):
        """Roth IRA has no age limit, only depends on work status and continue flag"""
        # Working, should allow
        assert can_contribute("roth_ira", 70, 75, False) == True
        assert can_contribute("roth_ira", 80, 85, False) == True
        
        # Retired, without continue flag
        assert can_contribute("roth_ira", 70, 65, False) == False
        
        # Retired, with continue flag (should continue indefinitely)
        assert can_contribute("roth_ira", 70, 65, True) == True
        assert can_contribute("roth_ira", 80, 65, True) == True
        assert can_contribute("roth_ira", 90, 65, True) == True
    
    def test_taxable_brokerage_no_limit(self):
        """Taxable brokerage has no age limit"""
        # Working
        assert can_contribute("taxable_brokerage", 70, 75, False) == True
        
        # Retired, without continue flag
        assert can_contribute("taxable_brokerage", 70, 65, False) == False
        
        # Retired, with continue flag
        assert can_contribute("taxable_brokerage", 70, 65, True) == True
        assert can_contribute("taxable_brokerage", 90, 65, True) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
