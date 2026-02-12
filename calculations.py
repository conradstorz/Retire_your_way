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


def can_contribute(account_type: str, age: int, work_end_age: int) -> bool:
    """Check if an account type is eligible for contributions at a given age."""
    rule = CONTRIBUTION_STOP_RULES.get(account_type)
    if rule is None:
        return True
    if rule == 'work_end_age':
        return age < work_end_age
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
        year = 2026 + year_offset

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

        # --- ONE-TIME EVENTS ---

        event_amount = 0
        event_description = ""
        for event in events:
            if event.year == year:
                event_amount = event.amount
                event_description = event.description
                break

        # --- PLANNED CONTRIBUTIONS ---
        # Figure out which accounts are eligible and what they want

        planned = {}
        for acc in accounts:
            if can_contribute(acc.account_type, age, work_end_age):
                planned[acc.name] = acc.planned_contribution
            else:
                planned[acc.name] = 0

        total_planned = sum(planned.values())

        # --- FUNDING CONTRIBUTIONS FROM SURPLUS ---
        # Surplus = income - core expenses - flex expenses - events
        # Contributions are prioritized over flex spending

        # How much money is available before touching flex spending?
        available_for_all = total_income - core_expenses - event_amount
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
            # Not even enough income to cover core expenses + events + contributions.
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

        # Apply contributions to account balances
        for acc_name, contrib in contributions.items():
            account_balances[acc_name] += contrib

        # --- TOTAL EXPENSES (for surplus/deficit calculation) ---

        total_expenses_actual = (core_expenses + flex_expenses_actual
                                 + event_amount + total_contributions)
        surplus_deficit = total_income - total_expenses_actual

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
            'surplus_deficit': surplus_deficit,
            'total_contributions': total_contributions,
            'contribution_shortfall': contribution_shortfall,
            'total_withdrawals': total_withdrawals,
            'total_portfolio': total_portfolio,
            'portfolio_depleted': portfolio_depleted
        }

        # Add per-account detail columns
        for acc in accounts:
            year_data[f'{acc.name}_balance'] = account_balances[acc.name]
            year_data[f'{acc.name}_contribution'] = contributions.get(acc.name, 0)
            year_data[f'{acc.name}_withdrawal'] = withdrawals.get(acc.name, 0)
            year_data[f'{acc.name}_return'] = returns.get(acc.name, 0)

        results.append(year_data)

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
    - final_balance: Portfolio value at end of projection
    """
    if projection_df.empty:
        return {
            'run_out_age': None,
            'run_out_year': None,
            'cushion_years': 0,
            'status': 'AT RISK',
            'warnings': ['No projection data'],
            'final_balance': 0
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
    avg_flex_multiplier = projection_df['flex_multiplier'].mean()
    if avg_flex_multiplier < 0.8:
        warnings.append(
            f'Average flexible spending reduced to '
            f'{avg_flex_multiplier * 100:.0f}% of planned'
        )

    # Check for contribution shortfalls
    if 'contribution_shortfall' in projection_df.columns:
        shortfall_years = projection_df[
            projection_df['contribution_shortfall'] > 0
        ]
        if len(shortfall_years) > 0:
            first_shortfall_age = int(shortfall_years.iloc[0]['age'])
            warnings.append(
                f'Planned contributions cannot be fully funded starting at '
                f'age {first_shortfall_age} -- discretionary spending '
                f'already at minimum'
            )

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
        'final_balance': (projection_df.iloc[-1]['total_portfolio']
                          if not projection_df.empty else 0)
    }
