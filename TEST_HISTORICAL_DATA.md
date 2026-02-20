# Historical Data Feature - Test Coverage

## Overview
Comprehensive test suite for the historical years feature that integrates account snapshot data into retirement projections.

## Test Files
- **test_calculations.py** - All tests added to existing test file

## Test Classes (13 tests total)

### 1. TestGenerateHistoricalRows (4 tests)
Tests the `generate_historical_rows()` function that converts snapshot summaries into projection-compatible rows.

- ✅ `test_single_historical_year` - Single year conversion
- ✅ `test_multiple_historical_years` - Multiple years with chronological ordering
- ✅ `test_empty_historical_data` - Handles empty input gracefully
- ✅ `test_row_structure_matches_projection` - Validates all required fields exist

### 2. TestUserDataHistoricalSummaries (6 tests)
Tests the `UserDataManager.get_historical_year_summaries()` function that aggregates snapshots by calendar year.

- ✅ `test_no_snapshots_returns_empty_list` - No data case
- ✅ `test_single_year_single_account` - Basic aggregation with ROI calculation
- ✅ `test_multiple_accounts_same_year` - Cross-account aggregation
- ✅ `test_multiple_years_progression` - Year-to-year carry-forward logic
- ✅ `test_multiple_snapshots_per_year_aggregation` - Multiple snapshots within same year
- ✅ `test_roi_calculation_with_zero_starting_balance` - Edge case handling

### 3. TestProjectionWithHistoricalData (3 tests)
Integration tests for the complete feature in the projection engine.

- ✅ `test_projection_with_historical_data` - Historical rows prepended correctly
- ✅ `test_investment_roi_column_exists` - New ROI column added with actual + projected values
- ✅ `test_projection_without_historical_data` - Backward compatibility when no snapshots exist

## Running Tests

### Run all new tests:
```bash
python -m pytest test_calculations.py::TestGenerateHistoricalRows test_calculations.py::TestUserDataHistoricalSummaries test_calculations.py::TestProjectionWithHistoricalData -v
```

### Run specific test class:
```bash
python -m pytest test_calculations.py::TestUserDataHistoricalSummaries -v
```

### Run full test suite:
```bash
python -m pytest test_calculations.py -v
```

## Test Coverage Summary

### Functionality Tested:
- ✅ Snapshot data aggregation by calendar year
- ✅ Multiple accounts aggregation
- ✅ Multi-year progression with carry-forward balances
- ✅ ROI calculation (actual growth / starting balance)
- ✅ Historical row generation with correct age and year
- ✅ Integration with projection engine
- ✅ Investment ROI column (historical actual + projected weighted average)
- ✅ Empty data / edge case handling
- ✅ Backward compatibility

### Key Validations:
- Growth calculation: `ending_value - starting_value - contributions`
- ROI calculation: `growth / starting_balance`
- Year-to-year linkage: Each year's ending becomes next year's starting
- Row structure compatibility between historical and projected data
- Proper handling of NaN values in income/expense columns

## Implementation Files Tested:
- `user_data.py` - `get_historical_year_summaries()` method
- `calculations.py` - `generate_historical_rows()` and `run_comprehensive_projection()` functions
- `app.py` - Integration (tested indirectly through calculations)

## Test Results:
✅ All 13 tests passing
✅ No regressions in existing tests
✅ Full feature coverage achieved
