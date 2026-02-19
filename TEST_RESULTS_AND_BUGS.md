# Test Results and Bugs Found in Projection Logic

**Date**: February 19, 2026  
**Test Suite**: test_calculations.py  
**Tests Run**: 48  
**Tests Passed**: 45  
**Tests Failed**: 3  

## Summary

Comprehensive testing of the retirement projection logic using both specific scenario tests and property-based testing (hypothesis) has identified **3 confirmed bugs** that cause incorrect financial projections.

---

## Bug #1: Post-Retirement Contributions Not Funded

**Severity**: HIGH  
**Test**: `test_roth_ira_continue_post_retirement`  
**File**: [calculations.py](calculations.py)

### Description
When an account is configured with `continue_post_retirement=True` (e.g., Roth IRA), the account should accept contributions after work income stops, provided there's sufficient income from other sources (like Social Security). However, contributions are not being made even when there's a clear surplus.

### Expected Behavior
```python
# Scenario: Age 66 (retired), SS income $36k/year, expenses $30k/year
# Roth IRA with continue_post_retirement=True, planned contribution $7k/year
# Available surplus: $36k - $30k = $6k/year
# Expected: Contribution should be $6k (limited by available funds)
```

### Actual Behavior
```python
result.iloc[2]['Roth_contribution']  # Age 66 (post-retirement)
# Output: 0.0
# Contribution is $0 even with $6k surplus available
```

### Test Case
```python
result = run_comprehensive_projection(
    current_age=64,
    target_age=70,
    current_work_income=100000,
    work_end_age=66,
    ss_start_age=67,
    ss_monthly_benefit=3000,  # $36k/year
    accounts=[AccountBucket("Roth", 300000, 0.07, 1, "roth_ira", 7000, True)],
    expense_categories=[ExpenseCategory("Living", 30000, "CORE")],
)

# Age 64-65: Contributions working correctly ($7k/year)
# Age 66+: Contributions are $0 (BUG - should be funded from SS income surplus)
```

### Impact
- Users planning to continue Roth IRA contributions in retirement will see incorrect projections
- Portfolio balances will be underestimated
- Tax-advantaged savings opportunities will be missed in projections

### Root Cause
Likely in the contribution funding logic around lines 270-340 of [calculations.py](calculations.py). The logic may be checking for work income instead of total income when determining contribution eligibility post-retirement.

---

## Bug #2: One-Time Event Timing Error

**Severity**: MEDIUM  
**Test**: `test_one_time_withdrawal_reduces_account_balance`  
**File**: [calculations.py](calculations.py)

### Description
When a one-time event (withdrawal or addition) occurs in a specific year, the account balance calculation is off by approximately $2,100. This suggests the event is being applied at the wrong point in the year-by-year calculation sequence.

### Expected Behavior
```python
# Scenario: One-time $30k car purchase from $200k Taxable account
# Starting balance: $200,000
# Event: -$30,000 withdrawal
# Remaining: $170,000
# Returns (7%): $170,000 * 0.07 = $11,900
# Ending balance: $170,000 + $11,900 = $181,900
```

### Actual Behavior
```python
result.iloc[0]['Taxable_balance']
# Output: 184,000
# Off by $2,100 (exactly $30,000 * 0.07)
```

### Analysis
The error of $2,100 = $30,000 × 0.07 suggests that:
1. Returns are being calculated on the balance BEFORE the event is applied
2. Or the event is being applied AFTER returns instead of BEFORE returns

### Test Case
```python
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

# Expected balance after event + returns: ~$181,900
# Actual balance: $184,000
```

### Impact
- One-time event projections (inheritances, home sales, major purchases) will be incorrect
- Error accumulates in subsequent years
- Balance discrepancy = event_amount × return_rate

### Root Cause
Order of operations issue in [calculations.py](calculations.py) lines 450-470. Events are likely being applied AFTER investment returns instead of BEFORE.

Current (incorrect) order appears to be:
1. Calculate returns on starting balance → $200k × 0.07 = $14k
2. Apply event → Balance becomes $200k + $14k - $30k = $184k

Correct order should be:
1. Apply event → Balance becomes $170k
2. Calculate returns on remaining balance → $170k × 0.07 = $11.9k
3. Final balance → $181.9k

---

## Bug #3: Account Depletion with Contribution Surplus

**Severity**: HIGH  
**Test**: `test_zero_initial_balance`  
**File**: [calculations.py](calculations.py)

### Description
When an account starts with $0 balance but has planned contributions and surplus income to fund them, the account should grow over time. Instead, the account remains at $0 or depletes, suggesting contributions are not being properly applied.

### Expected Behavior
```python
# Scenario: Start with $0, contribute $5k/year with $20k/year surplus
# Year 0: $0 + $5k contribution + $350 returns (7%) = $5,350
# Year 1: $5,350 + $5k contribution + $724.50 returns = $11,074.50
# Year 5: Should have $25k+ from contributions alone
```

### Actual Behavior
```python
result.iloc[-1]['Empty_balance']  # After 5 years
# Output: 0.0
# Account has $0 instead of expected $25k+
```

### Test Case
```python
result = run_comprehensive_projection(
    current_age=30,
    target_age=35,
    current_work_income=60000,  # Plenty of income
    work_end_age=65,
    ss_start_age=67,
    ss_monthly_benefit=2000,
    accounts=[AccountBucket("Empty", 0, 0.07, 1, "taxable_brokerage", 5000)],
    expense_categories=[ExpenseCategory("Living", 40000, "CORE")],
)

# Income: $60k, Expenses: $40k, Surplus: $20k
# Planned contribution: $5k/year
# Expected: Account grows to $25k+ over 5 years
# Actual: Account remains at $0
```

### Impact
- Users starting new accounts or with low balances will see incorrect projections
- Long-term portfolio growth will be severely underestimated
- This is particularly problematic for younger users beginning their retirement savings journey

### Root Cause
Likely related to the contribution funding logic and/or application of contributions to accounts. Possible issues:
1. Contributions are calculated but not actually added to account balances
2. Withdrawals are incorrectly happening from the account despite surplus
3. Contribution logic has a bug when balance is $0 or very low

Investigate [calculations.py](calculations.py) lines 270-380 (contribution calculation and application).

---

## Test Coverage Statistics

### By Component
| Component | Tests | Passed | Failed |
|-----------|-------|--------|--------|
| Work Income | 2 | 2 | 0 |
| Social Security | 2 | 2 | 0 |
| Expense Inflation | 4 | 4 | 0 |
| Account Contributions | 6 | 5 | 1 |
| Withdrawal Ordering | 2 | 2 | 0 |
| Investment Returns | 3 | 3 | 0 |
| RMDs | 6 | 6 | 0 |
| One-Time Events | 2 | 1 | 1 |
| Complete Scenarios | 4 | 4 | 0 |
| Property-Based (hypothesis) | 8 | 8 | 0 |
| Edge Cases | 5 | 4 | 1 |
| Helper Functions | 4 | 4 | 0 |

### Property-Based Testing
Hypothesis successfully tested 100 random scenarios each for 8 different invariants, validating:
- Portfolio balances never go negative ✓
- Income exceeding expenses means no withdrawals ✓
- Expenses grow monotonically with inflation ✓
- Work income grows with inflation while working ✓
- Zero net transactions means compound growth ✓
- Social Security grows with COLA ✓
- Work income stops after work_end_age ✓
- FLEX multiplier respects max_reduction limits ✓

---

## Recommendations

### Priority 1 (Critical - Fix Immediately)
1. **Bug #1**: Fix post-retirement contribution funding logic
2. **Bug #3**: Fix contribution application for zero/low balance accounts

### Priority 2 (Important - Fix Soon)
3. **Bug #2**: Correct one-time event timing in calculation sequence

### Additional Testing
- Add more edge case tests for:
  - Accounts with very low balances (<$100)
  - Multiple simultaneous contributions post-retirement
  - Multiple one-time events in the same year
  - One-time events combined with RMDs

---

## Files Affected
- [calculations.py](calculations.py) - Core projection logic
- [test_calculations.py](test_calculations.py) - Test suite (48 comprehensive tests)
- [requirements.txt](requirements.txt) - Added pytest and hypothesis dependencies

## How to Run Tests
```bash
pip install -r requirements.txt
python -m pytest test_calculations.py -v
```

For detailed failure information:
```bash
python -m pytest test_calculations.py -v --tb=short
```

For running only failed tests:
```bash
python -m pytest test_calculations.py -v --lf
```
