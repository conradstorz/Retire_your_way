# 💰 Retirement Planning Application

A transparent, easy-to-understand retirement planning tool built with Python and Streamlit. This application replaces complex spreadsheet formulas with clear, documented code that anyone can read, verify, and maintain.

## Why This Instead of a Spreadsheet?

**Transparency:** All calculations are written in well-documented Python functions. No hidden formulas, no cell reference errors.

**Maintainability:** Code is organized in logical modules. Updates are easy and don't break references.

**Sharing:** Deploy to the web with a simple URL. No need to email Excel files back and forth.

**Complexity:** Handle sophisticated scenarios (multiple accounts, tax planning, Monte Carlo simulations) without spreadsheet limitations.

**Version Control:** Track changes over time with Git instead of "Budget_v2_final_FINAL.xlsx"

## Features

- **Interactive Planning:** Adjust your age, savings, contributions, and see results update in real-time
- **Visual Projections:** Clear charts showing your money growth and retirement spending
- **Scenario Analysis:** Test different contribution levels and retirement ages
- **Transparent Calculations:** Every formula is documented and easy to understand
- **Data Export:** Download your full projection as CSV for further analysis

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone or download this repository**

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

### Running the App

**Option 1: Run locally**

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

**Option 2: Deploy to Streamlit Cloud (Free)**

1. Push this code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy the app
5. Share the URL with family/friends - they can use it without installing anything!

## Project Structure

```
Retirement_planning/
├── app.py                  # Main Streamlit application
├── calculations.py         # All financial calculation functions
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── .gitignore            # Files to exclude from version control
```

## How to Use

1. **Enter Your Information** (left sidebar):
   - Current age and retirement age
   - Current savings and planned contributions
   - Desired retirement spending

2. **Adjust Assumptions**:
   - Expected investment returns (before and during retirement)
   - Inflation rate
   - Life expectancy

3. **Review Results**:
   - See if you're on track
   - View detailed projections for each year
   - Test what-if scenarios

4. **Export Data**:
   - Download the year-by-year projection as CSV
   - Share with financial advisors or family

## Customization

### Adding Your Specification

When you're ready to implement your specific requirements:

1. Add new calculation functions to `calculations.py`
2. Add corresponding UI elements to `app.py`
3. Test with different scenarios

### Example: Adding Social Security

```python
# In calculations.py
def calculate_social_security(
    full_retirement_age: int,
    claiming_age: int,
    estimated_benefit: float
) -> float:
    """
    Calculate adjusted Social Security benefit based on claiming age.
    
    Claiming early (62) reduces benefit by ~30%
    Claiming late (70) increases benefit by ~24%
    """
    # Implementation here
    pass
```

### Example: Adding Tax Calculations

```python
# In calculations.py
def calculate_retirement_taxes(
    traditional_401k_withdrawal: float,
    roth_withdrawal: float,
    social_security: float,
    filing_status: str = 'single'
) -> float:
    """Calculate estimated federal taxes on retirement income."""
    # Implementation here
    pass
```

## Understanding the Calculations

All calculation functions are in `calculations.py` with detailed documentation:

- `calculate_future_value()`: Projects investment growth with contributions
- `project_retirement_balance()`: Shows how your money depletes during retirement
- `calculate_retirement_readiness()`: Comprehensive analysis of your plan
- `calculate_safe_withdrawal_rate()`: Determines sustainable spending level

Each function includes:
- Clear parameter descriptions
- Return value explanation
- Usage examples
- The actual formula/logic used

## Next Steps

### Immediate Improvements You Could Add:

1. **Multiple Accounts:** Track 401(k), IRA, Roth IRA, taxable accounts separately
2. **Tax Planning:** Model tax implications of different withdrawal strategies
3. **Social Security:** Integrate SS benefits and optimal claiming age
4. **Healthcare Costs:** Add Medicare and health insurance estimates
5. **Pension Income:** Include defined benefit pensions
6. **Monte Carlo:** Run probabilistic simulations instead of single scenario

### Sharing with Others:

- **Family:** Deploy to Streamlit Cloud and share the URL
- **Financial Advisor:** Export CSV data or show them the code
- **Friends:** They can fork your GitHub repo and customize for themselves

## Contributing

This is your personal project, but if you want to:
- Track improvements: Use GitHub Issues
- Version changes: Commit to Git regularly
- Get feedback: Share with the Streamlit community

## License

This is your personal tool - use and modify however you like!

## Support

- **Streamlit Documentation:** https://docs.streamlit.io
- **Python Financial Calculations:** Check NumPy Financial (numpy-financial)
- **Retirement Planning:** Consult with a licensed financial advisor for personalized advice

---

**Remember:** This tool is for educational and planning purposes. Always consult with qualified financial professionals for important financial decisions.
