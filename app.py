import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import bcrypt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Banking Simulator",
    page_icon="🏦",
    layout="wide"
)

st.title("🏦 Personal Banking Simulator")
st.markdown("A simulated banking platform — "
            "accounts, transfers and statements.")
st.markdown("---")

USERS_FILE = "users.json"
TXN_FILE   = "transactions.json"

def load_json(path, default):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def hash_pw(pw):
    return bcrypt.hashpw(
        pw.encode(), bcrypt.gensalt()
    ).decode()

def check_pw(pw, hashed):
    return bcrypt.checkpw(
        pw.encode(), hashed.encode())

if 'users' not in st.session_state:
    st.session_state.users = load_json(
        USERS_FILE, {})
if 'transactions' not in st.session_state:
    st.session_state.transactions = load_json(
        TXN_FILE, [])
if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

def generate_account_number(username):
    return "AC" + str(
        abs(hash(username)) % 10**10
    ).zfill(10)

# ── AUTH SCREEN ───────────────────────────────
if st.session_state.logged_in_user is None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        auth_tab1, auth_tab2 = st.tabs(
            ["🔐 Login", "📝 Sign Up"])

        with auth_tab1:
            st.markdown("### Login")
            login_user = st.text_input(
                "Username:", key="login_u")
            login_pass = st.text_input(
                "Password:", type="password",
                key="login_p")
            if st.button("🔐 Login",
                         type="primary"):
                users = st.session_state.users
                if login_user in users and \
                        check_pw(
                            login_pass,
                            users[login_user]
                            ['password']):
                    st.session_state\
                        .logged_in_user = \
                        login_user
                    st.rerun()
                else:
                    st.error(
                        "Invalid username "
                        "or password!")

        with auth_tab2:
            st.markdown("### Create Account")
            new_user = st.text_input(
                "Choose username:",
                key="signup_u")
            new_name  = st.text_input(
                "Full name:", key="signup_n")
            new_pass  = st.text_input(
                "Choose password:",
                type="password",
                key="signup_p")
            initial_deposit = st.number_input(
                "Initial deposit (₹):",
                min_value=0, value=5000,
                step=500)

            if st.button("📝 Create Account",
                         type="primary"):
                if new_user.strip() and \
                        new_pass.strip():
                    if new_user in \
                            st.session_state\
                            .users:
                        st.error(
                            "Username already "
                            "exists!")
                    else:
                        acc_num = \
                            generate_account_number(
                                new_user)
                        st.session_state\
                            .users[new_user] = {
                            'password':  hash_pw(
                                new_pass),
                            'name':      new_name,
                            'account':   acc_num,
                            'balance':   initial_deposit,
                            'created':   str(
                                datetime.now())
                        }
                        save_json(
                            USERS_FILE,
                            st.session_state
                            .users)

                        if initial_deposit > 0:
                            st.session_state\
                                .transactions\
                                .append({
                                'account': acc_num,
                                'type':    'Deposit',
                                'amount':  initial_deposit,
                                'balance_after':
                                    initial_deposit,
                                'note':    'Initial deposit',
                                'date':    str(
                                    datetime.now())
                            })
                            save_json(
                                TXN_FILE,
                                st.session_state
                                .transactions)

                        st.success(
                            f"✅ Account created! "
                            f"Account No: {acc_num}")
                else:
                    st.warning(
                        "Fill all fields!")

    st.markdown("---")
    st.caption(
        "🔒 Educational simulation only. "
        "No real money or banking involved.")

# ── DASHBOARD ─────────────────────────────────
else:
    username = st.session_state.logged_in_user
    user     = st.session_state.users[username]

    col_a, col_b = st.columns([5, 1])
    with col_a:
        st.markdown(
            f"### 👋 Welcome, {user['name'] or username}")
    with col_b:
        if st.button("🚪 Logout"):
            st.session_state.logged_in_user = None
            st.rerun()

    my_txns = [
        t for t in st.session_state.transactions
        if t['account'] == user['account']
    ]
    txn_df = pd.DataFrame(my_txns) \
        if my_txns else pd.DataFrame(
            columns=['account', 'type',
                     'amount', 'balance_after',
                     'note', 'date'])
    if len(txn_df) > 0:
        txn_df['date'] = pd.to_datetime(
            txn_df['date'])

    tab1, tab2, tab3, tab4 = st.tabs([
        "💰 Dashboard",
        "💸 Transfer / Deposit",
        "📜 Statement",
        "📊 Spending Insights"
    ])

    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Account Number",
                  user['account'])
        c2.metric("Current Balance",
                  f"₹{user['balance']:,.2f}")
        c3.metric("Total Transactions",
                  len(my_txns))

        if len(txn_df) > 0:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=txn_df['date'],
                y=txn_df['balance_after'],
                mode='lines+markers',
                fill='tozeroy',
                line=dict(color='#1A56DB',
                          width=2),
                fillcolor='rgba(26,86,219,0.1)'
            ))
            fig.update_layout(
                title='Balance Over Time',
                height=350,
                template='plotly_white')
            st.plotly_chart(
                fig, use_container_width=True)

            st.markdown("#### Recent Activity")
            recent = txn_df.sort_values(
                'date', ascending=False).head(5)
            for _, t in recent.iterrows():
                icon = "🟢" if t['type'] in \
                    ['Deposit', 'Received'] \
                    else "🔴"
                st.markdown(
                    f"{icon} **{t['type']}** "
                    f"₹{t['amount']:,.2f} — "
                    f"{t['note']} "
                    f"({t['date'].strftime('%d %b, %H:%M')})")
        else:
            st.info("No transactions yet!")

    with tab2:
        action = st.radio(
            "Action:",
            ["💵 Deposit", "💸 Transfer to "
             "another account",
             "🏧 Withdraw"],
            horizontal=True
        )

        if action == "💵 Deposit":
            dep_amt = st.number_input(
                "Deposit amount (₹):",
                min_value=1, value=1000)
            if st.button("💵 Deposit",
                         type="primary"):
                user['balance'] += dep_amt
                st.session_state\
                    .users[username] = user
                save_json(
                    USERS_FILE,
                    st.session_state.users)
                st.session_state\
                    .transactions.append({
                    'account': user['account'],
                    'type':    'Deposit',
                    'amount':  dep_amt,
                    'balance_after': user[
                        'balance'],
                    'note':    'Self deposit',
                    'date':    str(
                        datetime.now())
                })
                save_json(
                    TXN_FILE,
                    st.session_state
                    .transactions)
                st.success(
                    f"✅ Deposited ₹{dep_amt:,}!")
                st.rerun()

        elif action == "🏧 Withdraw":
            wd_amt = st.number_input(
                "Withdraw amount (₹):",
                min_value=1, value=500)
            if st.button("🏧 Withdraw",
                         type="primary"):
                if wd_amt > user['balance']:
                    st.error(
                        "❌ Insufficient balance!")
                else:
                    user['balance'] -= wd_amt
                    st.session_state\
                        .users[username] = user
                    save_json(
                        USERS_FILE,
                        st.session_state.users)
                    st.session_state\
                        .transactions.append({
                        'account': user[
                            'account'],
                        'type':    'Withdrawal',
                        'amount':  wd_amt,
                        'balance_after': user[
                            'balance'],
                        'note':    'ATM withdrawal',
                        'date':    str(
                            datetime.now())
                    })
                    save_json(
                        TXN_FILE,
                        st.session_state
                        .transactions)
                    st.success(
                        f"✅ Withdrew ₹{wd_amt:,}!")
                    st.rerun()

        else:
            other_users = [
                u for u in
                st.session_state.users
                if u != username
            ]
            if not other_users:
                st.info(
                    "No other accounts exist "
                    "yet. Sign up another "
                    "user to test transfers!")
            else:
                to_user = st.selectbox(
                    "Transfer to:", other_users)
                transfer_amt = st.number_input(
                    "Amount (₹):",
                    min_value=1, value=500)
                transfer_note = st.text_input(
                    "Note:",
                    placeholder="e.g. Rent split")

                if st.button("💸 Send",
                             type="primary"):
                    if transfer_amt > \
                            user['balance']:
                        st.error(
                            "❌ Insufficient "
                            "balance!")
                    else:
                        user['balance'] -= \
                            transfer_amt
                        receiver = \
                            st.session_state\
                            .users[to_user]
                        receiver['balance'] += \
                            transfer_amt

                        st.session_state\
                            .users[username] = \
                            user
                        st.session_state\
                            .users[to_user] = \
                            receiver
                        save_json(
                            USERS_FILE,
                            st.session_state
                            .users)

                        now = str(
                            datetime.now())
                        st.session_state\
                            .transactions\
                            .append({
                            'account': user[
                                'account'],
                            'type':    'Sent',
                            'amount':  transfer_amt,
                            'balance_after':
                                user['balance'],
                            'note':
                                f"{transfer_note} "
                                f"→ {to_user}",
                            'date': now
                        })
                        st.session_state\
                            .transactions\
                            .append({
                            'account': receiver[
                                'account'],
                            'type':    'Received',
                            'amount':  transfer_amt,
                            'balance_after':
                                receiver[
                                    'balance'],
                            'note':
                                f"{transfer_note} "
                                f"← {username}",
                            'date': now
                        })
                        save_json(
                            TXN_FILE,
                            st.session_state
                            .transactions)
                        st.success(
                            f"✅ Sent ₹"
                            f"{transfer_amt:,} "
                            f"to {to_user}!")
                        st.rerun()

    with tab3:
        st.markdown("### 📜 Full Statement")
        if len(txn_df) > 0:
            display = txn_df.sort_values(
                'date', ascending=False)[[
                'date', 'type', 'amount',
                'balance_after', 'note'
            ]].copy()
            display['date'] = display[
                'date'].dt.strftime(
                '%d %b %Y, %H:%M')
            display.columns = [
                'Date', 'Type', 'Amount',
                'Balance After', 'Note']
            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True)
            st.download_button(
                "⬇️ Download Statement",
                display.to_csv(index=False),
                f"statement_{user['account']}.csv",
                "text/csv")
        else:
            st.info("No transactions yet!")

    with tab4:
        st.markdown("### 📊 Spending Insights")
        if len(txn_df) > 0:
            outflow = txn_df[
                txn_df['type'].isin(
                    ['Withdrawal', 'Sent'])]
            if len(outflow) > 0:
                fig2 = px.pie(
                    values=outflow.groupby(
                        'type')['amount']
                        .sum().values,
                    names=outflow.groupby(
                        'type')['amount']
                        .sum().index,
                    title='Outflow Breakdown'
                )
                st.plotly_chart(
                    fig2,
                    use_container_width=True)

                c1, c2 = st.columns(2)
                c1.metric(
                    "Total Spent",
                    f"₹{outflow['amount'].sum():,.0f}")
                c2.metric(
                    "Avg Transaction",
                    f"₹{outflow['amount'].mean():,.0f}")
            else:
                st.info(
                    "No outgoing transactions "
                    "yet!")
        else:
            st.info("No transactions yet!")

st.markdown("---")
st.markdown(
    "Built by **Jyotiraditya** | "
    "Banking Simulator | "
    "Educational simulation, no real funds"
)