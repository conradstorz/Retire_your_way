"""
Retirement Planning Application - V2 (Multi-User)

A transparent retirement planning tool implementing comprehensive financial modeling
with multiple account buckets, expense categories, and Social Security integration.

Features multi-user authentication with individual data persistence.
"""

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
    with st.expander("🔑 Forgot Password? Recover Account"):
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
    with st.expander("📝 New User Registration"):
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
                        
                        st.markdown("**You can now login with your credentials.**")
                        
                        if st.button("🔐 Return to Login Page", type="primary", key="return_login_1"):
                            st.rerun()
                    else:
                        st.error("Username already exists")
    
    st.stop()

elif authentication_status == None:
    st.warning('Please enter your username and password')
    
    # Password Recovery section
    with st.expander("🔑 Forgot Password? Recover Account"):
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
    with st.expander("📝 New User Registration"):
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
                        
                        st.markdown("**You can now login with your credentials.**")
                        
                        if st.button("🔐 Return to Login Page", type="primary", key="return_login_2"):
                            st.rerun()
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
    st.title("💰 Retirement Planning Calculator V2")
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

config_tabs = st.tabs(["📋 Profile", "💰 Accounts", "🏠 Expenses", "📅 One-Time Events", "📈 Projections"])

# --- PROFILE TAB ---
with config_tabs[0]:
    st.subheader("Personal Profile")

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

    st.divider()
    if st.button("💾 Save All Configuration", type="primary"):
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
    st.subheader("Investment Accounts")
    st.caption("Each account has a type (which controls contribution rules), a planned annual "
               "contribution, and a withdrawal priority. Deficits withdraw in priority order (1 = first).")

    # Account type options for the dropdown
    account_type_options = list(ACCOUNT_TYPE_LABELS.keys())
    account_type_display = list(ACCOUNT_TYPE_LABELS.values())

    # Display current accounts
    for i, acc in enumerate(st.session_state.accounts):
        # Look up display label for this account's type
        acc_type_label = ACCOUNT_TYPE_LABELS.get(
            acc.get('account_type', 'taxable_brokerage'), 'Taxable Brokerage')
        expander_label = (f"**{acc['name']}** ({acc_type_label}) "
                          f"- ${acc['balance']:,.0f}")

        with st.expander(expander_label, expanded=False):
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
                        help="Controls when contributions stop"
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
                    max_value=20.0,
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

            if st.button(f"Remove {acc['name']}", key=f"remove_acc_{i}"):
                st.session_state.accounts.pop(i)
                st.rerun()

    # Add new account button
    if st.button("Add Account"):
        st.session_state.accounts.append({
            'name': f'Account {len(st.session_state.accounts) + 1}',
            'account_type': 'taxable_brokerage',
            'balance': 10000,
            'return': 0.07,
            'contrib_share': 0,
            'planned_contribution': 0,
            'priority': len(st.session_state.accounts) + 1
        })
        st.rerun()

    total_balance = sum(acc['balance'] for acc in st.session_state.accounts)
    total_planned = sum(acc.get('planned_contribution', 0)
                        for acc in st.session_state.accounts)
    col1, col2 = st.columns(2)
    col1.info(f"**Total Portfolio: ${total_balance:,.0f}**")
    col2.info(f"**Total Planned Contributions: ${total_planned:,.0f}/year**")

# --- EXPENSES TAB ---
with config_tabs[2]:
    st.subheader("Expense Categories")
    st.caption("CORE expenses cannot be reduced. FLEX expenses can be cut up to the max % if needed.")
    
    # Display categories
    for i, exp in enumerate(st.session_state.expense_categories):
        with st.expander(f"**{exp['name']}** - ${exp['amount']:,.0f}/year ({exp['type']})", expanded=False):
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
            
            if st.button(f"🗑️ Remove {exp['name']}", key=f"remove_exp_{i}"):
                st.session_state.expense_categories.pop(i)
                st.rerun()
    
    # Add new expense
    if st.button("➕ Add Expense Category"):
        st.session_state.expense_categories.append({
            'name': f'Category {len(st.session_state.expense_categories) + 1}',
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
    st.subheader("One-Time Financial Events")
    st.caption("Positive amounts = expenses. Negative amounts = windfalls.")
    
    if len(st.session_state.events) == 0:
        st.info("No events configured. Add major one-time expenses or income below.")
    
    for i, evt in enumerate(st.session_state.events):
        with st.expander(f"**{evt['description']}** - ${evt['amount']:,.0f} in {evt['year']}", expanded=False):
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
                    key=f"evt_desc_{i}"
                )
            with col2:
                evt['amount'] = st.number_input(
                    "Amount ($)",
                    value=int(evt['amount']),
                    step=1000,
                    key=f"evt_amt_{i}",
                    help="Positive = expense, Negative = windfall"
                )
                st.write("")  # Spacing
            
            if st.button(f"🗑️ Remove Event", key=f"remove_evt_{i}"):
                st.session_state.events.pop(i)
                st.rerun()
    
    if st.button("➕ Add Event"):
        current_year = 2026
        st.session_state.events.append({
            'year': current_year,
            'description': 'New Event',
            'amount': 10000
        })
        st.rerun()

# ===== RUN PROJECTION =====
# Computed after all config tabs so it uses current widget values.

accounts = [
    AccountBucket(
        name=acc['name'],
        balance=acc['balance'],
        annual_return=acc['return'],
        priority=acc['priority'],
        account_type=acc.get('account_type', 'taxable_brokerage'),
        planned_contribution=acc.get('planned_contribution', 0)
    )
    for acc in st.session_state.accounts
]

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
        amount=evt['amount']
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

analysis = analyze_retirement_plan(projection, target_age=target_age)

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

# --- PROJECTIONS TAB ---
with config_tabs[4]:
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
