"""
Retirement Planning Application - V2 (Multi-User)

A transparent retirement planning tool implementing comprehensive financial modeling
with multiple account buckets, expense categories, and Social Security integration.

Features multi-user authentication with individual data persistence.
"""

__version__ = "0.9.0"

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit_authenticator as stauth
from datetime import datetime, date
from calculations import (
    AccountBucket,
    ExpenseCategory,
    OneTimeEvent,
    ACCOUNT_TYPE_LABELS,
    run_comprehensive_projection,
    analyze_retirement_plan
)
from auth_config import (
    load_credentials, 
    register_new_user, 
    init_credentials_file,
    generate_recovery_code,
    add_recovery_code,
    add_security_question,
    get_security_question,
    reset_password_with_recovery,
    reset_password_with_security_question
)
from user_data import UserDataManager

# Page configuration
st.set_page_config(
    page_title="Retirement Planner V2",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize expander states (must be before authentication flow)
if 'expander_recovery_false' not in st.session_state:
    st.session_state.expander_recovery_false = False
if 'expander_registration_false' not in st.session_state:
    st.session_state.expander_registration_false = False
if 'expander_recovery_none' not in st.session_state:
    st.session_state.expander_recovery_none = False
if 'expander_registration_none' not in st.session_state:
    st.session_state.expander_registration_none = False
if 'expander_accounts' not in st.session_state:
    st.session_state.expander_accounts = {}
if 'expander_expenses' not in st.session_state:
    st.session_state.expander_expenses = {}
if 'expander_events' not in st.session_state:
    st.session_state.expander_events = {}

# Initialize credentials file
init_credentials_file()

# Load authentication configuration
config = load_credentials()

# Create authenticator object
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Display number of registered accounts on login page
num_accounts = len(config['credentials']['usernames'])
st.info(f"ℹ️ {num_accounts} registered account{'s' if num_accounts != 1 else ''}")

# Authentication
try:
    authenticator.login(location='main')
except Exception as e:
    st.error(f"Authentication error: {e}")
    st.stop()

# Get authentication status from session state
if st.session_state.get("authentication_status"):
    username = st.session_state["username"]
    name = st.session_state["name"]
    authentication_status = st.session_state["authentication_status"]
else:
    username = None
    name = None
    authentication_status = st.session_state.get("authentication_status", None)

if authentication_status == False:
    st.error('Username/password is incorrect')
    
    # Password Recovery section
    with st.expander("🔑 Forgot Password? Recover Account", expanded=False):
        st.markdown("Reset your password using your recovery code or security question.")
        
        recovery_method = st.radio(
            "Recovery Method:",
            ["Recovery Code", "Security Question"],
            horizontal=True
        )
        
        with st.form("password_recovery_form"):
            recover_username = st.text_input("Username")
            
            if recovery_method == "Recovery Code":
                recovery_code_input = st.text_input("Recovery Code", help="Enter the 16-character code you saved during registration")
                security_answer = None
            else:
                if recover_username:
                    security_q = get_security_question(recover_username)
                    if security_q:
                        st.info(f"**Your Security Question:** {security_q}")
                        security_answer = st.text_input("Answer")
                    else:
                        st.warning("No security question set for this account. Use recovery code instead.")
                        security_answer = None
                else:
                    security_answer = None
                recovery_code_input = None
            
            new_pass = st.text_input("New Password", type="password")
            new_pass_confirm = st.text_input("Confirm New Password", type="password")
            
            recover_button = st.form_submit_button("Reset Password")
            
            if recover_button:
                if not recover_username:
                    st.error("Please enter your username")
                elif new_pass != new_pass_confirm:
                    st.error("Passwords do not match")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if recovery_method == "Recovery Code" and recovery_code_input:
                        if reset_password_with_recovery(recover_username, recovery_code_input, new_pass):
                            st.success("✅ Password reset successful! Please login with your new password.")
                            st.balloons()
                        else:
                            st.error("Invalid username or recovery code")
                    elif recovery_method == "Security Question" and security_answer:
                        if reset_password_with_security_question(recover_username, security_answer, new_pass):
                            st.success("✅ Password reset successful! Please login with your new password.")
                            st.balloons()
                        else:
                            st.error("Invalid username or security answer")
                    else:
                        st.error("Please provide the required recovery information")
    
    # Registration section
    with st.expander("📝 New User Registration", expanded=False):
        st.markdown("Create a new account to start planning your retirement.")
        
        with st.form("registration_form"):
            new_username = st.text_input("Username")
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_password_confirm = st.text_input("Confirm Password", type="password")
            
            st.divider()
            st.markdown("**🔐 Account Recovery Setup** (Optional but recommended)")
            
            # Security question
            security_questions = [
                "What was the name of your first pet?",
                "What city were you born in?",
                "What is your mother's maiden name?",
                "What was the name of your first school?",
                "What is your favorite book?",
                "What was your childhood nickname?"
            ]
            security_question = st.selectbox("Security Question (optional)", [""] + security_questions)
            security_answer = st.text_input("Answer (optional)", help="Answer is case-insensitive") if security_question else ""
            
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                if not all([new_username, new_name, new_email, new_password]):
                    st.error("All fields are required")
                elif new_password != new_password_confirm:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if register_new_user(new_username, new_name, new_password, new_email):
                        # Generate and display recovery code
                        recovery_code = generate_recovery_code()
                        add_recovery_code(new_username, recovery_code)
                        
                        # Add security question if provided
                        if security_question and security_answer:
                            add_security_question(new_username, security_question, security_answer)
                        
                        st.success("✅ Registration successful!")
                        st.info(f"""
                        **🔑 Your Recovery Code:** `{recovery_code}`
                        
                        **⚠️ IMPORTANT:** Save this code in a secure place!
                        You can use it to reset your password if you forget it.
                        This code will not be shown again.
                        """)
                        
                        if security_question:
                            st.success("✅ Security question set successfully!")
                        
                        st.markdown("**You can now login with your credentials. Please close this expander to proceed.**")
                    else:
                        st.error("Username already exists")
    
    st.stop()

elif authentication_status == None:
    st.warning('Please enter your username and password')
    
    # Password Recovery section
    with st.expander("🔑 Forgot Password? Recover Account", expanded=False):
        st.markdown("Reset your password using your recovery code or security question.")
        
        recovery_method = st.radio(
            "Recovery Method:",
            ["Recovery Code", "Security Question"],
            horizontal=True,
            key="recovery_method_none"
        )
        
        with st.form("password_recovery_form_none"):
            recover_username = st.text_input("Username")
            
            if recovery_method == "Recovery Code":
                recovery_code_input = st.text_input("Recovery Code", help="Enter the 16-character code you saved during registration")
                security_answer = None
            else:
                if recover_username:
                    security_q = get_security_question(recover_username)
                    if security_q:
                        st.info(f"**Your Security Question:** {security_q}")
                        security_answer = st.text_input("Answer")
                    else:
                        st.warning("No security question set for this account. Use recovery code instead.")
                        security_answer = None
                else:
                    security_answer = None
                recovery_code_input = None
            
            new_pass = st.text_input("New Password", type="password")
            new_pass_confirm = st.text_input("Confirm New Password", type="password")
            
            recover_button = st.form_submit_button("Reset Password")
            
            if recover_button:
                if not recover_username:
                    st.error("Please enter your username")
                elif new_pass != new_pass_confirm:
                    st.error("Passwords do not match")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if recovery_method == "Recovery Code" and recovery_code_input:
                        if reset_password_with_recovery(recover_username, recovery_code_input, new_pass):
                            st.success("✅ Password reset successful! Please login with your new password.")
                            st.balloons()
                        else:
                            st.error("Invalid username or recovery code")
                    elif recovery_method == "Security Question" and security_answer:
                        if reset_password_with_security_question(recover_username, security_answer, new_pass):
                            st.success("✅ Password reset successful! Please login with your new password.")
                            st.balloons()
                        else:
                            st.error("Invalid username or security answer")
                    else:
                        st.error("Please provide the required recovery information")
    
    # Registration section
    with st.expander("📝 New User Registration", expanded=False):
        st.markdown("Create a new account to start planning your retirement.")
        
        with st.form("registration_form_none"):
            new_username = st.text_input("Username")
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            new_password_confirm = st.text_input("Confirm Password", type="password")
            
            st.divider()
            st.markdown("**🔐 Account Recovery Setup** (Optional but recommended)")
            
            # Security question
            security_questions = [
                "What was the name of your first pet?",
                "What city were you born in?",
                "What is your mother's maiden name?",
                "What was the name of your first school?",
                "What is your favorite book?",
                "What was your childhood nickname?"
            ]
            security_question = st.selectbox("Security Question (optional)", [""] + security_questions)
            security_answer = st.text_input("Answer (optional)", help="Answer is case-insensitive") if security_question else ""
            
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                if not all([new_username, new_name, new_email, new_password]):
                    st.error("All fields are required")
                elif new_password != new_password_confirm:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    if register_new_user(new_username, new_name, new_password, new_email):
                        # Generate and display recovery code
                        recovery_code = generate_recovery_code()
                        add_recovery_code(new_username, recovery_code)
                        
                        # Add security question if provided
                        if security_question and security_answer:
                            add_security_question(new_username, security_question, security_answer)
                        
                        st.success("✅ Registration successful!")
                        st.info(f"""
                        **🔑 Your Recovery Code:** `{recovery_code}`
                        
                        **⚠️ IMPORTANT:** Save this code in a secure place!
                        You can use it to reset your password if you forget it.
                        This code will not be shown again.
                        """)
                        
                        if security_question:
                            st.success("✅ Security question set successfully!")
                        
                        st.markdown("**You can now login with your credentials. Please close this expander to proceed.**")
                    else:
                        st.error("Username already exists")
    
    st.stop()

# ===== USER IS AUTHENTICATED =====

# Initialize user data manager
db_manager = UserDataManager()

# Load user-specific data or create defaults
if not db_manager.user_exists(username):
    db_manager.create_default_data_for_user(username)

# Load user's saved data
user_profile = db_manager.load_user_profile(username)
user_accounts = db_manager.load_user_accounts(username)
user_expenses = db_manager.load_user_expenses(username)
user_events = db_manager.load_user_events(username)

# Initialize session state for dynamic lists if not already set
if 'expense_categories' not in st.session_state:
    st.session_state.expense_categories = user_expenses

if 'accounts' not in st.session_state:
    st.session_state.accounts = user_accounts

if 'events' not in st.session_state:
    st.session_state.events = user_events

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = True

# Title with user greeting and logout button on same row
title_col, logout_col = st.columns([4, 1])
with title_col:
    st.title(f"💰 Retirement Planning Calculator v{__version__}")
with logout_col:
    st.write("")  # Vertical spacing to align with title
    authenticator.logout(location='main')

st.markdown(f"**Welcome back, {name}!** | *Logged in as: {username}*")
st.markdown("""
**Transparent, Long-Term Financial Simulation**

This is a work-in-progress. Please ignore the icon buttons at the top right of the page. They are links to my developement code repository.
I appologise for changes to the apperance from day to day.
Please reach out with feedback!
""")

# ===== DASHBOARD PLACEHOLDER =====
# Reserve space at the top for the dashboard. It gets filled in AFTER the
# configuration tabs so the projection uses current widget values.

dashboard_container = st.container()

# ===== CONFIGURATION & PROJECTIONS =====

st.header("⚙️ Configuration")

# Make configuration tab labels larger for readability
st.markdown("""
<style>
    button[data-baseweb="tab"] {
        font-size: 1.5rem !important;
        padding: 0.75rem 1.5rem !important;
    }
    button[data-baseweb="tab"] p {
        font-size: 1.5rem !important;
    }
    div[data-baseweb="tab-list"] button {
        font-size: 1.5rem !important;
        padding: 0.75rem 1.5rem !important;
    }
    div[data-baseweb="tab-list"] button p {
        font-size: 1.5rem !important;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 1.5rem !important;
        padding: 0.75rem 1.5rem !important;
    }
    .stTabs [data-baseweb="tab-list"] button p {
        font-size: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

config_tabs = st.tabs(["📋 Profile", "💰 Accounts", "🏠 Expenses", "📅 One-Time Events", "✅ Sanity Checks", "📈 Projections"])

# --- PROFILE TAB ---
with config_tabs[0]:
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("Personal Profile")
    with header_col2:
        st.write("")
        save_profile_clicked = st.button("💾 Save All Configuration", type="primary", key="save_all_config_header")

    prof_col1, prof_col2 = st.columns(2)

    with prof_col1:
        st.markdown("**Age & Retirement**")
        current_age = st.number_input(
            "Current Age",
            min_value=1,
            max_value=130,
            value=int(user_profile['current_age']),
            help="Your age today"
        )
        target_age = st.number_input(
            "Target Age (Goal)",
            min_value=current_age + 1,
            max_value=130,
            value=int(user_profile['target_age']),
            help="Age you want to ensure money lasts until"
        )
        work_end_age = st.number_input(
            "Work End Age",
            min_value=current_age,
            max_value=100,
            value=int(user_profile['work_end_age']),
            help="Age when you stop working"
        )
        current_work_income = st.number_input(
            "Current Annual Work Income ($)",
            min_value=0,
            value=int(user_profile['current_work_income']),
            step=5000,
            help="Current annual salary/income (projected to grow at inflation rate)"
        )

    with prof_col2:
        st.markdown("**Social Security**")
        ss_start_age = st.number_input(
            "SS Start Age",
            min_value=62,
            max_value=70,
            value=int(user_profile['ss_start_age']),
            help="Age when you start claiming Social Security"
        )
        ss_monthly_benefit = st.number_input(
            "SS Monthly Benefit ($)",
            min_value=0,
            value=int(user_profile['ss_monthly_benefit']),
            step=100,
            help="Expected monthly Social Security benefit"
        )
        ss_cola = st.slider(
            "SS COLA (%)",
            min_value=0.0,
            max_value=5.0,
            value=float(user_profile['ss_cola'] * 100),
            step=0.1,
            help="Social Security cost of living adjustment"
        ) / 100

        st.markdown("**Assumptions**")
        inflation_rate = st.slider(
            "Inflation Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=float(user_profile['inflation_rate'] * 100),
            step=0.5
        ) / 100
        max_flex_reduction = st.slider(
            "Max Flexible Spending Cut (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(user_profile['max_flex_reduction'] * 100),
            step=5.0,
            help="Maximum reduction allowed for flexible expenses before withdrawing from portfolio"
        ) / 100

    # Display RMD starting age based on birth year
    from calculations import get_rmd_starting_age
    current_year = 2026
    birth_year = current_year - current_age
    rmd_starting_age = get_rmd_starting_age(birth_year)
    
    st.divider()
    st.info(f"📋 **Tax Info:** Based on your birth year ({birth_year}), Required Minimum Distributions (RMDs) "
            f"from Traditional IRA and 401(k) accounts will begin at age **{rmd_starting_age}**.")

    # Handle save button click
    if save_profile_clicked:
        profile_data = {
            'current_age': current_age,
            'target_age': target_age,
            'work_end_age': work_end_age,
            'current_work_income': current_work_income,
            'work_income_growth': 0,
            'ss_start_age': ss_start_age,
            'ss_monthly_benefit': ss_monthly_benefit,
            'ss_cola': ss_cola,
            'inflation_rate': inflation_rate,
            'max_flex_reduction': max_flex_reduction
        }
        db_manager.save_user_profile(username, profile_data)
        db_manager.save_user_accounts(username, st.session_state.accounts)
        db_manager.save_user_expenses(username, st.session_state.expense_categories)
        db_manager.save_user_events(username, st.session_state.events)
        st.success("Configuration saved!")
        st.balloons()


# --- ACCOUNTS TAB ---
with config_tabs[1]:
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("Investment Accounts")
    with header_col2:
        st.write("")
        if st.button("💾 Save Accounts", key="save_accounts_header", type="primary"):
            db_manager.save_user_accounts(username, st.session_state.accounts)
            st.success("Accounts saved!")
    
    st.caption("Each account has a type (which controls contribution rules), a planned annual "
               "contribution, and a withdrawal priority. Deficits withdraw in priority order (1 = first).")

    # Account type options for the dropdown
    account_type_options = list(ACCOUNT_TYPE_LABELS.keys())
    account_type_display = list(ACCOUNT_TYPE_LABELS.values())

    # Summary totals at the top
    total_balance = sum(acc['balance'] for acc in st.session_state.accounts)
    total_planned = sum(acc.get('planned_contribution', 0)
                        for acc in st.session_state.accounts)
    col1, col2 = st.columns(2)
    col1.info(f"**Total Portfolio: ${total_balance:,.0f}**")
    col2.info(f"**Total Planned Contributions: ${total_planned:,.0f}/year**")

    # Display current accounts
    for i, acc in enumerate(st.session_state.accounts):
        # Create a unique key for this account expander
        expander_key = f"account_expander_{i}"
        
        # Look up display label for this account's type
        acc_type_label = ACCOUNT_TYPE_LABELS.get(
            acc.get('account_type', 'taxable_brokerage'), 'Taxable Brokerage')
        expander_label = (f"**{acc['name']}** ({acc_type_label}) | "
                          f"Balance: ${acc['balance']:,.0f}")
        
        # Use st.container with a manual toggle instead of st.expander for better control
        container_expanded = st.session_state.get(expander_key, False)
        
        # Create a clickable header
        header_col, remove_col = st.columns([0.95, 0.05])
        with header_col:
            arrow = "▼" if container_expanded else "▶"
            if st.button(f"{arrow} {expander_label}", key=f"toggle_{expander_key}"):
                st.session_state[expander_key] = not container_expanded
                st.rerun()
        with remove_col:
            if st.button("🗑️", key=f"remove_acc_{i}", help="Remove this account"):
                st.session_state.accounts.pop(i)
                # Clean up expander state
                if expander_key in st.session_state:
                    del st.session_state[expander_key]
                st.rerun()
        
        # Show content if expanded
        if container_expanded:
            col1, col2 = st.columns(2)
            with col1:
                acc['name'] = st.text_input(
                    "Account Name",
                    value=acc['name'],
                    key=f"acc_name_{i}"
                )
                current_type = acc.get('account_type', 'taxable_brokerage')
                type_index = (account_type_options.index(current_type)
                              if current_type in account_type_options else 3)
                acc['account_type'] = account_type_options[
                    st.selectbox(
                        "Account Type",
                        range(len(account_type_display)),
                        index=type_index,
                        format_func=lambda x: account_type_display[x],
                        key=f"acc_type_{i}",
                        help="Controls contribution limits and RMDs. 401(k) and Traditional IRA require RMDs starting at age 70/72/73/75 (varies by birth year per SECURE Act 2.0)."
                    )
                ]
                acc['balance'] = st.number_input(
                    "Current Balance ($)",
                    min_value=0,
                    value=int(acc['balance']),
                    step=1000,
                    key=f"acc_bal_{i}"
                )
            with col2:
                acc['return'] = st.number_input(
                    "Expected Annual Return (%)",
                    min_value=0.0,
                    value=float(acc['return'] * 100),
                    step=0.5,
                    key=f"acc_ret_{i}"
                ) / 100
                acc['planned_contribution'] = st.number_input(
                    "Planned Annual Contribution ($)",
                    min_value=0,
                    value=int(acc.get('planned_contribution', 0)),
                    step=500,
                    key=f"acc_planned_{i}",
                    help="Flat annual amount you plan to contribute"
                )
                
                # Show option to continue contributions after retirement for eligible account types
                acc_type = acc.get('account_type', 'taxable_brokerage')
                if acc_type in ['traditional_ira', 'roth_ira', 'taxable_brokerage']:
                    # Create account-specific help text
                    help_texts = {
                        'traditional_ira': "If checked, contributions continue until age 73 (IRS limit). RMDs start at age 70/72/73/75 depending on birth year. Requires earned income.",
                        'roth_ira': "If checked, contributions continue indefinitely. No RMDs required. Requires earned income and income limits apply.",
                        'taxable_brokerage': "If checked, contributions continue indefinitely as long as you have income."
                    }
                    acc['continue_post_retirement'] = st.checkbox(
                        "Continue contributions after retirement",
                        value=acc.get('continue_post_retirement', False),
                        key=f"acc_continue_{i}",
                        help=help_texts.get(acc_type, "Continue contributions after work ends")
                    )
                else:
                    acc['continue_post_retirement'] = False
                
                acc['priority'] = st.number_input(
                    "Withdrawal Priority",
                    min_value=1,
                    max_value=10,
                    value=int(acc['priority']),
                    key=f"acc_pri_{i}",
                    help="1 = withdraw first, 2 = second, etc."
                )

            # --- HISTORICAL SNAPSHOTS ---
            st.markdown("**Account History**")

            snapshots = db_manager.load_snapshots(username, acc['name'])

            if snapshots:
                # Calculate derived metrics for each snapshot
                display_rows = []
                for s_idx, snap in enumerate(snapshots):
                    row = {
                        'Date': snap['date'],
                        'Contributed': f"${snap['contributed']:,.0f}",
                        'Total Value': f"${snap['total_value']:,.0f}",
                    }
                    if s_idx == 0:
                        # First snapshot is the baseline; no previous to compare
                        row['Invest. Gain'] = 'N/A (baseline)'
                        row['Total Change %'] = 'N/A'
                        row['Invest. Return %'] = 'N/A'
                    else:
                        prev = snapshots[s_idx - 1]
                        # Investment gain = how much the investments earned,
                        # separate from money the user put in
                        invest_gain = (snap['total_value'] - prev['total_value']
                                       - snap['contributed'])
                        days = (datetime.strptime(snap['date'], '%Y-%m-%d')
                                - datetime.strptime(prev['date'], '%Y-%m-%d')).days
                        annualize = 365 / days if days > 0 else 1
                        prev_val = prev['total_value']

                        row['Invest. Gain'] = f"${invest_gain:,.0f}"
                        if prev_val > 0:
                            total_change = snap['total_value'] - prev_val
                            row['Total Change %'] = (
                                f"{(total_change / prev_val) * annualize * 100:.1f}% ann.")
                            row['Invest. Return %'] = (
                                f"{(invest_gain / prev_val) * annualize * 100:.1f}% ann.")
                        else:
                            row['Total Change %'] = 'N/A'
                            row['Invest. Return %'] = 'N/A'

                    display_rows.append(row)

                st.dataframe(
                    pd.DataFrame(display_rows),
                    width='stretch',
                    hide_index=True
                )

                # Delete snapshot buttons
                for s_idx, snap in enumerate(snapshots):
                    if st.button(
                        f"Delete {snap['date']} snapshot",
                        key=f"del_snap_{i}_{s_idx}"
                    ):
                        db_manager.delete_snapshot(username, snap['id'])
                        st.rerun()

                # Auto-update balance from most recent snapshot
                latest_value = snapshots[-1]['total_value']
                if abs(acc['balance'] - latest_value) > 0.01:
                    acc['balance'] = latest_value
            else:
                st.caption("No snapshots recorded yet. Add one below to start tracking performance.")

            # Add snapshot — no st.form, so Enter won't accidentally save
            st.markdown("**Record a new snapshot**")
            snap_cols = st.columns(3)
            with snap_cols[0]:
                snap_date = st.date_input(
                    "Date",
                    value=date.today(),
                    key=f"snap_date_{i}"
                )
            with snap_cols[1]:
                snap_contributed = st.number_input(
                    "Contributed Since Last Snapshot ($)",
                    min_value=0,
                    value=0,
                    step=500,
                    key=f"snap_contrib_{i}",
                    help="Money you added to this account since the last snapshot"
                )
            with snap_cols[2]:
                snap_value = st.number_input(
                    "Total Account Value ($)",
                    min_value=0,
                    value=int(acc['balance']),
                    step=1000,
                    key=f"snap_value_{i}",
                    help="Current total value of this account"
                )

            if st.button("Save Snapshot", key=f"save_snap_{i}"):
                db_manager.save_snapshot(
                    username, acc['name'],
                    snap_date.isoformat(),
                    snap_contributed, snap_value
                )
                acc['balance'] = snap_value
                st.rerun()

    # Add new account button
    if st.button("Add Account"):
        new_index = len(st.session_state.accounts)
        st.session_state.accounts.append({
            'name': f'Account {new_index + 1}',
            'account_type': 'taxable_brokerage',
            'balance': 100,
            'return': 0.08,
            'contrib_share': 0,
            'planned_contribution': 0,
            'priority': new_index + 1
        })
        st.session_state.expander_accounts[new_index] = True
        st.rerun()
    


# --- EXPENSES TAB ---
with config_tabs[2]:
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("Expense Categories")
    with header_col2:
        st.write("")
        if st.button("💾 Save Expenses", key="save_expenses_header", type="primary"):
            db_manager.save_user_expenses(username, st.session_state.expense_categories)
            st.success("Expenses saved!")
    
    st.caption("CORE expenses cannot be reduced. FLEX expenses can be cut up to the max % if needed.")
    
    # Display categories
    for i, exp in enumerate(st.session_state.expense_categories):
        # Create a unique key for this expense expander
        expander_key = f"expense_expander_{i}"
        
        # Build label at render time so it reflects current values
        expander_label = f"**{exp['name']}** | ${exp['amount']:,.0f}/year | {exp['type']}"
        
        # Use st.container with a manual toggle instead of st.expander for better control
        container_expanded = st.session_state.get(expander_key, False)
        
        # Create a clickable header
        header_col, remove_col = st.columns([0.95, 0.05])
        with header_col:
            arrow = "▼" if container_expanded else "▶"
            if st.button(f"{arrow} {expander_label}", key=f"toggle_{expander_key}"):
                st.session_state[expander_key] = not container_expanded
                st.rerun()
        with remove_col:
            if st.button("🗑️", key=f"remove_exp_{i}", help="Remove this expense"):
                st.session_state.expense_categories.pop(i)
                # Clean up expander state
                if expander_key in st.session_state:
                    del st.session_state[expander_key]
                st.rerun()
        
        # Show content if expanded
        if container_expanded:
            col1, col2 = st.columns(2)
            with col1:
                exp['name'] = st.text_input(
                    "Category Name",
                    value=exp['name'],
                    key=f"exp_name_{i}"
                )
                exp['amount'] = st.number_input(
                    "Annual Amount ($)",
                    min_value=0,
                    value=int(exp['amount']),
                    step=500,
                    key=f"exp_amt_{i}",
                    help="Amount in today's dollars (will be inflated)"
                )
            with col2:
                exp['type'] = st.selectbox(
                    "Type",
                    options=['CORE', 'FLEX'],
                    index=0 if exp['type'] == 'CORE' else 1,
                    key=f"exp_type_{i}",
                    help="CORE = essential, FLEX = can be reduced if needed"
                )
                st.write("")  # Spacing
    
    # Add new expense
    if st.button("➕ Add Expense Category"):
        new_index = len(st.session_state.expense_categories)
        st.session_state.expense_categories.append({
            'name': f'Category {new_index + 1}',
            'amount': 5000,
            'type': 'FLEX'
        })
        st.rerun()
    
    # Summary
    total_core = sum(e['amount'] for e in st.session_state.expense_categories if e['type'] == 'CORE')
    total_flex = sum(e['amount'] for e in st.session_state.expense_categories if e['type'] == 'FLEX')
    total_expenses = total_core + total_flex
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total CORE", f"${total_core:,.0f}/year")
    col2.metric("Total FLEX", f"${total_flex:,.0f}/year")
    col3.metric("Total Expenses", f"${total_expenses:,.0f}/year")
    


# --- EVENTS TAB ---
with config_tabs[3]:
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.subheader("One-Time Financial Events")
    with header_col2:
        st.write("")
        if st.button("💾 Save Events", key="save_events_header", type="primary"):
            db_manager.save_user_events(username, st.session_state.events)
            st.success("Events saved!")
    
    # Add custom CSS for left-aligned event buttons
    st.markdown("""
    <style>
    /* Left-align event toggle buttons */
    .stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
    }
    .stButton > button > div {
        text-align: left !important;
        justify-content: flex-start !important;
    }
    .stButton > button p {
        text-align: left !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Explanation
    with st.expander("ℹ️ What are One-Time Events?", expanded=False):
        st.markdown("""
        **One-Time Events** let you model major transactions that directly affect your investment accounts in specific years:
        
        **Withdrawals (money out of an account):**
        - Major purchases (car, home renovation, boat)
        - College tuition payments
        - Medical procedures
        - Large gifts to family
        
        **Additions (money into an account):**
        - Inheritance deposited into investment accounts
        - Property sale proceeds invested
        - Bonus or severance package invested
        - Life insurance payout invested
        - Large tax refunds invested
        
        **How they work:**
        - Events directly adjust the specified account's balance in the event year
        - They happen AFTER your normal annual income, expenses, and contributions
        - They don't interfere with your regular cash flow or budget
        - Perfect for modeling life events that directly impact your retirement portfolio
        
        **Example:** "In 2030, withdraw $25,000 from Brokerage Account for car purchase" will directly 
        reduce your brokerage account balance by $25,000 in 2030.
        """)
    
    if len(st.session_state.events) == 0:
        st.info("No events configured. Add major one-time expenses or income below.")
    
    for i, evt in enumerate(st.session_state.events):
        # Create a unique key for this event expander
        expander_key = f"event_expander_{i}"
        
        # Determine if this is a withdrawal or addition based on sign
        is_withdrawal = evt['amount'] > 0
        abs_amount = abs(evt['amount'])
        event_type = "Withdrawal" if is_withdrawal else "Addition"
        account_name = evt.get('account_name', 'Unknown Account')
        
        # Build label at render time so it reflects current values
        expander_label = f"**{evt['description']}** | ${abs_amount:,.0f} {event_type} | {account_name} | {evt['year']}"
        
        # Use st.container with a manual toggle instead of st.expander for better control
        container_expanded = st.session_state.get(expander_key, False)
        
        # Create a clickable header
        header_col, remove_col = st.columns([0.95, 0.05])
        with header_col:
            arrow = "▼" if container_expanded else "▶"
            # Use button without container width to keep natural left alignment
            if st.button(f"{arrow} {expander_label}", key=f"toggle_{expander_key}"):
                st.session_state[expander_key] = not container_expanded
                st.rerun()
        with remove_col:
            if st.button("🗑️", key=f"remove_evt_{i}", help="Remove this event"):
                st.session_state.events.pop(i)
                # Clean up expander state
                if expander_key in st.session_state:
                    del st.session_state[expander_key]
                st.rerun()
        
        # Show content if expanded
        if container_expanded:
            col1, col2 = st.columns(2)
            with col1:
                evt['year'] = st.number_input(
                    "Year",
                    min_value=2026,
                    max_value=2100,
                    value=int(evt['year']),
                    key=f"evt_year_{i}"
                )
                evt['description'] = st.text_input(
                    "Description",
                    value=evt['description'],
                    key=f"evt_desc_{i}",
                    help="e.g., 'New car', 'Inheritance from estate', 'Roof replacement'"
                )
                
                # Account selector
                account_names = [acc['name'] for acc in st.session_state.accounts]
                if account_names:
                    current_account = evt.get('account_name', account_names[0])
                    if current_account not in account_names:
                        current_account = account_names[0]
                    account_index = account_names.index(current_account)
                    evt['account_name'] = st.selectbox(
                        "Account",
                        options=account_names,
                        index=account_index,
                        key=f"evt_account_{i}",
                        help="Which investment account will be affected"
                    )
                else:
                    st.warning("⚠️ No accounts configured. Add accounts first.")
                    evt['account_name'] = "No Account"
                    
            with col2:
                # Event type selector
                event_type_current = st.radio(
                    "Event Type",
                    options=["Withdrawal", "Addition"],
                    index=0 if is_withdrawal else 1,
                    key=f"evt_type_{i}",
                    horizontal=True,
                    help="Withdrawal = take money out, Addition = put money in"
                )
                
                # Amount (always positive in UI)
                amount_input = st.number_input(
                    "Amount ($)",
                    min_value=0,
                    value=int(abs_amount),
                    step=1000,
                    key=f"evt_amt_{i}",
                    help="Enter the amount as a positive number"
                )
                
                # Convert back to signed amount for storage
                evt['amount'] = amount_input if event_type_current == "Withdrawal" else -amount_input
            
            st.divider()
    
    if st.button("➕ Add Event"):
        current_year = 2026
        new_index = len(st.session_state.events)
        # Default to first account if available
        default_account = st.session_state.accounts[0]['name'] if st.session_state.accounts else 'No Account'
        st.session_state.events.append({
            'year': current_year,
            'description': 'New Event',
            'amount': 10000,  # Default to withdrawal
            'account_name': default_account
        })
        # Auto-open the newly created event
        st.session_state[f"event_expander_{new_index}"] = True
        st.rerun()
    


# ===== RUN PROJECTION =====
# Computed after all config tabs so it uses current widget values.

# Ensure backward compatibility for accounts that may not have all fields
accounts = []
for acc in st.session_state.accounts:
    # Ensure all required fields exist with defaults
    account = AccountBucket(
        name=acc.get('name', 'Unknown'),
        balance=float(acc.get('balance', 0)),
        annual_return=float(acc.get('return', 0.07)),
        priority=int(acc.get('priority', 1)),
        account_type=str(acc.get('account_type', 'taxable_brokerage')),
        planned_contribution=float(acc.get('planned_contribution', 0)),
        continue_post_retirement=bool(acc.get('continue_post_retirement', False))
    )
    accounts.append(account)

expenses = [
    ExpenseCategory(
        name=exp['name'],
        annual_amount=exp['amount'],
        category_type=exp['type']
    )
    for exp in st.session_state.expense_categories
]

events_list = [
    OneTimeEvent(
        year=evt['year'],
        description=evt['description'],
        amount=evt['amount'],
        account_name=evt.get('account_name', 'No Account')
    )
    for evt in st.session_state.events
]

projection = run_comprehensive_projection(
    current_age=current_age,
    target_age=target_age,
    current_work_income=current_work_income,
    work_end_age=work_end_age,
    ss_start_age=ss_start_age,
    ss_monthly_benefit=ss_monthly_benefit,
    ss_cola=ss_cola,
    accounts=accounts,
    expense_categories=expenses,
    max_flex_reduction=max_flex_reduction,
    events=events_list,
    inflation_rate=inflation_rate,
    max_age=110
)

analysis = analyze_retirement_plan(
    projection, 
    target_age=target_age, 
    work_end_age=work_end_age,
    accounts=accounts,
    current_age=current_age
)

# Look up portfolio balances at key ages
retirement_row = projection[projection['age'] == work_end_age]
balance_at_retirement = (retirement_row.iloc[0]['total_portfolio']
                         if len(retirement_row) > 0 else None)

target_row = projection[projection['age'] == target_age]
balance_at_target = (target_row.iloc[0]['total_portfolio']
                     if len(target_row) > 0 else None)

# ===== FILL IN DASHBOARD =====

with dashboard_container:
    st.header("Dashboard")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Status",
            analysis['status'],
            delta="Good" if analysis['status'] == 'ON TRACK' else "Warning"
        )

    with col2:
        if analysis['run_out_age']:
            st.metric("Money Lasts Until", f"Age {analysis['run_out_age']}")
        else:
            st.metric("Money Lasts Until", "Age 110+")

    with col3:
        cushion = analysis['cushion_years']
        st.metric(
            "Cushion",
            f"{cushion} years",
            delta="Good" if cushion >= 0 else "Short"
        )

    with col4:
        if balance_at_retirement is not None:
            st.metric(
                f"At Retirement ({work_end_age})",
                f"${balance_at_retirement:,.0f}"
            )
        else:
            st.metric(f"At Retirement ({work_end_age})", "N/A")

    with col5:
        if balance_at_target is not None:
            st.metric(
                f"At Target Age ({target_age})",
                f"${balance_at_target:,.0f}"
            )
        else:
            st.metric(f"At Target Age ({target_age})", "Depleted")

    if analysis['warnings']:
        st.warning("**Warnings:**\n\n" + "\n\n".join(f"- {w}" for w in analysis['warnings']))
    else:
        st.success("No warnings detected. Plan looks solid!")
    
    # Show sustainable withdrawal guidance if available
    if analysis.get('sustainable_withdrawal_monthly') is not None:
        monthly_val = analysis['sustainable_withdrawal_monthly']
        annual_val = analysis['sustainable_withdrawal_annual']
        st.markdown(
            f"<div style='padding: 10px; background-color: #d1ecf1; border-left: 5px solid #0c5460; border-radius: 5px;'>"
            f"ℹ️ <strong>Conservative Sustainable Retirement Spending:</strong> "
            f"To make your portfolio last until age {target_age}, you can safely withdraw up to "
            f"<span style='font-size: 1.4em; font-weight: bold;'>${monthly_val:,.0f}/month</span> "
            f"(<span style='font-size: 1.4em; font-weight: bold;'>${annual_val:,.0f}/year</span>) "
            f"starting at retirement (age {work_end_age}). "
            f"<br><br>"
            f"<em style='font-size: 0.9em;'>This conservative estimate uses different assumptions than your main projection: "
            f"8% nominal investment return, 2.5% inflation (5.5% real return), includes your planned contributions, "
            f"and assumes your portfolio compounds without withdrawals before retirement. "
            f"This provides a benchmark independent from your custom account settings and expense projections.</em>"
            f"</div>",
            unsafe_allow_html=True
        )

# --- PROJECTIONS TAB ---
# --- SANITY CHECKS TAB ---
with config_tabs[4]:
    st.subheader("Current Year Sanity Checks")
    st.markdown("""
    Quick reality check on your numbers **as of today** (age {}).
    This helps catch data entry errors before running projections.
    """.format(current_age))
    
    # Calculate current year metrics
    current_work_income_val = current_work_income if current_age < work_end_age else 0
    current_ss_income = ss_monthly_benefit * 12 if current_age >= ss_start_age else 0
    current_total_income = current_work_income_val + current_ss_income
    
    # Get current expenses
    current_core_expenses = sum(e['amount'] for e in st.session_state.expense_categories if e['type'] == 'CORE')
    current_flex_expenses = sum(e['amount'] for e in st.session_state.expense_categories if e['type'] == 'FLEX')
    current_total_expenses = current_core_expenses + current_flex_expenses
    
    # Get planned contributions for current year
    current_planned_contributions = 0
    for acc in st.session_state.accounts:
        acc_type = acc.get('account_type', 'taxable_brokerage')
        planned_contrib = acc.get('planned_contribution', 0)
        continue_post_ret = acc.get('continue_post_retirement', False)
        
        # Check if this account can receive contributions this year
        from calculations import can_contribute
        if can_contribute(acc_type, current_age, work_end_age, continue_post_ret):
            current_planned_contributions += planned_contrib
    
    # Calculate net cash flow
    net_before_contributions = current_total_income - current_total_expenses
    net_after_contributions = net_before_contributions - current_planned_contributions
    
    # Display in columns
    st.markdown("### 📊 Current Year Cash Flow")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**💵 Income**")
        st.metric("Work Income", f"${current_work_income_val:,.0f}")
        st.metric("Social Security", f"${current_ss_income:,.0f}")
        st.metric("Total Income", f"${current_total_income:,.0f}", 
                 help="Annual income for current year")
    
    with col2:
        st.markdown("**📤 Outflows**")
        st.metric("Core Expenses", f"${current_core_expenses:,.0f}", 
                 help="Essential spending that cannot be reduced")
        st.metric("Flex Expenses", f"${current_flex_expenses:,.0f}",
                 help="Discretionary spending that can be reduced up to 50%")
        st.metric("Planned Contributions", f"${current_planned_contributions:,.0f}",
                 help="Annual contributions to investment accounts")
        st.metric("Total Outflows", f"${current_total_expenses + current_planned_contributions:,.0f}")
    
    with col3:
        st.markdown("**💰 Net Position**")
        
        # Net before contributions
        delta_color_before = "normal" if net_before_contributions >= 0 else "inverse"
        st.metric(
            "After Expenses",
            f"${net_before_contributions:,.0f}",
            delta=None,
            help="Income minus expenses (before contributions)"
        )
        
        # Net after contributions
        delta_color_after = "normal" if net_after_contributions >= 0 else "inverse"
        st.metric(
            "After Contributions",
            f"${net_after_contributions:,.0f}",
            delta=None,
            help="Income minus expenses and planned contributions"
        )
        
        # Savings rate
        if current_total_income > 0:
            savings_rate = (current_planned_contributions / current_total_income) * 100
            st.metric("Savings Rate", f"{savings_rate:.1f}%",
                     help="Planned contributions as % of income")
    
    st.divider()
    
    # Warnings and recommendations
    st.markdown("### ⚠️ Quick Checks")
    
    # Track if any issues were found
    issues_found = []
    
    checks_col1, checks_col2 = st.columns(2)
    
    with checks_col1:
        # Income checks
        if current_total_income == 0 and current_age < work_end_age:
            st.warning("⚠️ No income configured but still before retirement age")
            issues_found.append(True)
        
        if current_work_income_val > 0 and current_work_income_val < 10000:
            st.info("ℹ️ Work income seems low - verify this is annual (not monthly)")
            issues_found.append(True)
        
        if current_total_expenses == 0:
            st.warning("⚠️ No expenses configured")
            issues_found.append(True)
        
        if current_core_expenses == 0:
            st.info("ℹ️ No core expenses - consider adding housing, food, healthcare")
            issues_found.append(True)
    
    with checks_col2:
        # Expense checks  
        if current_total_income > 0:
            expense_ratio = (current_total_expenses / current_total_income) * 100
            if expense_ratio > 100:
                st.error(f"❌ Expenses are {expense_ratio:.0f}% of income - currently running a deficit")
                issues_found.append(True)
            elif expense_ratio > 90:
                st.warning(f"⚠️ Expenses are {expense_ratio:.0f}% of income - very tight budget")
                issues_found.append(True)
            elif expense_ratio < 30:
                st.info(f"ℹ️ Expenses are only {expense_ratio:.0f}% of income - verify numbers are annual")
                issues_found.append(True)
        
        # Contribution checks
        if net_after_contributions < 0:
            shortfall = abs(net_after_contributions)
            st.error(f"❌ Planned contributions exceed available funds by ${shortfall:,.0f}")
            issues_found.append(True)
        
        if current_planned_contributions > 0 and current_total_income == 0:
            st.warning("⚠️ Planned contributions set but no income configured")
            issues_found.append(True)
    
    # If no issues found, show success message
    if not issues_found:
        st.success("✅ All basic validation checks passed! Your current year configuration looks reasonable.")
    
    st.divider()
    
    # Account balances summary
    st.markdown("### 🏦 Current Account Balances")
    total_portfolio = sum(acc['balance'] for acc in st.session_state.accounts)
    
    acct_col1, acct_col2 = st.columns([2, 1])
    
    with acct_col1:
        account_df = pd.DataFrame([{
            'Account': acc['name'],
            'Type': ACCOUNT_TYPE_LABELS.get(acc.get('account_type', 'taxable_brokerage'), 'Unknown'),
            'Balance': f"${acc['balance']:,.0f}",
            'Annual Return': f"{acc['return']*100:.1f}%",
            'Planned Contrib': f"${acc.get('planned_contribution', 0):,.0f}"
        } for acc in st.session_state.accounts])
        
        st.dataframe(account_df, hide_index=True, width='stretch')
    
    with acct_col2:
        st.metric("Total Portfolio", f"${total_portfolio:,.0f}")
        
        if total_portfolio > 0 and current_total_expenses > 0:
            years_of_expenses = total_portfolio / current_total_expenses
            st.metric("Years of Expenses", f"{years_of_expenses:.1f}",
                     help="Current portfolio ÷ annual expenses (ignoring investment returns)")

# --- PROJECTIONS TAB ---
with config_tabs[5]:
    st.subheader("Financial Overview")

    # Summary stats
    years_working = len(projection[projection['work_income'] > 0])
    years_on_ss = len(projection[projection['ss_income'] > 0])
    avg_flex_reduction = (1 - projection['flex_multiplier'].mean()) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Years Working", years_working)
    col2.metric("Years on Social Security", years_on_ss)
    col3.metric("Avg Flex Reduction", f"{avg_flex_reduction:.1f}%")

    # Create comprehensive overview chart
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("Portfolio Balance", "Income vs Expenses", "Account Balances"),
        vertical_spacing=0.12,
        row_heights=[0.4, 0.3, 0.3]
    )

    # Row 1: Total portfolio
    fig.add_trace(
        go.Scatter(
            x=projection['age'],
            y=projection['total_portfolio'],
            mode='lines',
            name='Total Portfolio',
            fill='tozeroy',
            line=dict(color='green', width=2)
        ),
        row=1, col=1
    )

    fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=1)

    # Row 2: Income and expenses
    fig.add_trace(
        go.Scatter(
            x=projection['age'],
            y=projection['total_income'],
            mode='lines',
            name='Income',
            line=dict(color='blue')
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=projection['age'],
            y=projection['total_expenses'],
            mode='lines',
            name='Expenses',
            line=dict(color='orange')
        ),
        row=2, col=1
    )

    # Row 3: Individual accounts
    for acc in st.session_state.accounts:
        col_name = f"{acc['name']}_balance"
        if col_name in projection.columns:
            fig.add_trace(
                go.Scatter(
                    x=projection['age'],
                    y=projection[col_name],
                    mode='lines',
                    name=acc['name'],
                    stackgroup='one'
                ),
                row=3, col=1
            )

    fig.update_xaxes(title_text="Age", row=3, col=1)
    fig.update_yaxes(title_text="Balance ($)", row=1, col=1)
    fig.update_yaxes(title_text="Annual ($)", row=2, col=1)
    fig.update_yaxes(title_text="Balance ($)", row=3, col=1)

    fig.update_layout(height=900, showlegend=True, hovermode='x unified')

    st.plotly_chart(fig, width='stretch')

    # Portfolio balance detail
    st.divider()
    st.subheader("Portfolio Balance Over Time")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=projection['age'],
        y=projection['total_portfolio'],
        mode='lines',
        name='Total Portfolio',
        fill='tozeroy',
        line=dict(color='darkgreen', width=3)
    ))

    fig.add_vline(
        x=target_age,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Target Age ({target_age})"
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="red",
        annotation_text="Zero Balance"
    )

    fig.update_layout(
        title="Total Investment Portfolio Projection",
        xaxis_title="Age",
        yaxis_title="Portfolio Balance ($)",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, width='stretch')

    # Income vs expenses detail
    st.divider()
    st.subheader("Income vs Expenses")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=projection['age'],
            y=projection['work_income'],
            mode='lines',
            name='Work Income',
            stackgroup='income',
            line=dict(color='blue')
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=projection['age'],
            y=projection['ss_income'],
            mode='lines',
            name='Social Security',
            stackgroup='income',
            line=dict(color='lightblue')
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=projection['age'],
            y=projection['core_expenses'],
            mode='lines',
            name='Core Expenses',
            stackgroup='expenses',
            line=dict(color='red')
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=projection['age'],
            y=projection['flex_expenses_actual'],
            mode='lines',
            name='Flexible Expenses',
            stackgroup='expenses',
            line=dict(color='orange')
        ),
        secondary_y=False
    )

    fig.update_xaxes(title_text="Age")
    fig.update_yaxes(title_text="Annual Amount ($)", secondary_y=False)

    fig.update_layout(
        title="Income and Expense Breakdown",
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig, width='stretch')

    # Year-by-year table
    st.divider()
    st.subheader("Year-by-Year Detail")

    display_cols = [
        'year', 'age', 'work_income', 'ss_income', 'total_income',
        'core_expenses', 'flex_expenses_actual', 'total_expenses',
        'surplus_deficit', 'total_contributions', 'total_withdrawals',
        'total_portfolio'
    ]

    display_df = projection[display_cols].copy()

    currency_cols = ['work_income', 'ss_income', 'total_income', 'core_expenses',
                     'flex_expenses_actual', 'total_expenses', 'surplus_deficit',
                     'total_contributions', 'total_withdrawals', 'total_portfolio']

    for col in currency_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f'${x:,.0f}')

    st.dataframe(
        display_df,
        width='stretch',
        height=600
    )

    csv = projection.to_csv(index=False)
    st.download_button(
        label="Download Complete Projection (CSV)",
        data=csv,
        file_name="retirement_projection_detailed.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.caption(
    "This is your living financial control panel - update it annually and refine over time."
)
