"""
Retirement Planning Calculations

This module contains all the financial calculations for retirement planning.
Unlike spreadsheet formulas, these functions are:
- Clearly documented with what they do
- Easy to test and verify
- Transparent in their logic
- Reusable across different scenarios

Key Features:
- Multiple account buckets (401k, Roth IRA) with priority ordering
- CORE vs FLEX expense categories with flexible spending reduction
- Social Security with COLA adjustments
- Surplus reinvestment and withdrawal ordering
- Transparent year-by-year projection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class AccountBucket:
    """Represents an investment account (401k, Roth, etc.)"""
    name: str
    balance: float
    annual_return: float  # Total return (growth + dividends)
    contribution_share: float  # % of surplus to allocate (0-1)
    priority: int  # Withdrawal order (1 = first)


@dataclass
class ExpenseCategory:
    """Represents a spending category"""
    name: str
    annual_amount: float
    category_type: str  # 'CORE' or 'FLEX'


@dataclass
class OneTimeEvent:
    """Represents a one-time financial event"""
    year: int
    description: str
    amount: float  # Positive = expense, Negative = windfall


def run_comprehensive_projection(
    # Personal info
    current_age: int,
    target_age: int,  # Typically 90
    
    # Work income
    current_work_income: float,
    work_end_age: int,
    
    # Social Security
    ss_start_age: int,
    ss_monthly_benefit: float,
    
    # Investment accounts
    accounts: List[AccountBucket],
    
    # Expenses
    expense_categories: List[ExpenseCategory],
    
    # Optional parameters with defaults
    work_income_growth: float = 0.0,  # Annual % change
    ss_cola: float = 0.025,  # Annual COLA increase
    max_flex_reduction: float = 0.50,  # Max % to cut flexible spending
    events: List[OneTimeEvent] = None,  # One-time events
    inflation_rate: float = 0.03,  # Assumptions
    max_age: int = 110  # Extension years for cushion analysis
) -> pd.DataFrame:
    """
    Comprehensive year-by-year retirement projection following the spec.
    
    This is the "Engine Sheet" - performs all annual calculations:
    - Inflates expenses
    - Applies income (work + Social Security)
    - Handles one-time events
    - Reduces flexible spending if needed
    - Reinvests surplus across accounts
    - Withdraws from accounts in priority order
    - Applies investment returns
    - Detects portfolio depletion
    
    Returns:
        DataFrame with complete year-by-year projection
    """
    if events is None:
        events = []
    
    # Get current year (we'll use age-based indexing)
    projection_years = max_age - current_age + 1
    
    # Initialize storage
    results = []
    
    # Sort accounts by priority for withdrawal ordering
    sorted_accounts = sorted(accounts, key=lambda a: a.priority)
    
    # Initialize account balances (will be modified each year)
    account_balances = {acc.name: acc.balance for acc in accounts}
    
    # Calculate initial expense totals
    core_expenses_base = sum(e.annual_amount for e in expense_categories if e.category_type == 'CORE')
    flex_expenses_base = sum(e.annual_amount for e in expense_categories if e.category_type == 'FLEX')
    
    # Track year-by-year
    for year_offset in range(projection_years):
        age = current_age + year_offset
        year = 2026 + year_offset  # Assuming current year is 2026
        
        # --- INCOME CALCULATION ---
        
        # Work income (ends at work_end_age)
        if age < work_end_age:
            work_income = current_work_income * ((1 + work_income_growth) ** year_offset)
        else:
            work_income = 0
        
        # Social Security (starts at ss_start_age)
        if age >= ss_start_age:
            years_on_ss = age - ss_start_age
            ss_income = ss_monthly_benefit * 12 * ((1 + ss_cola) ** years_on_ss)
        else:
            ss_income = 0
        
        total_income = work_income + ss_income
        
        # --- EXPENSE CALCULATION ---
        
        # Inflate expenses from base year
        inflation_multiplier = (1 + inflation_rate) ** year_offset
        core_expenses = core_expenses_base * inflation_multiplier
        flex_expenses_full = flex_expenses_base * inflation_multiplier
        
        # --- ONE-TIME EVENTS ---
        
        event_amount = 0
        event_description = ""
        for event in events:
            if event.year == year:
                event_amount = event.amount
                event_description = event.description
                break
        
        # --- SURPLUS/DEFICIT LOGIC ---
        
        # Start with full flexible expenses
        flex_multiplier = 1.0
        flex_expenses_actual = flex_expenses_full
        
        # Total spending (before flex reduction)
        total_expenses_full = core_expenses + flex_expenses_full + event_amount
        
        # Calculate initial surplus/deficit
        surplus_deficit = total_income - total_expenses_full
        
        # --- FLEXIBLE SPENDING REDUCTION ---
        
        if surplus_deficit < 0:  # Deficit
            # Try to cover deficit by reducing flexible spending
            deficit = abs(surplus_deficit)
            max_flex_cut = flex_expenses_full * max_flex_reduction
            
            if deficit <= max_flex_cut:
                # Can cover entirely with flex reduction
                flex_reduction = deficit
                flex_expenses_actual = flex_expenses_full - flex_reduction
                flex_multiplier = flex_expenses_actual / flex_expenses_full if flex_expenses_full > 0 else 1.0
                surplus_deficit = 0  # Now balanced
            else:
                # Reduce flex to minimum, still have deficit
                flex_expenses_actual = flex_expenses_full * (1 - max_flex_reduction)
                flex_multiplier = 1 - max_flex_reduction
                surplus_deficit = total_income - (core_expenses + flex_expenses_actual + event_amount)
        
        total_expenses_actual = core_expenses + flex_expenses_actual + event_amount
        
        # Recalculate surplus/deficit after flex adjustment
        surplus_deficit = total_income - total_expenses_actual
        
        # --- CONTRIBUTIONS (Surplus Reinvestment) ---
        
        contributions = {}
        total_contributions = 0
        
        if surplus_deficit > 0 and age < work_end_age:  # Only contribute while working
            # Distribute surplus according to contribution shares
            total_share = sum(acc.contribution_share for acc in accounts)
            for acc in accounts:
                if total_share > 0:
                    contrib = surplus_deficit * (acc.contribution_share / total_share)
                else:
                    contrib = 0
                contributions[acc.name] = contrib
                account_balances[acc.name] += contrib
                total_contributions += contrib
        
        # --- WITHDRAWALS (Deficit Coverage) ---
        
        withdrawals = {}
        total_withdrawals = 0
        
        if surplus_deficit < 0:  # Deficit remains after flex reduction
            deficit_to_cover = abs(surplus_deficit)
            
            # Withdraw from accounts in priority order
            for acc in sorted_accounts:
                if deficit_to_cover <= 0:
                    withdrawals[acc.name] = 0
                    continue
                
                available = account_balances[acc.name]
                withdrawal = min(deficit_to_cover, available)
                
                withdrawals[acc.name] = withdrawal
                account_balances[acc.name] -= withdrawal
                total_withdrawals += withdrawal
                deficit_to_cover -= withdrawal
        else:
            for acc in accounts:
                withdrawals[acc.name] = 0
        
        # --- INVESTMENT RETURNS ---
        
        returns = {}
        for acc in accounts:
            annual_return = account_balances[acc.name] * acc.annual_return
            returns[acc.name] = annual_return
            account_balances[acc.name] += annual_return
        
        # --- PORTFOLIO STATUS ---
        
        total_portfolio = sum(account_balances.values())
        portfolio_depleted = total_portfolio <= 0
        
        # --- RECORD YEAR ---
        
        year_data = {
            'year': year,
            'age': age,
            'work_income': work_income,
            'ss_income': ss_income,
            'total_income': total_income,
            'core_expenses': core_expenses,
            'flex_expenses_full': flex_expenses_full,
            'flex_multiplier': flex_multiplier,
            'flex_expenses_actual': flex_expenses_actual,
            'event_amount': event_amount,
            'event_description': event_description,
            'total_expenses': total_expenses_actual,
            'surplus_deficit': total_income - total_expenses_actual,
            'total_contributions': total_contributions,
            'total_withdrawals': total_withdrawals,
            'total_portfolio': total_portfolio,
            'portfolio_depleted': portfolio_depleted
        }
        
        # Add individual account balances
        for acc in accounts:
            year_data[f'{acc.name}_balance'] = account_balances[acc.name]
            year_data[f'{acc.name}_contribution'] = contributions.get(acc.name, 0)
            year_data[f'{acc.name}_withdrawal'] = withdrawals.get(acc.name, 0)
            year_data[f'{acc.name}_return'] = returns.get(acc.name, 0)
        
        results.append(year_data)
        
        # Stop if portfolio depleted
        if portfolio_depleted:
            break
    
    return pd.DataFrame(results)


def analyze_retirement_plan(
    projection_df: pd.DataFrame,
    target_age: int = 90
) -> Dict:
    """
    Analyze a retirement projection and return key metrics.
    
    Returns dictionary with:
    - run_out_age: Age when money runs out (or None if never)
    - run_out_year: Year when money runs out
    - cushion_years: Years beyond target_age
    - status: 'ON TRACK' or 'AT RISK'
    - warnings: List of warning messages
    """
    if projection_df.empty:
        return {
            'run_out_age': None,
            'run_out_year': None,
            'cushion_years': 0,
            'status': 'AT RISK',
            'warnings': ['No projection data']
        }
    
    warnings = []
    
    # Find when portfolio depletes
    depleted = projection_df[projection_df['portfolio_depleted'] == True]
    
    if len(depleted) > 0:
        run_out_age = depleted.iloc[0]['age']
        run_out_year = depleted.iloc[0]['year']
    else:
        # Money never runs out
        run_out_age = None
        run_out_year = None
    
    # Calculate cushion
    if run_out_age is None:
        # Project to end, use last age
        cushion_years = projection_df.iloc[-1]['age'] - target_age
    elif run_out_age >= target_age:
        cushion_years = run_out_age - target_age
    else:
        cushion_years = run_out_age - target_age  # Will be negative
    
    # Determine status
    if run_out_age is None or run_out_age >= target_age:
        status = 'ON TRACK'
    else:
        status = 'AT RISK'
        warnings.append(f'Portfolio depletes at age {run_out_age}, {target_age - run_out_age} years before target')
    
    # Check for excessive flexible spending reduction
    avg_flex_multiplier = projection_df['flex_multiplier'].mean()
    if avg_flex_multiplier < 0.8:
        warnings.append(f'Average flexible spending reduced to {avg_flex_multiplier*100:.0f}% of planned')
    
    # Check for early withdrawals
    working_years = projection_df[projection_df['work_income'] > 0]
    if len(working_years) > 0 and working_years['total_withdrawals'].sum() > 0:
        warnings.append('Withdrawing from portfolio while still working')
    
    return {
        'run_out_age': run_out_age,
        'run_out_year': run_out_year,
        'cushion_years': cushion_years,
        'status': status,
        'warnings': warnings,
        'final_balance': projection_df.iloc[-1]['total_portfolio'] if not projection_df.empty else 0
    }


# ===== LEGACY FUNCTIONS (kept for compatibility) =====


def calculate_future_value(
    present_value: float,
    annual_return: float,
    years: int,
    annual_contribution: float = 0
) -> float:
    """
    Calculate future value of an investment with compound growth.
    
    Args:
        present_value: Current account balance
        annual_return: Expected annual return rate (e.g., 0.07 for 7%)
        years: Number of years to project
        annual_contribution: Amount added each year (at year start)
    
    Returns:
        Future value of the investment
    
    Example:
        >>> calculate_future_value(100000, 0.07, 10, 5000)
        # $100k growing at 7% for 10 years with $5k/year contributions
    """
    if years == 0:
        return present_value
    
    # Future value of present amount
    fv_present = present_value * ((1 + annual_return) ** years)
    
    # Future value of annuity (contributions)
    if annual_contribution > 0 and annual_return != 0:
        fv_contributions = annual_contribution * (
            ((1 + annual_return) ** years - 1) / annual_return
        )
    else:
        fv_contributions = annual_contribution * years
    
    return fv_present + fv_contributions


def adjust_for_inflation(
    amount: float,
    inflation_rate: float,
    years: int
) -> float:
    """
    Adjust an amount for inflation to get real (today's dollars) value.
    
    Args:
        amount: Future dollar amount
        inflation_rate: Annual inflation rate (e.g., 0.03 for 3%)
        years: Number of years in the future
    
    Returns:
        Amount in today's dollars
    """
    return amount / ((1 + inflation_rate) ** years)


def calculate_required_savings(
    target_amount: float,
    years_to_save: int,
    current_savings: float,
    annual_return: float
) -> float:
    """
    Calculate annual contribution needed to reach a target amount.
    
    Args:
        target_amount: Goal amount to reach
        years_to_save: Number of years until retirement
        current_savings: Current account balance
        annual_return: Expected annual return rate
    
    Returns:
        Required annual contribution
    """
    if years_to_save == 0:
        return target_amount - current_savings
    
    # Future value of current savings
    fv_current = current_savings * ((1 + annual_return) ** years_to_save)
    
    # Amount still needed
    needed = target_amount - fv_current
    
    if needed <= 0:
        return 0
    
    # Solve for payment (PMT) in future value of annuity formula
    if annual_return == 0:
        return needed / years_to_save
    
    payment = needed / (((1 + annual_return) ** years_to_save - 1) / annual_return)
    return payment


def project_retirement_balance(
    starting_balance: float,
    annual_withdrawal: float,
    annual_return: float,
    years: int,
    inflation_adjusted: bool = True,
    inflation_rate: float = 0.03
) -> pd.DataFrame:
    """
    Project retirement account balance over time with withdrawals.
    
    Args:
        starting_balance: Balance at start of retirement
        annual_withdrawal: Amount withdrawn each year
        annual_return: Expected return during retirement
        years: Number of years to project
        inflation_adjusted: Whether to increase withdrawals with inflation
        inflation_rate: Annual inflation rate (if inflation_adjusted=True)
    
    Returns:
        DataFrame with columns: year, balance, withdrawal, growth
    """
    data = []
    balance = starting_balance
    withdrawal = annual_withdrawal
    
    for year in range(1, years + 1):
        # Adjust withdrawal for inflation if needed
        if inflation_adjusted and year > 1:
            withdrawal *= (1 + inflation_rate)
        
        # Withdrawal happens at start of year
        balance -= withdrawal
        
        # Investment grows during the year
        growth = balance * annual_return
        balance += growth
        
        data.append({
            'year': year,
            'balance': balance,
            'withdrawal': withdrawal,
            'growth': growth
        })
        
        # Stop if we run out of money
        if balance <= 0:
            break
    
    return pd.DataFrame(data)


def calculate_safe_withdrawal_rate(
    retirement_balance: float,
    years_in_retirement: int,
    annual_return: float,
    inflation_rate: float = 0.03,
    final_balance_target: float = 0
) -> float:
    """
    Calculate the initial annual withdrawal amount that will last the desired period.
    Uses the classic 4% rule concept but allows customization.
    
    Args:
        retirement_balance: Starting balance at retirement
        years_in_retirement: Expected years in retirement
        annual_return: Expected annual return during retirement
        inflation_rate: Rate to increase withdrawals each year
        final_balance_target: Desired balance at end (legacy/buffer)
    
    Returns:
        Safe annual withdrawal amount (first year)
    """
    # This is a simplified calculation
    # For a more accurate version, we'd use binary search or solver
    
    # Start with 4% rule as initial guess
    withdrawal = retirement_balance * 0.04
    
    # Iterate to refine (simple approach)
    for _ in range(20):  # Max iterations
        projection = project_retirement_balance(
            retirement_balance,
            withdrawal,
            annual_return,
            years_in_retirement,
            inflation_adjusted=True,
            inflation_rate=inflation_rate
        )
        
        if len(projection) < years_in_retirement:
            # Ran out of money too soon
            withdrawal *= 0.95
        else:
            final_balance = projection.iloc[-1]['balance']
            if final_balance < final_balance_target:
                withdrawal *= 0.98
            elif final_balance > final_balance_target * 1.5:
                withdrawal *= 1.02
            else:
                break  # Close enough
    
    return withdrawal


def calculate_retirement_readiness(
    current_age: int,
    retirement_age: int,
    current_savings: float,
    annual_contribution: float,
    pre_retirement_return: float,
    post_retirement_return: float,
    desired_annual_spending: float,
    life_expectancy: int,
    inflation_rate: float = 0.03
) -> Dict:
    """
    Comprehensive retirement readiness analysis.
    
    Returns a dictionary with:
    - projected_balance: Balance at retirement
    - years_money_lasts: How long the money will last
    - recommended_spending: Safe annual spending amount
    - shortfall: Gap between desired and safe spending (if any)
    """
    years_to_retirement = retirement_age - current_age
    years_in_retirement = life_expectancy - retirement_age
    
    # Project balance at retirement
    projected_balance = calculate_future_value(
        current_savings,
        pre_retirement_return,
        years_to_retirement,
        annual_contribution
    )
    
    # Test how long money lasts with desired spending
    projection = project_retirement_balance(
        projected_balance,
        desired_annual_spending,
        post_retirement_return,
        years_in_retirement,
        inflation_adjusted=True,
        inflation_rate=inflation_rate
    )
    
    years_money_lasts = len(projection)
    
    # Calculate safe withdrawal amount
    safe_withdrawal = calculate_safe_withdrawal_rate(
        projected_balance,
        years_in_retirement,
        post_retirement_return,
        inflation_rate
    )
    
    shortfall = max(0, desired_annual_spending - safe_withdrawal)
    
    return {
        'projected_balance': projected_balance,
        'years_money_lasts': years_money_lasts,
        'recommended_spending': safe_withdrawal,
        'shortfall': shortfall,
        'is_ready': years_money_lasts >= years_in_retirement and shortfall == 0
    }
