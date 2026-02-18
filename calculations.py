"""
Retirement Planning Calculations

Year-by-year financial projection engine.

Key Features:
- Account types with contribution rules (401k, IRA, Roth IRA, Taxable)
- Planned annual contributions (user-specified, flat dollar amounts)
- CORE vs FLEX expense categories with flexible spending reduction
- Social Security with COLA adjustments
- Deficit withdrawal ordering by account priority
- Transparent year-by-year projection
"""

import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class AccountBucket:
    """Represents an investment account (401k, Roth IRA, etc.)"""
    name: str
    balance: float
    annual_return: float  # Total return (growth + dividends), e.g. 0.07
    priority: int  # Withdrawal order (1 = first)
    account_type: str  # '401k', 'traditional_ira', 'roth_ira', 'taxable_brokerage'
    planned_contribution: float  # Annual dollar amount the user plans to add
    continue_post_retirement: bool = False  # Continue contributions after work_end_age


@dataclass
class ExpenseCategory:
    """Represents a spending category"""
    name: str
    annual_amount: float
    category_type: str  # 'CORE' or 'FLEX'


@dataclass
class OneTimeEvent:
    """Represents a one-time portfolio transaction in a specific account"""
    year: int
    description: str
    amount: float  # Positive = withdrawal, Negative = addition
    account_name: str  # Which account to affect


# When contributions must stop, by account type.
# 'work_end_age' means use the user's work_end_age setting.
# An integer means stop at that age.
# None means contributions never stop.
CONTRIBUTION_STOP_RULES = {
    '401k': 'work_end_age',
    'traditional_ira': 73,
    'roth_ira': None,
    'taxable_brokerage': None,
}

# Human-readable labels for display
ACCOUNT_TYPE_LABELS = {
    '401k': '401(k)',
    'traditional_ira': 'Traditional IRA',
    'roth_ira': 'Roth IRA',
    'taxable_brokerage': 'Taxable Brokerage',
}

# IRS Uniform Lifetime Table for RMD calculations (Publication 590-B)
# Maps age to distribution period (divisor)
RMD_LIFETIME_TABLE = {
    70: 27.4, 71: 26.5, 72: 25.6,  # Added for early RMD ages
    73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0, 79: 21.1, 
    80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0, 86: 15.2,
    87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8, 93: 10.1,
    94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8, 100: 6.4,
    101: 6.0, 102: 5.6, 103: 5.2, 104: 4.9, 105: 4.6, 106: 4.3, 107: 4.1,
    108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3, 113: 3.1, 114: 3.0,
    115: 2.9, 116: 2.8, 117: 2.7, 118: 2.5, 119: 2.3, 120: 2.0
}

# Account types subject to RMDs
RMD_ACCOUNT_TYPES = {'401k', 'traditional_ira'}


def get_rmd_starting_age(birth_year: int) -> int:
    """Determine RMD starting age based on birth year.
    
    SECURE Act and SECURE 2.0 Act rules:
    - Born before July 1, 1949: Age 70.5 (using 70 for simplicity)
    - Born July 1, 1949 - Dec 31, 1950: Age 72
    - Born Jan 1, 1951 - Dec 31, 1959: Age 73
    - Born Jan 1, 1960 or later: Age 75
    
    Args:
        birth_year: Year of birth
        
    Returns:
        Age when RMDs must begin
    """
    if birth_year < 1949:
        return 70  # Actually 70.5, but using 70 for simplicity
    elif birth_year <= 1950:
        return 72
    elif birth_year <= 1959:
        return 73
    else:  # 1960 or later
        return 75


def calculate_rmd_amount(account_balance: float, age: int, rmd_starting_age: int) -> float:
    """Calculate Required Minimum Distribution for an account.
    
    RMDs start at different ages depending on birth year (per SECURE Act/SECURE 2.0).
    Uses IRS Uniform Lifetime Table.
    
    Args:
        account_balance: Current account balance (before RMD)
        age: Account owner's current age
        rmd_starting_age: Age when RMDs must begin (varies by birth year)
        
    Returns:
        Required minimum distribution amount (0 if not applicable)
    """
    if age < rmd_starting_age:
        return 0.0
    
    divisor = RMD_LIFETIME_TABLE.get(age, 2.0)  # Default to 2.0 for ages beyond table
    return account_balance / divisor


def can_contribute(account_type: str, age: int, work_end_age: int, continue_post_retirement: bool = False) -> bool:
    """Check if an account type is eligible for contributions at a given age.
    
    Args:
        account_type: Type of account (401k, traditional_ira, roth_ira, taxable_brokerage)
        age: Current age
        work_end_age: Age when work income stops
        continue_post_retirement: If True, allows contributions after work_end_age for eligible accounts
    """
    rule = CONTRIBUTION_STOP_RULES.get(account_type)
    if rule is None:
        return True
    if rule == 'work_end_age':
        return age < work_end_age
    
    # For accounts with age-based rules (like Traditional IRA at 73),
    # check both the age rule and whether user wants to continue after retirement
    if isinstance(rule, int):
        # If user wants to continue post-retirement and still under age limit
        if continue_post_retirement:
            return age < rule
        # Otherwise, stop at work_end_age even if under the age limit
        return age < work_end_age and age < rule
    
    return age < rule


def run_comprehensive_projection(
    # Personal info
    current_age: int,
    target_age: int,

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
    ss_cola: float = 0.025,
    max_flex_reduction: float = 0.50,
    events: Optional[List[OneTimeEvent]] = None,
    inflation_rate: float = 0.03,
    max_age: int = 110
) -> pd.DataFrame:
    """
    Year-by-year retirement projection.

    Each year:
    1. Calculate income (work income grows at inflation, SS with COLA)
    2. Calculate inflated expenses and one-time events
    3. Determine planned contributions for eligible accounts
    4. Fund contributions from surplus, reducing flex spending if needed
    5. Withdraw from accounts in priority order if still in deficit
    6. Apply investment returns to remaining balances

    Returns:
        DataFrame with one row per year of the projection.
    """
    if events is None:
        events = []

    projection_years = max_age - current_age + 1
    results = []

    # Calculate birth year and determine RMD starting age
    current_year = 2026  # Base year for projections
    birth_year = current_year - current_age
    rmd_starting_age = get_rmd_starting_age(birth_year)

    # Sort accounts by priority for withdrawal ordering
    sorted_accounts = sorted(accounts, key=lambda a: a.priority)

    # Initialize account balances (modified each year)
    account_balances = {acc.name: acc.balance for acc in accounts}

    # Base-year expense totals (before inflation)
    core_expenses_base = sum(e.annual_amount for e in expense_categories
                             if e.category_type == 'CORE')
    flex_expenses_base = sum(e.annual_amount for e in expense_categories
                             if e.category_type == 'FLEX')

    for year_offset in range(projection_years):
        age = current_age + year_offset
        year = current_year + year_offset

        # --- INCOME ---

        # Work income grows at inflation rate, stops at work_end_age
        if age < work_end_age:
            work_income = current_work_income * ((1 + inflation_rate) ** year_offset)
        else:
            work_income = 0

        # Social Security starts at ss_start_age with annual COLA
        if age >= ss_start_age:
            years_on_ss = age - ss_start_age
            ss_income = ss_monthly_benefit * 12 * ((1 + ss_cola) ** years_on_ss)
        else:
            ss_income = 0

        total_income = work_income + ss_income

        # --- EXPENSES ---

        inflation_multiplier = (1 + inflation_rate) ** year_offset
        core_expenses = core_expenses_base * inflation_multiplier
        flex_expenses_full = flex_expenses_base * inflation_multiplier

        # --- PLANNED CONTRIBUTIONS ---
        # Figure out which accounts are eligible and what they want

        planned = {}
        for acc in accounts:
            if can_contribute(acc.account_type, age, work_end_age, acc.continue_post_retirement):
                planned[acc.name] = acc.planned_contribution
            else:
                planned[acc.name] = 0

        total_planned = sum(planned.values())

        # --- FUNDING CONTRIBUTIONS FROM SURPLUS ---
        # Surplus = income - core expenses - flex expenses
        # Contributions are prioritized over flex spending

        # How much money is available before touching flex spending?
        available_for_all = total_income - core_expenses
        # This must cover both flex expenses and contributions

        flex_expenses_actual = flex_expenses_full
        flex_multiplier = 1.0
        total_contributions = 0
        contributions = {}
        contribution_shortfall = 0

        if available_for_all >= flex_expenses_full + total_planned:
            # Enough income to cover everything: full flex + full contributions
            flex_expenses_actual = flex_expenses_full
            flex_multiplier = 1.0
            contributions = dict(planned)
            total_contributions = total_planned

        elif available_for_all >= total_planned:
            # Enough for contributions but not full flex spending.
            # Reduce flex to make room for contributions.
            money_for_flex = available_for_all - total_planned
            flex_expenses_actual = max(
                money_for_flex,
                flex_expenses_full * (1 - max_flex_reduction)
            )
            flex_multiplier = (flex_expenses_actual / flex_expenses_full
                               if flex_expenses_full > 0 else 1.0)

            if money_for_flex >= flex_expenses_full * (1 - max_flex_reduction):
                # Flex reduction was enough to fund all contributions
                contributions = dict(planned)
                total_contributions = total_planned
            else:
                # Even max flex reduction wasn't enough; fund what we can
                money_after_min_flex = (available_for_all
                                        - flex_expenses_full * (1 - max_flex_reduction))
                flex_expenses_actual = flex_expenses_full * (1 - max_flex_reduction)
                flex_multiplier = 1 - max_flex_reduction

                # Distribute available money proportionally across planned contributions
                if total_planned > 0:
                    for acc_name, amt in planned.items():
                        share = amt / total_planned
                        contributions[acc_name] = money_after_min_flex * share
                    total_contributions = money_after_min_flex
                    contribution_shortfall = total_planned - total_contributions
                else:
                    contributions = {name: 0 for name in planned}

        else:
            # Not even enough income to cover core expenses + contributions.
            # Reduce flex to minimum. Contribute what we can after that.
            flex_expenses_actual = flex_expenses_full * (1 - max_flex_reduction)
            flex_multiplier = 1 - max_flex_reduction if flex_expenses_full > 0 else 1.0

            money_after_min_flex = (available_for_all
                                    - flex_expenses_full * (1 - max_flex_reduction))

            if money_after_min_flex > 0 and total_planned > 0:
                # Some money left for partial contributions
                for acc_name, amt in planned.items():
                    share = amt / total_planned
                    contributions[acc_name] = money_after_min_flex * share
                total_contributions = money_after_min_flex
                contribution_shortfall = total_planned - total_contributions
            else:
                # No money for contributions at all
                contributions = {name: 0 for name in planned}
                contribution_shortfall = total_planned

        # --- FUND REMAINING CONTRIBUTIONS FROM PORTFOLIO ---
        # If income couldn't fully fund contributions (after reducing flex),
        # withdraw from accounts (by priority) to fund contributions to other accounts.
        # This enables strategic moves like: withdraw from taxable → contribute to Roth IRA
        
        contribution_withdrawals = {acc.name: 0 for acc in accounts}
        
        if contribution_shortfall > 0 and total_planned > 0:
            remaining_shortfall = contribution_shortfall
            
            # For each account that needs contributions (proportional to their shortfall)
            for acc_name, planned_amt in planned.items():
                if planned_amt == 0:
                    continue
                    
                # How much does this account still need?
                already_funded = contributions.get(acc_name, 0)
                this_account_shortfall = planned_amt - already_funded
                
                if this_account_shortfall <= 0:
                    continue
                
                # Withdraw from other accounts (by priority) to fund this contribution
                for source_acc in sorted_accounts:
                    if this_account_shortfall <= 0:
                        break
                    
                    # Don't withdraw from an account to contribute to itself (circular)
                    if source_acc.name == acc_name:
                        continue
                    
                    # How much can we withdraw from this source?
                    available_in_source = account_balances[source_acc.name]
                    withdrawal_amount = min(this_account_shortfall, available_in_source)
                    
                    if withdrawal_amount > 0:
                        # Record this as a contribution withdrawal (separate from deficit withdrawals)
                        contribution_withdrawals[source_acc.name] += withdrawal_amount
                        account_balances[source_acc.name] -= withdrawal_amount
                        
                        # Add to this account's contribution
                        contributions[acc_name] = contributions.get(acc_name, 0) + withdrawal_amount
                        total_contributions += withdrawal_amount
                        this_account_shortfall -= withdrawal_amount
                        remaining_shortfall -= withdrawal_amount
            
            # Update shortfall to reflect what couldn't be funded even from portfolio
            contribution_shortfall = remaining_shortfall

        # Apply contributions to account balances
        for acc_name, contrib in contributions.items():
            account_balances[acc_name] += contrib

        # --- REQUIRED MINIMUM DISTRIBUTIONS (RMDs) ---
        # RMDs are mandatory withdrawals from Traditional IRA and 401(k).
        # Starting age varies by birth year: 70/72/73/75 (SECURE Act/SECURE 2.0).
        # These withdrawals count as income for tax purposes but we add them to available cash.
        # RMDs happen BEFORE regular deficit withdrawals.
        
        rmds = {}
        total_rmds = 0
        
        for acc in accounts:
            if acc.account_type in RMD_ACCOUNT_TYPES:
                # Calculate RMD based on balance AFTER contributions
                rmd_amount = calculate_rmd_amount(account_balances[acc.name], age, rmd_starting_age)
                
                # Apply the RMD (reduce account balance)
                actual_rmd = min(rmd_amount, account_balances[acc.name])
                account_balances[acc.name] -= actual_rmd
                rmds[acc.name] = actual_rmd
                total_rmds += actual_rmd
            else:
                rmds[acc.name] = 0

        # --- TOTAL EXPENSES (for surplus/deficit calculation) ---

        total_expenses_actual = (core_expenses + flex_expenses_actual
                                 + total_contributions)
        
        # RMDs add to available cash (they're forced withdrawals that can cover expenses)
        surplus_deficit = total_income + total_rmds - total_expenses_actual

        # --- WITHDRAWALS (Deficit Coverage) ---

        withdrawals = {}
        total_withdrawals = 0

        if surplus_deficit < 0:
            deficit_to_cover = abs(surplus_deficit)

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

        # --- ONE-TIME EVENTS (Portfolio Transactions) ---
        # Apply events as direct additions/withdrawals to specific accounts
        # This happens AFTER normal income/expense/contribution flow

        event_amount = 0
        event_description = ""
        event_account = ""
        for event in events:
            if event.year == year:
                event_amount = event.amount
                event_description = event.description
                event_account = event.account_name
                # Apply the event to the specified account
                # Positive amount = withdrawal (reduces balance)
                # Negative amount = addition (increases balance)
                if event_account in account_balances:
                    account_balances[event_account] -= event_amount
                break

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
            'event_account': event_account,
            'total_expenses': total_expenses_actual,
            'surplus_deficit': surplus_deficit,
            'total_contributions': total_contributions,
            'contribution_shortfall': contribution_shortfall,
            'total_rmds': total_rmds,
            'total_withdrawals': total_withdrawals,
            'total_portfolio': total_portfolio,
            'portfolio_depleted': portfolio_depleted
        }

        # Add per-account detail columns
        for acc in accounts:
            year_data[f'{acc.name}_balance'] = account_balances[acc.name]
            year_data[f'{acc.name}_contribution'] = contributions.get(acc.name, 0)
            year_data[f'{acc.name}_withdrawal'] = withdrawals.get(acc.name, 0)
            year_data[f'{acc.name}_contribution_withdrawal'] = contribution_withdrawals.get(acc.name, 0)
            year_data[f'{acc.name}_rmd'] = rmds.get(acc.name, 0)
            year_data[f'{acc.name}_return'] = returns.get(acc.name, 0)

        results.append(year_data)

        if portfolio_depleted:
            break

    return pd.DataFrame(results)


def calculate_conservative_retirement_balance(
    accounts: List[AccountBucket],
    current_age: int,
    work_end_age: int
) -> float:
    """
    Calculate a conservative projection of retirement portfolio balance.
    
    This is a simplified calculation that:
    - Starts with current portfolio balances
    - Includes planned contributions (respecting account type rules)
    - Grows at fixed 5.5% real return (8% nominal - 2.5% inflation)
    - Does NOT account for living expenses (conservative assumption)
    
    This provides a benchmark separate from the user's detailed projection.
    
    Args:
        accounts: List of investment accounts with current balances and planned contributions
        current_age: User's current age
        work_end_age: Age when user plans to stop working
    
    Returns:
        Projected portfolio balance at retirement age
    """
    # Conservative assumptions
    REAL_RETURN = 0.055  # 5.5% real return (8% nominal - 2.5% inflation)
    
    # Initialize balances
    account_balances = {acc.name: acc.balance for acc in accounts}
    
    # Project year by year from current age to retirement
    for year_offset in range(work_end_age - current_age):
        age = current_age + year_offset
        
        # Add contributions for eligible accounts
        for acc in accounts:
            if can_contribute(acc.account_type, age, work_end_age, acc.continue_post_retirement):
                account_balances[acc.name] += acc.planned_contribution
        
        # Apply 5.5% real return to all accounts
        for acc in accounts:
            account_balances[acc.name] *= (1 + REAL_RETURN)
    
    # Return total portfolio value at retirement
    return sum(account_balances.values())


def analyze_retirement_plan(
    projection_df: pd.DataFrame,
    target_age: int = 90,
    work_end_age: int = None,
    accounts: Optional[List[AccountBucket]] = None,
    current_age: Optional[int] = None
) -> Dict:
    """
    Analyze a retirement projection and return key metrics.
    
    Args:
        projection_df: DataFrame from run_comprehensive_projection()
        target_age: Target age for retirement planning (default 90)
        work_end_age: Age when work income stops
        accounts: List of AccountBucket objects (optional, for conservative calculation)
        current_age: User's current age (optional, for conservative calculation)

    Returns dictionary with:
    - run_out_age: Age when money runs out (or None if never)
    - run_out_year: Year when money runs out
    - cushion_years: Years beyond target_age
    - status: 'ON TRACK' or 'AT RISK'
    - warnings: List of warning messages
    - final_balance: Portfolio value at end of projection
    - sustainable_withdrawal_annual: Conservative safe annual withdrawal (if accounts provided)
    - sustainable_withdrawal_monthly: Conservative safe monthly withdrawal (if accounts provided)
    
    Conservative Sustainable Withdrawal:
    If accounts and current_age are provided, calculates a separate conservative estimate
    that projects current balances forward at 5.5% real return (8% nominal - 2.5% inflation),
    includes planned contributions, assumes no living expenses withdrawn before retirement.
    Calculated to last from work_end_age to target_age (not fixed at age 110).
    This is independent from the main projection's assumptions.
    """
    if projection_df.empty:
        return {
            'run_out_age': None,
            'run_out_year': None,
            'cushion_years': 0,
            'status': 'AT RISK',
            'warnings': ['No projection data'],
            'final_balance': 0,
            'sustainable_withdrawal_annual': None,
            'sustainable_withdrawal_monthly': None
        }

    warnings = []

    # Find when portfolio depletes
    depleted = projection_df[projection_df['portfolio_depleted'] == True]

    if len(depleted) > 0:
        run_out_age = depleted.iloc[0]['age']
        run_out_year = depleted.iloc[0]['year']
    else:
        run_out_age = None
        run_out_year = None

    # Calculate cushion
    if run_out_age is None:
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
        warnings.append(
            f'Portfolio depletes at age {run_out_age}, '
            f'{target_age - run_out_age} years before target'
        )

    # Check for excessive flexible spending reduction
    # Only warn if flex spending is reduced AND portfolio shows signs of strain
    avg_flex_multiplier = projection_df['flex_multiplier'].mean()
    if avg_flex_multiplier < 0.8:
        # Get detailed info about flex spending reductions
        reduced_years = projection_df[projection_df['flex_multiplier'] < 1.0]
        if len(reduced_years) > 0:
            # Check if this is a real problem or just accounting from contribution prioritization
            # If portfolio is healthy and growing, flex reductions aren't concerning
            
            # Calculate portfolio health during reduction years
            avg_portfolio_during_reductions = reduced_years['total_portfolio'].mean()
            initial_portfolio = projection_df.iloc[0]['total_portfolio']
            portfolio_growth_factor = avg_portfolio_during_reductions / initial_portfolio if initial_portfolio > 0 else 0
            
            # Only warn if portfolio is actually struggling (shrinking or status is AT RISK)
            portfolio_is_struggling = (portfolio_growth_factor < 0.8 or status == 'AT RISK')
            
            if portfolio_is_struggling:
                min_multiplier = reduced_years['flex_multiplier'].min()
                first_reduction_age = int(reduced_years.iloc[0]['age'])
                last_reduction_age = int(reduced_years.iloc[-1]['age'])
                num_years_reduced = len(reduced_years)
                
                # Calculate average planned vs actual flex spending
                total_planned_flex = projection_df['flex_expenses_full'].sum()
                total_actual_flex = projection_df['flex_expenses_actual'].sum()
                lifetime_avg_multiplier = total_actual_flex / total_planned_flex if total_planned_flex > 0 else 1.0
                
                warnings.append(
                    f'Flexible (discretionary) spending frequently reduced below planned levels. '
                    f'Over your lifetime, you\'ll spend an average of {lifetime_avg_multiplier * 100:.0f}% '
                    f'of your planned flexible budget. Reductions occur in {num_years_reduced} years '
                    f'(ages {first_reduction_age}-{last_reduction_age}), with the worst year at '
                    f'{min_multiplier * 100:.0f}% of planned. This happens because income doesn\'t fully '
                    f'cover core expenses and contributions, requiring cuts to discretionary spending. '
                    f'Consider: reducing planned contributions, adjusting retirement age, or accepting '
                    f'lower discretionary spending in retirement.'
                )

    # Check for contribution shortfalls (only warn if it happens while still working)
    if 'contribution_shortfall' in projection_df.columns:
        # Filter to significant shortfalls only (> $100/year to avoid noise from rounding)
        shortfall_years = projection_df[
            projection_df['contribution_shortfall'] > 100
        ]
        if len(shortfall_years) > 0:
            first_shortfall_age = int(shortfall_years.iloc[0]['age'])
            first_shortfall_year = int(shortfall_years.iloc[0]['year'])
            total_shortfall = shortfall_years['contribution_shortfall'].sum()
            # Calculate average monthly shortfall across all affected years
            avg_annual_shortfall = total_shortfall / len(shortfall_years)
            monthly_shortfall = avg_annual_shortfall / 12
            
            # Check if still working when shortfall starts
            still_working = shortfall_years.iloc[0]['work_income'] > 0
            
            if still_working:
                # Shortfall while still working - this is a real issue
                warnings.append(
                    f'Income insufficient to fund planned account contributions '
                    f'starting in {first_shortfall_year} (age {first_shortfall_age}). '
                    f'Average monthly shortfall: ${monthly_shortfall:,.0f}/month '
                    f'(${total_shortfall:,.0f} total over {len(shortfall_years)} years). '
                    f'Consider increasing income or reducing planned contributions.'
                )
            # Note: Post-retirement contribution shortfalls are not warned about.
            # In retirement, the focus should be on sustainable withdrawals, not contributions.

    # Check for early withdrawals (only warn if significant, > $1000/year threshold)
    working_years = projection_df[projection_df['work_income'] > 0]
    if len(working_years) > 0:
        total_working_withdrawals = working_years['total_withdrawals'].sum()
        # Only warn if withdrawals are significant (avoid noise from rounding/timing)
        if total_working_withdrawals > 1000:
            warnings.append(
                f'Withdrawing ${total_working_withdrawals:,.0f} from portfolio '
                f'over {len(working_years)} working years. Consider increasing income '
                f'or reducing expenses/contributions.'
            )

    # Calculate conservative sustainable withdrawal rate for retirement
    sustainable_withdrawal_annual = None
    sustainable_withdrawal_monthly = None
    
    if work_end_age is not None and accounts is not None and current_age is not None:
        # Use conservative calculation: 5.5% real return (8% nominal - 2.5% inflation)
        # This projects current portfolio forward with contributions but no expense withdrawals
        balance_at_retirement = calculate_conservative_retirement_balance(
            accounts=accounts,
            current_age=current_age,
            work_end_age=work_end_age
        )
        
        years_in_retirement = target_age - work_end_age
        CONSERVATIVE_REAL_RETURN = 0.055  # 5.5% real (8% nominal - 2.5% inflation)
        
        if years_in_retirement > 0 and balance_at_retirement > 0:
            # Annuity payment formula: PV * (r * (1+r)^n) / ((1+r)^n - 1)
            sustainable_withdrawal_annual = balance_at_retirement * (
                CONSERVATIVE_REAL_RETURN * (1 + CONSERVATIVE_REAL_RETURN) ** years_in_retirement
            ) / ((1 + CONSERVATIVE_REAL_RETURN) ** years_in_retirement - 1)
            
            sustainable_withdrawal_monthly = sustainable_withdrawal_annual / 12

    return {
        'run_out_age': run_out_age,
        'run_out_year': run_out_year,
        'cushion_years': cushion_years,
        'status': status,
        'warnings': warnings,
        'final_balance': (projection_df.iloc[-1]['total_portfolio']
                          if not projection_df.empty else 0),
        'sustainable_withdrawal_annual': sustainable_withdrawal_annual,
        'sustainable_withdrawal_monthly': sustainable_withdrawal_monthly
    }
