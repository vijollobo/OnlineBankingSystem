"""
app.py  –  Bank of Bharat | Streamlit Application  (v3 – formal, light theme)
Run:  streamlit run app.py
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import time

import models as M
from database import fetchone as db_fetchone, fetchall as db_fetchall
from loan_engine import (LoanProfile, calculate_rate, affordability_check,
                         LOAN_PURPOSES, COLLATERAL_TYPES)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Bank of Bharat", page_icon="🏦",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Apply Inter font globally ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ── Page header bar ── */
.bob-header {
    background: linear-gradient(135deg, #1a2744, #0f1729);
    color: #e8edf5; padding: 1rem 1.5rem; border-radius: 10px;
    margin-bottom: 1.4rem; display: flex; align-items: center; gap: 14px;
    box-shadow: 0 3px 16px rgba(0,0,0,.4);
    border-left: 5px solid #c9a84c;
}
.bob-logo {
    background: #c9a84c; color: #0f1729; font-weight: 900;
    font-size: 1.1rem; width: 44px; height: 44px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; letter-spacing: -.5px;
}
.bob-title    { font-size: 1.3rem; font-weight: 700; margin: 0; color: #f0f4ff; }
.bob-subtitle { font-size: .8rem; opacity: .6; margin: 0; color: #c9d3e8; }

/* ── Metric cards ── */
.metric-card {
    background: #1a2744; border-radius: 10px;
    padding: 1.1rem 1.3rem; margin-bottom: .9rem;
    box-shadow: 0 2px 10px rgba(0,0,0,.3);
    border-top: 3px solid #c9a84c;
}
.metric-value { font-size: 1.7rem; font-weight: 800; color: #f0f4ff; line-height: 1.15; }
.metric-label {
    font-size: .7rem; color: #8899bb; text-transform: uppercase;
    letter-spacing: .08em; margin-bottom: 3px;
}
.metric-icon-box {
    float: right; background: rgba(201,168,76,.12); border-radius: 6px;
    width: 38px; height: 38px; display: flex; align-items: center;
    justify-content: center; margin-top: -2px;
}
.metric-icon-box svg { width: 20px; height: 20px; stroke: #c9a84c !important; }

/* ── Account card ── */
.account-card {
    background: #1a2744; border-radius: 10px; padding: 1.1rem 1.3rem;
    box-shadow: 0 2px 10px rgba(0,0,0,.25); margin-bottom: .8rem;
    border-left: 4px solid #c9a84c; transition: box-shadow .2s, transform .15s;
}
.account-card:hover { box-shadow: 0 4px 18px rgba(0,0,0,.4); transform: translateY(-1px); }
.acc-type  { font-size: .68rem; text-transform: uppercase; letter-spacing: .1em; color: #6b7a9a; }
.acc-id    { font-size: .85rem; color: #7fb3f5; font-weight: 600; margin: 2px 0; }
.acc-bal   { font-size: 1.5rem; font-weight: 800; color: #f0f4ff; }
.acc-meta  { font-size: .76rem; color: #8899bb; margin-top: 4px; }

/* ── Rate preview box ── */
.rate-box {
    background: linear-gradient(135deg, #1a2744, #0f1729);
    border: 1px solid #2a3d6b; border-radius: 10px;
    padding: 1.4rem 1.2rem; text-align: center;
}
.rate-big    { font-size: 2.8rem; font-weight: 900; color: #c9a84c; line-height: 1; }
.rate-label  { font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; color: #8899bb; margin-bottom: .3rem; }
.rate-emi    { font-size: 1rem; font-weight: 600; color: #7fb3f5; margin-top: .5rem; }
.rate-totals { font-size: .78rem; color: #6b7a9a; margin-top: .4rem; }

/* ── Section heading ── */
.section-title {
    font-size: .88rem; font-weight: 700; color: #c9a84c;
    border-bottom: 1px solid #2a3d6b; padding-bottom: 6px;
    margin: 1.1rem 0 .8rem; text-transform: uppercase; letter-spacing: .06em;
}

/* ── Info / Warn banners ── */
.info-box {
    background: rgba(59,130,246,.1); border-radius: 7px; padding: .8rem 1rem;
    border-left: 3px solid #3b82f6; font-size: .85rem; margin: .6rem 0;
    color: #93c5fd;
}
.warn-box {
    background: rgba(245,158,11,.1); border-radius: 7px; padding: .8rem 1rem;
    border-left: 3px solid #f59e0b; font-size: .85rem; margin: .6rem 0;
    color: #fcd34d;
}

/* ── Badges ── */
.badge {
    display: inline-block; padding: 2px 9px; border-radius: 4px;
    font-size: .68rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em;
}
.badge-success { background: rgba(34,197,94,.15);  color: #86efac; }
.badge-warning { background: rgba(245,158,11,.15); color: #fcd34d; }
.badge-danger  { background: rgba(239,68,68,.15);  color: #fca5a5; }
.badge-info    { background: rgba(59,130,246,.15);  color: #93c5fd; }
.badge-gold    { background: rgba(201,168,76,.15);  color: #c9a84c; }

/* ── Transaction row ── */
.txn-row {
    background: #1a2744; border-radius: 7px; padding: 9px 13px;
    margin-bottom: 5px; box-shadow: 0 1px 4px rgba(0,0,0,.2);
    display: flex; justify-content: space-between; align-items: center;
    border: 1px solid #2a3d6b;
}
.txn-type { font-weight: 600; font-size: .84rem; color: #e8edf5; }
.txn-date { font-size: .71rem; color: #6b7a9a; margin-top: 1px; }
.txn-cr   { font-weight: 800; font-size: .92rem; color: #86efac; }
.txn-dr   { font-weight: 800; font-size: .92rem; color: #fca5a5; }

/* ── Step indicator ── */
.step {
    display: inline-flex; align-items: center; gap: 8px;
    background: #1a2744; border-radius: 6px; padding: 6px 12px;
    border: 1px solid #2a3d6b; margin-right: 8px; margin-bottom: 8px;
    font-size: .82rem; color: #c9d3e8;
}
.step-num {
    background: #c9a84c; color: #0f1729; width: 22px; height: 22px;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-size: .72rem; font-weight: 800; flex-shrink: 0;
}

/* ── Divider ── */
.divider { height: 1px; background: #2a3d6b; margin: .8rem 0; }

/* ── Login card ── */
.login-wrap {
    background: #1a2744; border-radius: 12px; padding: 2.4rem 2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,.5); max-width: 420px; margin: 0 auto;
    border: 1px solid #2a3d6b;
}
.login-brand-name {
    font-size: 1.55rem; font-weight: 800; color: #f0f4ff;
    text-align: center; margin-bottom: 2px;
}
.login-tagline { text-align: center; color: #6b7a9a; font-size: .8rem; margin-bottom: 1.8rem; }
.login-logo-bank {
    width: 56px; height: 56px; background: #c9a84c; border-radius: 10px;
    margin: 0 auto 1rem; display: flex; align-items: center; justify-content: center;
}

/* ── Sidebar role badge ── */
.role-badge {
    display: inline-block; padding: 2px 10px; border-radius: 4px;
    background: rgba(201,168,76,.2); color: #c9a84c;
    font-size: .7rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .06em; margin-top: 3px;
}

/* ── Streamlit default header chrome ── */
[data-testid="stHeader"] { background: transparent !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
# SVG icons (no emojis) – used for metric cards
ICONS = {
    "customers": '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>',
    "accounts":  '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
    "balance":   '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12M6 8h12M6 13h3c6.667 0 6.667-10 0-10M6 13l8.5 8"/></svg>',
    "loans":     '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "clock":     '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "txn":       '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 014-4h14M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 01-4 4H3"/></svg>',
    "chart":     '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "staff":     '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "inbox":     '<svg viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/></svg>',
}

ACCOUNT_COLORS = {
    "Savings": "#c9a84c", "Current": "#7fb3f5",
    "Fixed Deposit": "#a78bfa", "Recurring Deposit": "#6ee7b7", "Salary Account": "#67e8f9",
}

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def inr(v): return f"₹{float(v):,.2f}"

def badge(text, kind="info"):
    return f'<span class="badge badge-{kind}">{text}</span>'

def status_badge(s):
    m = {"Active":"success","Approved":"success","Disbursed":"gold","Success":"success",
         "Pending":"warning","Inactive":"danger","Rejected":"danger","Frozen":"danger","Failed":"danger"}
    return badge(s, m.get(s, "info"))

def show_header(title, subtitle=""):
    st.markdown(
        f"""<div class="bob-header">
          <div class="bob-logo">BoB</div>
          <div><p class="bob-title">{title}</p>
          <p class="bob-subtitle">{subtitle}</p></div>
        </div>""", unsafe_allow_html=True)

def metric_card(label, value, icon_key="chart", color="#0f2552"):
    icon_svg = ICONS.get(icon_key, ICONS["chart"])
    st.markdown(
        f"""<div class="metric-card" style="border-top-color:{color}">
          <div class="metric-icon-box">{icon_svg}</div>
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
        </div>""", unsafe_allow_html=True)

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

def info_box(text):
    st.markdown(f'<div class="info-box">{text}</div>', unsafe_allow_html=True)

def warn_box(text):
    st.markdown(f'<div class="warn-box">{text}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SESSION
# ══════════════════════════════════════════════════════════════════════════════
for k, v in [("user",None),("page","Dashboard"),("last_activity",time.time()),("sel_purpose","Home")]:
    if k not in st.session_state: st.session_state[k] = v

def logout():
    if st.session_state.user:
        M.log_audit(st.session_state.user["user_id"],
                    st.session_state.user["username"], "LOGOUT", "User logged out")
    for k in ["user","page","last_activity","sel_purpose"]:
        if k in st.session_state: del st.session_state[k]
    st.rerun()

def check_timeout():
    if time.time() - st.session_state.last_activity > 600:
        st.warning("Session expired due to inactivity. Please log in again.")
        logout()
    st.session_state.last_activity = time.time()

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
def login_page():
    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        st.markdown("""
        <div class="login-wrap">
          <div class="login-logo-bank">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <div class="login-brand-name">Bank of Bharat</div>
          <div class="login-tagline">Secure Online Banking Portal</div>
        </div>""", unsafe_allow_html=True)

        t1, t2 = st.tabs(["Sign In", "New Customer Registration"])

        with t1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                else:
                    user, msg = M.authenticate(username, password)
                    if user:
                        st.session_state.user = user
                        st.session_state.page = "Dashboard"
                        st.session_state.last_activity = time.time()
                        M.log_audit(user["user_id"], username, "LOGIN", "Successful login")
                        st.success(f"Welcome, {user['full_name']}. Redirecting...")
                        time.sleep(0.5); st.rerun()
                    else:
                        M.log_audit(None, username, "LOGIN_FAILED", msg)
                        st.error(msg)

        with t2:
            info_box("Self-registration is available for <b>Customers only</b>. "
                     "Staff accounts are created by the Bank Administrator.")
            with st.form("register_form"):
                c1, c2 = st.columns(2)
                with c1:
                    r_user   = st.text_input("Username *")
                    r_pwd    = st.text_input("Password *", type="password")
                    r_cpwd   = st.text_input("Confirm Password *", type="password")
                    r_name   = st.text_input("Full Name *")
                with c2:
                    r_email  = st.text_input("Email Address")
                    r_phone  = st.text_input("Phone Number")
                    r_dob    = st.date_input("Date of Birth *", value=date(1995,1,1),
                                             min_value=date(1930,1,1), max_value=date.today())
                    r_gender = st.selectbox("Gender *", ["Male","Female","Other"])
                r_addr = st.text_input("Residential Address")
                reg = st.form_submit_button("Register", use_container_width=True)
            if reg:
                errs = []
                if not r_user.strip():       errs.append("Username is required.")
                if not r_pwd:                errs.append("Password is required.")
                if r_pwd != r_cpwd:          errs.append("Passwords do not match.")
                if not r_name.strip():       errs.append("Full Name is required.")
                if len(r_pwd) < 6:           errs.append("Password must be at least 6 characters.")
                for e in errs: st.error(e)
                if not errs:
                    ok, msg = M.create_user(r_user.strip(), r_pwd, "customer",
                        r_name.strip(), r_email, r_phone, r_addr, r_dob, r_gender,
                        self_registered=True)
                    if ok: st.success(f"Registration successful. You may now sign in as: {r_user}")
                    else:  st.error(msg)

        st.markdown(
            "<div style='text-align:center;font-size:.73rem;color:#9ca3af;margin-top:1.2rem'>"
            "Bank of Bharat &copy; 2026 &nbsp;|&nbsp; Demonstration Project</div>",
            unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
ROLE_PAGES = {
    "customer": ["Dashboard","My Accounts","Open Account",
                 "Fund Transfer","Transaction History",
                 "Apply for Loan","Loan Status"],
    "cashier":  ["Dashboard","Process Transaction",
                 "Disburse Salary","Send Report","All Transactions"],
    "admin":    ["Dashboard","Manage Users","Admin Fund Transfer",
                 "Interest Rate Settings","Analytics","Audit Log"],
    "manager":  ["Dashboard","Loan Approval","Promote Employee",
                 "Interest Analytics","Manager Inbox","Audit Log"],
}

def sidebar_nav():
    user  = st.session_state.user
    role  = user["role"]
    pages = ROLE_PAGES.get(role, [])

    with st.sidebar:
        # Bank branding
        st.markdown("""
        <div style="padding:1.2rem 0 .8rem;text-align:center;border-bottom:1px solid rgba(255,255,255,.12)">
          <div style="display:flex;align-items:center;justify-content:center;gap:10px">
            <div style="background:#c9a84c;border-radius:6px;width:34px;height:34px;display:flex;
              align-items:center;justify-content:center;flex-shrink:0">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#c9a84c" stroke-width="2.5">
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
                <polyline points="9 22 9 12 15 12 15 22"/>
              </svg>
            </div>
            <div>
              <div style="font-size:1rem;font-weight:800;letter-spacing:.02em;color:#f0f4ff">Bank of Bharat</div>
              <div style="font-size:.65rem;opacity:.5;color:#c9d3e8">Online Banking Portal</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # User info
        role_label = role.title()
        st.markdown(f"""
        <div style="padding:.9rem 0 .6rem">
          <div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.08em;
            color:rgba(255,255,255,.45);margin-bottom:5px">Logged In As</div>
          <div style="font-size:.92rem;font-weight:700;color:#e8edf5">{user['full_name']}</div>
          <div style="font-size:.68rem;color:rgba(255,255,255,.5)">@{user['username']}</div>
          <span class="role-badge">{role_label}</span>
        </div>""", unsafe_allow_html=True)

        st.markdown('<hr>', unsafe_allow_html=True)

        st.markdown('<div style="font-size:.62rem;text-transform:uppercase;letter-spacing:.1em;'
                    'color:rgba(255,255,255,.35);margin-bottom:6px;padding-left:2px">Navigation</div>',
                    unsafe_allow_html=True)
        selected = st.radio("nav", pages, label_visibility="collapsed")
        st.session_state.page = selected

        st.markdown('<hr>', unsafe_allow_html=True)

        if role == "manager":
            unread = M.get_unread_count()
            if unread > 0:
                st.markdown(
                    f'<div style="background:rgba(201,168,76,.18);border:1px solid rgba(201,168,76,.4);'
                    f'border-radius:6px;padding:7px 12px;font-size:.8rem;color:#f0d080;margin-bottom:.5rem">'
                    f'{unread} unread message{"s" if unread>1 else ""} in inbox</div>',
                    unsafe_allow_html=True)

        if st.button("Sign Out", use_container_width=True):
            logout()

        st.markdown(
            '<div style="font-size:.62rem;color:rgba(255,255,255,.25);text-align:center;margin-top:.8rem">'
            'Bank of Bharat v2.0</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def customer_dashboard():
    user = st.session_state.user
    show_header("Customer Dashboard", f"Welcome, {user['full_name']}")

    accounts  = M.get_customer_accounts(user["user_id"])
    loans     = M.get_loans_by_user(user["user_id"])
    total_bal = sum(float(a["balance"]) for a in accounts)
    active    = [a for a in accounts if a["status"]=="Active"]

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Balance", inr(total_bal), "balance", "#0f2552")
    with c2: metric_card("Active Accounts", str(len(active)), "accounts", "#1d4ed8")
    with c3: metric_card("Loan Applications", str(len(loans)), "loans", "#7c3aed")
    with c4: metric_card("Pending Loans", str(sum(1 for l in loans if l["status"]=="Pending")), "clock", "#b45309")

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        section("Your Accounts")
        if not accounts:
            info_box("No accounts found. Open an account to get started.")
        for acc in accounts[:4]:
            proj = float(acc["balance"]) * float(acc["interest_rate"]) / 100
            col  = ACCOUNT_COLORS.get(acc["account_type"], "#c9a84c")
            st.markdown(f"""
            <div class="account-card" style="border-left-color:{col}">
              <div class="acc-type">{acc['account_type']} &nbsp;{status_badge(acc['status'])}</div>
              <div class="acc-id">{acc['account_id']}</div>
              <div class="acc-bal">{inr(acc['balance'])}</div>
              <div class="acc-meta">
                Rate: {acc['interest_rate']}% p.a. &nbsp;&middot;&nbsp;
                Est. annual interest: {inr(proj)} &nbsp;&middot;&nbsp;
                Opened: {acc['opening_date']}
              </div>
            </div>""", unsafe_allow_html=True)

    with right:
        section("Recent Transactions")
        all_txns = []
        own_ids  = {a["account_id"] for a in accounts}
        for acc in active[:3]:
            all_txns.extend(M.get_account_transactions(acc["account_id"], 5))
        all_txns.sort(key=lambda x: x["created_at"], reverse=True)
        if not all_txns:
            info_box("No recent transactions.")
        for t in all_txns[:7]:
            is_cr  = t.get("to_account") in own_ids
            cr_cls = "txn-cr" if is_cr else "txn-dr"
            sign   = "+" if is_cr else "−"
            st.markdown(f"""
            <div class="txn-row">
              <div>
                <div class="txn-type">{t['transaction_type']}</div>
                <div class="txn-date">{str(t['created_at'])[:16]}</div>
              </div>
              <div class="{cr_cls}">{sign}{inr(t['amount'])}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER — MY ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════
def customer_accounts():
    user = st.session_state.user
    show_header("My Accounts", "Detailed view of all bank accounts")

    accounts = M.get_customer_accounts(user["user_id"])
    if not accounts:
        info_box("No accounts found. Open an account to get started."); return

    total     = sum(float(a["balance"]) for a in accounts)
    ann_int   = sum(float(a["balance"]) * float(a["interest_rate"]) / 100 for a in accounts)

    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Portfolio Balance", inr(total), "balance")
    with c2: metric_card("Number of Accounts", str(len(accounts)), "accounts")
    with c3: metric_card("Estimated Annual Interest", inr(ann_int), "chart")

    st.markdown("<br>", unsafe_allow_html=True)
    for acc in accounts:
        annual = float(acc["balance"]) * float(acc["interest_rate"]) / 100
        col    = ACCOUNT_COLORS.get(acc["account_type"], "#c9a84c")
        with st.expander(f"{acc['account_type']}  |  {acc['account_id']}  |  {inr(acc['balance'])}  |  {acc['status']}", expanded=False):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Account ID:** `{acc['account_id']}`  \n**Type:** {acc['account_type']}  \n**Status:** {acc['status']}")
            c2.markdown(f"**Balance:** {inr(acc['balance'])}  \n**Interest Rate:** {acc['interest_rate']}% p.a.  \n**Opened:** {acc['opening_date']}")
            c3.markdown(f"**Annual Interest (est.):** {inr(annual)}")
            if acc.get("maturity_date"):
                st.info(f"Maturity Date: {acc['maturity_date']}  |  Tenure: {acc.get('tenure_months','—')} months")
            section("Last 10 Transactions")
            txns = M.get_account_transactions(acc["account_id"], 10)
            if txns:
                own_ids = {a["account_id"] for a in accounts}
                rows = []
                for t in txns:
                    is_cr = t.get("to_account") in own_ids
                    rows.append({"Reference ID": t["transaction_id"], "Type": t["transaction_type"],
                        "Dr/Cr": "Credit" if is_cr else "Debit",
                        "Amount (INR)": f"{float(t['amount']):,.2f}",
                        "From Account": t.get("from_account") or "—",
                        "To Account":   t.get("to_account")   or "—",
                        "Narration":   (t.get("narration") or "")[:45],
                        "Status": t["status"], "Date & Time": str(t["created_at"])[:19]})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            else:
                st.caption("No transactions on record.")


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER — OPEN ACCOUNT
# ══════════════════════════════════════════════════════════════════════════════
def open_account_page():
    user = st.session_state.user
    show_header("Open New Account", "Select an account type and complete the application")

    ACC_INFO = {
        "Savings":           ("#0f2552", "4.00% p.a.", "Min. ₹500",       "Everyday savings with interest"),
        "Current":           ("#1d4ed8", "0% p.a.",    "Min. ₹1,000",     "High-frequency business transactions"),
        "Fixed Deposit":     ("#7c3aed", "6.50% p.a.", "Min. ₹5,000",     "Fixed tenure, guaranteed returns"),
        "Recurring Deposit": ("#c9a84c", "5.50% p.a.", "Min. ₹500/month", "Monthly installment savings plan"),
        "Salary Account":    ("#0369a1", "3.50% p.a.", "No minimum",      "Linked to employer payroll"),
    }

    section("Account Types Available")
    cols = st.columns(5)
    for i, (atype, (col, rate, minbal, desc)) in enumerate(ACC_INFO.items()):
        with cols[i]:
            st.markdown(f"""
            <div style="background:white;border-radius:8px;padding:1rem .8rem;text-align:center;
              border-top:3px solid {col};box-shadow:0 1px 5px rgba(0,0,0,.07);min-height:130px">
              <div style="font-weight:700;color:{col};font-size:.9rem;margin-bottom:4px">{atype}</div>
              <div style="font-size:.82rem;color:#111827;font-weight:600">{rate}</div>
              <div style="font-size:.72rem;color:#6b7280;margin-top:2px">{minbal}</div>
              <div style="font-size:.7rem;color:#9ca3af;margin-top:4px">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    section("Account Application Form")

    with st.form("open_acc_form"):
        c1, c2 = st.columns(2)
        with c1:
            account_type    = st.selectbox("Account Type *", list(ACC_INFO.keys()))
            initial_deposit = st.number_input("Initial Deposit (INR) *", min_value=0.0, step=500.0)
        with c2:
            tenure_months = None; monthly_installment = None
            if account_type in ("Fixed Deposit", "Recurring Deposit"):
                tenure_months = st.number_input("Tenure (Months) *", min_value=1, max_value=120, value=12)
                if account_type == "Recurring Deposit":
                    monthly_installment = st.number_input("Monthly Installment (INR) *", min_value=500.0, step=500.0)
            else:
                st.markdown(f"""<div class="info-box">
                  <strong>{account_type}</strong> — No fixed tenure required.<br>
                  Minimum deposit: {ACC_INFO[account_type][2]}
                </div>""", unsafe_allow_html=True)
        submitted = st.form_submit_button("Open Account", use_container_width=True)

    if submitted:
        ok, msg, acc_id = M.open_account(user["user_id"], account_type, initial_deposit,
                                          tenure_months, monthly_installment)
        if ok:
            st.success(msg)
            M.log_audit(user["user_id"], user["username"], "OPEN_ACCOUNT",
                        f"Opened {account_type} account {acc_id}")
        else:
            st.error(msg)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER — FUND TRANSFER
# ══════════════════════════════════════════════════════════════════════════════
def fund_transfer_page():
    user     = st.session_state.user
    show_header("Fund Transfer", "Transfer funds to any account securely")

    accounts = M.get_customer_accounts(user["user_id"])
    active   = [a for a in accounts if a["status"] == "Active"]
    if not active:
        info_box("You need at least one active account to initiate a transfer."); return

    acc_opts = {f"{a['account_id']}  ({a['account_type']})  —  Balance: {inr(a['balance'])}": a["account_id"]
                for a in active}

    st.markdown("""
    <div style="display:flex;flex-wrap:wrap;margin-bottom:1.1rem">
      <div class="step"><div class="step-num">1</div> Select source account</div>
      <div class="step"><div class="step-num">2</div> Enter destination account number</div>
      <div class="step"><div class="step-num">3</div> Enter amount and confirm</div>
    </div>""", unsafe_allow_html=True)

    with st.form("transfer_form"):
        c1, c2 = st.columns(2)
        with c1:
            from_label = st.selectbox("From Account *", list(acc_opts.keys()))
            from_acc   = acc_opts[from_label]
            amount     = st.number_input("Transfer Amount (INR) *", min_value=1.0, step=100.0)
        with c2:
            to_acc    = st.text_input("Destination Account Number *", placeholder="BOB…")
            narration = st.text_input("Narration / Purpose", placeholder="Optional description")
        submitted = st.form_submit_button("Initiate Transfer", use_container_width=True)

    if submitted:
        if not to_acc.strip():
            st.error("Destination account number is required.")
        else:
            dst = M.get_account_with_owner(to_acc.strip())
            if not dst:
                st.error("Destination account not found. Please verify the account number.")
            elif from_acc == to_acc.strip():
                st.error("Source and destination accounts cannot be the same.")
            else:
                ok, msg = M.transfer(from_acc, to_acc.strip(), amount,
                                     narration or "Fund Transfer",
                                     processed_by=user["user_id"])
                if ok:
                    st.success(msg)
                    M.log_audit(user["user_id"], user["username"], "FUND_TRANSFER",
                                f"{inr(amount)} to {to_acc}")
                    st.info(f"Credited to: {dst['full_name']}  |  Account: {dst['account_id']}")
                else:
                    st.error(msg)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER — TRANSACTION HISTORY
# ══════════════════════════════════════════════════════════════════════════════
def transaction_history_page():
    user     = st.session_state.user
    show_header("Transaction History", "Complete record of financial activity")

    accounts = M.get_customer_accounts(user["user_id"])
    if not accounts: info_box("No accounts found."); return

    acc_opts = {"All Accounts": None}
    acc_opts.update({f"{a['account_id']} ({a['account_type']})": a["account_id"] for a in accounts})

    c1, c2, c3 = st.columns(3)
    with c1: sel      = st.selectbox("Account", list(acc_opts.keys()))
    with c2: txn_filt = st.selectbox("Type", ["All","Deposit","Withdrawal","Transfer","Loan Disbursement"])
    with c3: limit    = st.selectbox("Records", [25, 50, 100], index=1)

    all_txns = []
    if acc_opts[sel] is None:
        for acc in accounts:
            all_txns.extend(M.get_account_transactions(acc["account_id"], limit))
    else:
        all_txns = M.get_account_transactions(acc_opts[sel], limit)
    all_txns.sort(key=lambda x: x["created_at"], reverse=True)
    if txn_filt != "All":
        all_txns = [t for t in all_txns if t["transaction_type"] == txn_filt]

    if not all_txns: info_box("No transactions found for the selected filter."); return

    own_ids = {a["account_id"] for a in accounts}
    rows = []
    for t in all_txns:
        is_cr = t.get("to_account") in own_ids
        rows.append({
            "Reference ID":   t["transaction_id"],
            "Type":           t["transaction_type"],
            "Dr / Cr":        "Credit" if is_cr else "Debit",
            "Amount (INR)":   f"{float(t['amount']):,.2f}",
            "From Account":   t.get("from_account") or "—",
            "To Account":     t.get("to_account")   or "—",
            "Narration":     (t.get("narration") or "")[:50],
            "Status":         t["status"],
            "Date & Time":    str(t["created_at"])[:19],
        })
    section(f"{len(rows)} Transaction(s)")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=440)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER — APPLY FOR LOAN
# ══════════════════════════════════════════════════════════════════════════════
def loan_application_page():
    user     = st.session_state.user
    show_header("Loan Application", "Personalised interest rate calculated in real time")

    accounts = M.get_customer_accounts(user["user_id"])
    active   = [a for a in accounts if a["status"] == "Active"]
    if not active:
        st.warning("An active account is required to apply for a loan."); return

    acc_opts = {f"{a['account_id']} ({a['account_type']})": a["account_id"] for a in active}

    # Loan type selector
    section("Step 1 — Select Loan Type")
    p_keys = list(LOAN_PURPOSES.keys())
    sel_purpose = st.session_state.get("sel_purpose", "Home")

    PURPOSE_DESC = {
        "Home":        ("Home Loan",     "Purchase or construct a residence"),
        "Education":   ("Education Loan","Finance higher education or professional courses"),
        "Personal":    ("Personal Loan", "Medical, wedding, or general personal expenses"),
        "Vehicle/Car": ("Vehicle Loan",  "Purchase a new or used vehicle"),
        "Business":    ("Business Loan", "Fund business operations or expansion"),
        "Gold Loan":   ("Gold Loan",     "Loan against gold jewellery or coins"),
        "Vacation":    ("Vacation Loan", "Travel and leisure financing"),
    }

    p_cols = st.columns(7)
    for i, (p, (_, _, adj)) in enumerate(LOAN_PURPOSES.items()):
        with p_cols[i]:
            adj_col  = "#166534" if adj < 0 else ("#854d0e" if adj == 0 else "#991b1b")
            adj_lbl  = f"{adj:+.2f}%"
            selected = (sel_purpose == p)
            border   = "border:2px solid #c9a84c;background:#fffbf0;" if selected else "border:2px solid #2a3d6b;"
            st.markdown(f"""
            <div style="background:white;border-radius:7px;padding:.7rem .5rem;text-align:center;
              {border} box-shadow:0 1px 4px rgba(0,0,0,.06)">
              <div style="font-size:.8rem;font-weight:700;color:#0f2552">{PURPOSE_DESC[p][0]}</div>
              <div style="font-size:.68rem;color:{adj_col};font-weight:700;margin-top:2px">{adj_lbl}</div>
            </div>""", unsafe_allow_html=True)
            if st.button(p, key=f"pu_{p}", use_container_width=True):
                st.session_state["sel_purpose"] = p
                sel_purpose = p
                st.rerun()

    sel_purpose = st.session_state.get("sel_purpose", "Home")
    st.markdown(f"""<div class="info-box">
      <strong>{PURPOSE_DESC[sel_purpose][0]}</strong> — {PURPOSE_DESC[sel_purpose][1]}<br>
      Rate adjustment for this loan type:
      <strong style="color:{'#166534' if LOAN_PURPOSES[sel_purpose][2]<0 else '#991b1b'}">{LOAN_PURPOSES[sel_purpose][2]:+.2f}%</strong>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    form_col, preview_col = st.columns([3, 2])

    with form_col:
        section("Step 2 — Applicant and Loan Details")
        with st.form("loan_form"):
            st.markdown("**Personal Information**")
            c1, c2 = st.columns(2)
            with c1:
                full_name  = st.text_input("Full Name *", value=user["full_name"])
                dob        = st.date_input("Date of Birth *", value=date(1990,1,1),
                                           min_value=date(1930,1,1), max_value=date.today())
            with c2:
                gender     = st.selectbox("Gender *", ["Male","Female","Other"])
                emp_status = st.selectbox("Employment Status *", ["Employed","Self-Employed","Unemployed"])

            st.markdown("**Financial Information**")
            c1, c2 = st.columns(2)
            with c1:
                monthly_income = st.number_input("Monthly Income (INR) *", min_value=10000.0, step=1000.0, value=50000.0)
                loan_amount    = st.number_input("Loan Amount Required (INR) *", min_value=10000.0, step=5000.0, value=500000.0)
                tenure_years   = st.number_input("Repayment Tenure (Years) *", min_value=1, max_value=30, value=5)
            with c2:
                credit_score   = st.number_input("CIBIL Credit Score *", min_value=300, max_value=900, value=700,
                                                  help="300 = Poor  |  750+ = Excellent. Score ≥ 750 gives −1.50% benefit.")
                existing_loans = st.number_input("Number of Existing Active Loans *", min_value=0, max_value=10, value=0)

            st.markdown("**Collateral Details**")
            c_labels = {k: f"{k} — {v[1]}  (Rate: {v[2]:+.2f}%)" for k, v in COLLATERAL_TYPES.items()}
            collateral_type = st.selectbox("Collateral Type *", list(c_labels.keys()),
                                            format_func=lambda k: c_labels[k])

            st.markdown("**Compliance and Disbursement**")
            c1, c2 = st.columns(2)
            with c1:
                kyc_ref = st.text_input("KYC Reference Number *", placeholder="10–20 alphanumeric characters")
            with c2:
                disb_label = st.selectbox("Disbursement Account *", list(acc_opts.keys()))
                disb_acc   = acc_opts[disb_label]

            submitted = st.form_submit_button("Submit Loan Application", use_container_width=True)

    with preview_col:
        section("Real-Time Rate Preview")
        try:
            profile = LoanProfile(
                date_of_birth=dob, gender=gender, employment_status=emp_status,
                monthly_income=monthly_income, loan_amount=loan_amount,
                tenure_years=tenure_years, credit_score=credit_score,
                collateral_type=collateral_type,
                existing_loans_count=existing_loans, loan_purpose=sel_purpose)
            bd = calculate_rate(profile)
            ok_aff, aff_msg = affordability_check(monthly_income, bd.emi)

            st.markdown(f"""
            <div class="rate-box">
              <div class="rate-label">Personalised Interest Rate</div>
              <div class="rate-big">{bd.final_rate:.2f}%</div>
              <div style="font-size:.75rem;opacity:.6;margin-top:2px">per annum</div>
              <div class="rate-emi">Monthly EMI:  {inr(bd.emi)}</div>
              <div class="rate-totals">
                Total Interest Payable: {inr(bd.total_interest)}<br>
                Total Amount Payable: {inr(bd.total_payable)}
              </div>
            </div>""", unsafe_allow_html=True)

            if ok_aff: st.success(aff_msg)
            else:      st.error(aff_msg)

            st.markdown("**Rate Breakdown**")
            bd_rows = [
                ("Base Rate",                   f"+{bd.base_rate:.2f}%"),
                (f"Age ({bd.age} years)",        f"{bd.age_adj:+.2f}%"),
                ("Gender",                       f"{bd.gender_adj:+.2f}%"),
                ("Loan Tenure",                  f"{bd.tenure_adj:+.2f}%"),
                ("Employment Status",            f"{bd.employment_adj:+.2f}%"),
                (f"CIBIL Score ({credit_score})",f"{bd.credit_adj:+.2f}%"),
                (f"Collateral: {collateral_type}",f"{bd.collateral_adj:+.2f}%"),
                (f"Existing Loans ({existing_loans})", f"{bd.existing_loans_adj:+.2f}%"),
                (f"LTI Ratio ({bd.lti_ratio:.1f}x)", f"{bd.lti_adj:+.2f}%"),
                (f"Loan Purpose",                f"{bd.purpose_adj:+.2f}%"),
                ("Final Rate (capped 6–22%)",    f"{bd.final_rate:.2f}%"),
            ]
            st.dataframe(pd.DataFrame(bd_rows, columns=["Factor","Adjustment"]),
                         use_container_width=True, hide_index=True, height=390)
        except Exception as ex:
            info_box(f"Complete the form to see your personalised rate.")

    if submitted:
        errs = []
        if not full_name.strip(): errs.append("Full Name is required.")
        if not kyc_ref.strip() or len(kyc_ref) < 10: errs.append("KYC Reference must be 10–20 characters.")
        for e in errs: st.error(e)
        if not errs:
            profile = LoanProfile(date_of_birth=dob, gender=gender, employment_status=emp_status,
                monthly_income=monthly_income, loan_amount=loan_amount, tenure_years=tenure_years,
                credit_score=credit_score, collateral_type=collateral_type,
                existing_loans_count=existing_loans, loan_purpose=sel_purpose)
            bd = calculate_rate(profile)
            ok_aff, aff_msg = affordability_check(monthly_income, bd.emi)
            if not ok_aff:
                st.error(f"Application rejected by affordability check: {aff_msg}")
            else:
                ok, msg = M.submit_loan(user["user_id"], disb_acc, full_name, dob, gender,
                    emp_status, monthly_income, loan_amount, sel_purpose, tenure_years,
                    credit_score, collateral_type, existing_loans, kyc_ref, bd.final_rate, bd.emi)
                if ok:
                    st.success(msg)
                    M.log_audit(user["user_id"], user["username"], "LOAN_APPLIED",
                                f"{inr(loan_amount)} | Rate: {bd.final_rate}% | {sel_purpose}")
                else:
                    st.error(msg)


# ══════════════════════════════════════════════════════════════════════════════
# CUSTOMER — LOAN STATUS
# ══════════════════════════════════════════════════════════════════════════════
def loan_status_page():
    user  = st.session_state.user
    show_header("Loan Applications", "Status of all loan requests")

    loans = M.get_loans_by_user(user["user_id"])
    if not loans:
        info_box("No loan applications on record. Apply for a loan to get started."); return

    STATUS_COLORS = {"Pending":"#b45309","Approved":"#15803d","Disbursed":"#c9a84c","Rejected":"#b91c1c"}
    for loan in loans:
        col = STATUS_COLORS.get(loan["status"], "#0f2552")
        with st.expander(
            f"{loan['loan_id']}  |  {inr(loan['loan_amount'])}  |  {loan['loan_purpose']}  |  {loan['status']}",
            expanded=loan["status"] == "Pending"):
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"**Loan ID:** `{loan['loan_id']}`  \n**Purpose:** {loan['loan_purpose']}  \n**Status:** {loan['status']}")
            c2.markdown(f"**Loan Amount:** {inr(loan['loan_amount'])}  \n**Tenure:** {loan['tenure_years']} year(s)  \n**Interest Rate:** {loan['computed_interest_rate']}% p.a.")
            c3.markdown(f"**Monthly EMI:** {inr(loan['emi_amount'])}  \n**Applied On:** {str(loan['applied_at'])[:10]}  \n**Decision Date:** {str(loan['decided_at'])[:10] if loan['decided_at'] else 'Awaited'}")
            c4, c5 = st.columns(2)
            c4.markdown(f"**Collateral:** {loan['collateral_type']}  \n**CIBIL Score:** {loan['credit_score']}  \n**Gender:** {loan['gender']}")
            c5.markdown(f"**Employment:** {loan['employment_status']}  \n**Monthly Income:** {inr(loan['monthly_income'])}  \n**KYC Ref:** `{loan['kyc_reference']}`")
            if loan.get("manager_remarks"):
                info_box(f"<strong>Manager Remarks:</strong> {loan['manager_remarks']}")


# ══════════════════════════════════════════════════════════════════════════════
# CASHIER — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def cashier_dashboard():
    user = st.session_state.user
    show_header("Cashier Dashboard", f"Operations Console — {user['full_name']}")
    s = M.get_bank_summary()
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Customers",   str(s["total_customers"]),   "customers", "#0f2552")
    with c2: metric_card("Active Accounts",   str(s["total_accounts"]),    "accounts",  "#1d4ed8")
    with c3: metric_card("Transactions Today",str(s["transactions_today"]),"txn",       "#15803d")
    with c4: metric_card("Pending Loans",     str(s["pending_loans"]),     "clock",     "#b45309")

    st.markdown("<br>", unsafe_allow_html=True)
    section("Recent Transactions")
    txns = M.get_recent_transactions_for_cashier(25)
    if txns:
        rows = [{"Reference": t["transaction_id"], "Type": t["transaction_type"],
            "Amount (INR)": f"{float(t['amount']):,.2f}",
            "From": t.get("from_account") or "—", "To": t.get("to_account") or "—",
            "Narration": (t.get("narration") or "")[:45],
            "Status": t["status"], "Date & Time": str(t["created_at"])[:19]} for t in txns]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=360)
    else:
        info_box("No transactions recorded yet.")


# ══════════════════════════════════════════════════════════════════════════════
# CASHIER — PROCESS TRANSACTION
# ══════════════════════════════════════════════════════════════════════════════
def process_transaction_page():
    user = st.session_state.user
    show_header("Process Transaction", "Deposit or withdraw on behalf of a customer")
    section("Customer Account Lookup")
    search = st.text_input("Enter Account ID", placeholder="BOB…")

    if search:
        acc = M.get_account_with_owner(search.strip())
        if acc:
            col = ACCOUNT_COLORS.get(acc["account_type"], "#c9a84c")
            st.markdown(f"""
            <div class="account-card" style="border-left-color:{col}">
              <div class="acc-type">{acc['account_type']} &nbsp;{status_badge(acc['status'])}</div>
              <div class="acc-id">{acc['account_id']}</div>
              <div class="acc-bal">{inr(acc['balance'])}</div>
              <div class="acc-meta">Account Holder: <strong>{acc['full_name']}</strong> (@{acc['username']})</div>
            </div>""", unsafe_allow_html=True)

            if acc["status"] == "Active":
                section("Transaction Details")
                with st.form("cashier_txn_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        txn_type = st.selectbox("Transaction Type", ["Deposit","Withdrawal"])
                        amount   = st.number_input("Amount (INR) *", min_value=1.0, step=100.0)
                    with c2:
                        narration = st.text_input("Narration", placeholder="Enter remarks")
                    submitted = st.form_submit_button("Process Transaction", use_container_width=True)
                if submitted:
                    fn = M.deposit if txn_type == "Deposit" else M.withdraw
                    ok, msg = fn(acc["account_id"], amount, narration or f"Cash {txn_type}", user["user_id"])
                    if ok:
                        st.success(msg)
                        M.log_audit(user["user_id"], user["username"], f"CASHIER_{txn_type.upper()}",
                                    f"{inr(amount)} on {acc['account_id']}")
                    else:
                        st.error(msg)
            else:
                st.warning(f"Account is {acc['status']}. Transactions cannot be processed.")
        elif search:
            st.error("Account not found. Please verify the account number.")


# ══════════════════════════════════════════════════════════════════════════════
# CASHIER — DISBURSE SALARY
# ══════════════════════════════════════════════════════════════════════════════
def disburse_salary_page():
    user      = st.session_state.user
    show_header("Salary Disbursement", "Process monthly salary for bank staff")

    employees = M.get_all_employees()
    if not employees: info_box("No employees found."); return

    month_year = st.text_input("Disbursement Period (YYYY-MM)", value=datetime.now().strftime("%Y-%m"))
    if not month_year: return

    paid_emps = set()
    for emp in employees:
        ex = db_fetchone("SELECT disbursement_id FROM salary_disbursements WHERE employee_user_id=%s AND month_year=%s",
                         (emp["user_id"], month_year))
        if ex: paid_emps.add(emp["user_id"])

    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Total Staff",    str(len(employees)),                   "staff")
    with c2: metric_card("Paid This Month",str(len(paid_emps)),                   "accounts", "#15803d")
    with c3: metric_card("Pending Payment",str(len(employees) - len(paid_emps)), "clock",    "#b45309")

    total_payroll = sum(float(e.get("salary", 0)) for e in employees)
    st.markdown(f"**Total Monthly Payroll: {inr(total_payroll)}**")
    divider()

    for emp in employees:
        is_paid  = emp["user_id"] in paid_emps
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
        with c1: st.markdown(f"**{emp['full_name']}**  \n{emp.get('designation','—')}  |  {emp.get('department','—')}")
        with c2: st.markdown(f"{inr(emp.get('salary', 0))} / month")
        with c3: st.markdown(emp["role"].title())
        with c4: st.markdown("Paid" if is_paid else "Pending")
        with c5:
            if not is_paid:
                if st.button("Disburse", key=f"sal_{emp['user_id']}_{month_year}"):
                    ok, msg = M.disburse_salary(emp["user_id"], user["user_id"],
                                                float(emp.get("salary", 0)), month_year)
                    if ok:
                        st.success(msg)
                        M.log_audit(user["user_id"], user["username"], "SALARY_DISBURSED",
                                    f"{emp['full_name']} | {month_year} | {inr(emp.get('salary',0))}")
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.markdown("—")
        divider()


# ══════════════════════════════════════════════════════════════════════════════
# CASHIER — SEND REPORT
# ══════════════════════════════════════════════════════════════════════════════
def send_report_page():
    user = st.session_state.user
    show_header("Send Report to Manager", "Compose and submit operational reports")
    section("Compose Message")
    with st.form("msg_form"):
        subject  = st.text_input("Subject *", placeholder="e.g. Daily Cash Summary — 23 Mar 2026")
        body     = st.text_area("Message Body *", height=200,
                                placeholder="Write your report, cash summary, or operational note here.")
        submitted = st.form_submit_button("Send to Manager", use_container_width=True)
    if submitted:
        if not subject.strip() or not body.strip():
            st.error("Both subject and message body are required.")
        else:
            ok, msg = M.send_message(user["user_id"], subject, body)
            if ok:
                st.success(msg)
                M.log_audit(user["user_id"], user["username"], "MSG_SENT", f"Subject: {subject}")
            else:
                st.error(msg)

    section("Sent Messages")
    sent = db_fetchall("SELECT * FROM messages WHERE sender_id=%s ORDER BY sent_at DESC LIMIT 20",
                       (user["user_id"],))
    if sent:
        for m in sent:
            status_label = "Read" if m["is_read"] else "Unread"
            with st.expander(f"{m['subject']}  —  {str(m['sent_at'])[:16]}  |  {status_label}"):
                st.markdown(m["body"])
    else:
        info_box("No messages sent yet.")


# ══════════════════════════════════════════════════════════════════════════════
# CASHIER — ALL TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════
def all_transactions_page():
    user = st.session_state.user
    show_header("All Transactions", "System-wide transaction history")
    c1, c2 = st.columns(2)
    with c1: limit    = st.selectbox("Records", [50, 100, 200, 500], index=1)
    with c2: txn_filt = st.selectbox("Filter Type", ["All","Deposit","Withdrawal","Transfer",
                                                       "Salary","Loan Disbursement","Admin Transfer"])
    txns = M.get_all_transactions(limit)
    if txn_filt != "All": txns = [t for t in txns if t["transaction_type"] == txn_filt]
    if not txns: info_box("No transactions found."); return
    rows = [{"Reference": t["transaction_id"], "Type": t["transaction_type"],
        "Amount (INR)": f"{float(t['amount']):,.2f}",
        "From":  t.get("from_account") or "—", "To": t.get("to_account") or "—",
        "Narration": (t.get("narration") or "")[:45], "Status": t["status"],
        "Date & Time": str(t["created_at"])[:19]} for t in txns]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, height=500)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def admin_dashboard():
    user = st.session_state.user
    show_header("Admin Dashboard", "Bank Administration Control Panel")
    s = M.get_bank_summary()
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Total Customers",  str(s["total_customers"]),           "customers", "#0f2552")
    with c2: metric_card("Active Accounts",  str(s["total_accounts"]),            "accounts",  "#1d4ed8")
    with c3: metric_card("Total Deposits",   inr(s["total_balance"]),             "balance",   "#15803d")
    with c4: metric_card("Pending Loans",    str(s["pending_loans"]),             "clock",     "#b45309")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        section("Account Type Distribution")
        dist = M.get_account_type_distribution()
        if dist:
            df  = pd.DataFrame(dist)
            fig = px.pie(df, values="count", names="account_type",
                color_discrete_sequence=["#c9a84c","#7fb3f5","#a78bfa","#6ee7b7","#67e8f9"], hole=.38)
            fig.update_layout(height=280, margin=dict(t=10,b=10,l=0,r=0),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            fig.update_traces(textfont_color="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            info_box("No accounts opened yet.")
    with c2:
        section("Current Interest Rates")
        rates = M.get_interest_rates()
        for r in rates:
            ca, cb = st.columns([3, 1])
            ca.markdown(f"**{r['account_type']}**")
            cb.markdown(f"**{r['rate']}% p.a.**")
            divider()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — MANAGE USERS
# ══════════════════════════════════════════════════════════════════════════════
def manage_users_page():
    user = st.session_state.user
    show_header("Manage Users", "Create, activate and deactivate user accounts")

    tab1, tab2 = st.tabs(["User Directory", "Create New User"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1: role_f   = st.selectbox("Filter by Role", ["All","customer","cashier","admin","manager"])
        with c2: status_f = st.selectbox("Filter by Status", ["All","Active","Inactive"])
        with c3: search_f = st.text_input("Search name or username")

        users = M.get_all_users(role_f if role_f != "All" else None)
        if status_f == "Active":   users = [u for u in users if u["is_active"]]
        if status_f == "Inactive": users = [u for u in users if not u["is_active"]]
        if search_f:
            users = [u for u in users if search_f.lower() in u["full_name"].lower()
                     or search_f.lower() in u["username"].lower()]

        section(f"{len(users)} User(s) Found")
        for u in users:
            status_lbl = "Active" if u["is_active"] else "Inactive"
            sr_tag     = "  [Self-Registered]" if u.get("self_registered") else ""
            with st.expander(f"{u['full_name']}  (@{u['username']}){sr_tag}  |  {u['role'].title()}  |  {status_lbl}", expanded=False):
                c1, c2, c3, c4 = st.columns(4)
                c1.markdown(f"**User ID:** {u['user_id']}  \n**Username:** {u['username']}  \n**Role:** {u['role'].title()}")
                c2.markdown(f"**Email:** {u.get('email') or '—'}  \n**Phone:** {u.get('phone') or '—'}  \n**Joined:** {str(u['created_at'])[:10]}")
                c3.markdown(f"**Status:** {'Active' if u['is_active'] else 'Inactive'}  \n**Date of Birth:** {u.get('date_of_birth') or '—'}  \n**Gender:** {u.get('gender') or '—'}")
                with c4:
                    if u["user_id"] != user["user_id"]:
                        if u["is_active"]:
                            if st.button("Deactivate", key=f"deact_{u['user_id']}"):
                                M.update_user_status(u["user_id"], False)
                                M.log_audit(user["user_id"], user["username"], "USER_DEACTIVATED", f"Deactivated {u['username']}")
                                st.success("User deactivated."); st.rerun()
                        else:
                            if st.button("Activate", key=f"act_{u['user_id']}"):
                                M.update_user_status(u["user_id"], True)
                                M.log_audit(user["user_id"], user["username"], "USER_ACTIVATED", f"Activated {u['username']}")
                                st.success("User activated."); st.rerun()
                        if st.button("Reset Password", key=f"rpwd_{u['user_id']}"):
                            np = f"Temp@{u['user_id']}123"
                            M.reset_password(u["user_id"], np)
                            st.info(f"Temporary password set to: {np}")

    with tab2:
        section("New User Account")
        with st.form("create_user_form"):
            c1, c2 = st.columns(2)
            with c1:
                nu      = st.text_input("Username *")
                npwd    = st.text_input("Password *", type="password")
                nrole   = st.selectbox("Role *", ["customer","cashier","admin","manager"])
                nname   = st.text_input("Full Name *")
                nemail  = st.text_input("Email Address")
                nphone  = st.text_input("Phone Number")
            with c2:
                ndob    = st.date_input("Date of Birth", value=date(1990,1,1))
                ngender = st.selectbox("Gender", ["Male","Female","Other"])
                naddr   = st.text_area("Address", height=72)
                emp_code = dept = grade = designation = None; salary = 0.0; joining = None
                if nrole in ("cashier","admin","manager"):
                    st.markdown("**Employee Information**")
                    emp_code    = st.text_input("Employee Code")
                    dept        = st.text_input("Department")
                    grade       = st.selectbox("Grade", ["Junior","Mid","Senior","Lead","Head"])
                    designation = st.text_input("Designation")
                    salary      = st.number_input("Monthly Salary (INR)", min_value=0.0, step=1000.0)
                    joining     = st.date_input("Date of Joining", value=date.today())
            sub = st.form_submit_button("Create User Account", use_container_width=True)
        if sub:
            if not nu.strip() or not npwd or not nname.strip():
                st.error("Username, password and full name are required.")
            else:
                ok, msg = M.create_user(nu.strip(), npwd, nrole, nname.strip(),
                                         nemail, nphone, naddr, ndob, ngender,
                                         emp_code, dept, grade, designation, salary, joining)
                if ok:
                    st.success(msg)
                    M.log_audit(user["user_id"], user["username"], "CREATE_USER", f"Created {nrole} '{nu}'")
                else:
                    st.error(msg)


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — FUND TRANSFER
# ══════════════════════════════════════════════════════════════════════════════
def admin_fund_transfer_page():
    user = st.session_state.user
    show_header("Admin Fund Transfer", "Credit funds directly to a customer account")
    warn_box("All admin fund transfers are logged in the audit trail and are irreversible.")

    search = st.text_input("Enter Account ID", placeholder="BOB…")
    if search:
        acc = M.get_account_with_owner(search.strip())
        if acc:
            col = ACCOUNT_COLORS.get(acc["account_type"], "#c9a84c")
            st.markdown(f"""
            <div class="account-card" style="border-left-color:{col}">
              <div class="acc-type">{acc['account_type']} &nbsp;{status_badge(acc['status'])}</div>
              <div class="acc-id">{acc['account_id']}</div>
              <div class="acc-bal">{inr(acc['balance'])}</div>
              <div class="acc-meta">Account Holder: <strong>{acc['full_name']}</strong> (@{acc['username']})</div>
            </div>""", unsafe_allow_html=True)
            with st.form("admin_xfer_form"):
                c1, c2 = st.columns(2)
                with c1: amount    = st.number_input("Credit Amount (INR) *", min_value=1.0, step=100.0)
                with c2: narration = st.text_input("Narration / Reason for Transfer *")
                sub = st.form_submit_button("Credit Account", use_container_width=True)
            if sub:
                if not narration.strip():
                    st.error("A narration is required for all admin transfers.")
                else:
                    ok, msg = M.admin_credit(acc["account_id"], amount, narration, user["user_id"])
                    if ok:
                        st.success(msg)
                        M.log_audit(user["user_id"], user["username"], "ADMIN_TRANSFER",
                                    f"{inr(amount)} to {acc['account_id']} | {narration}")
                    else:
                        st.error(msg)
        elif search:
            st.error("Account not found.")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — INTEREST RATE SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
def interest_rate_settings_page():
    user  = st.session_state.user
    show_header("Interest Rate Settings", "Configure base interest rates for all account types")

    rates = M.get_interest_rates()
    cols  = st.columns(5)
    RATE_COLORS = {"Savings":"#c9a84c","Current":"#7fb3f5","Fixed Deposit":"#a78bfa",
                   "Recurring Deposit":"#6ee7b7","Salary Account":"#67e8f9"}
    for i, r in enumerate(rates):
        with cols[i]:
            metric_card(r["account_type"], f"{r['rate']}% p.a.", "chart",
                        RATE_COLORS.get(r["account_type"], "#0f2552"))

    st.markdown("<br>", unsafe_allow_html=True)
    section("Update Interest Rates")
    rate_map = {r["account_type"]: float(r["rate"]) for r in rates}
    with st.form("rate_form"):
        c1, c2 = st.columns(2)
        inputs = {}
        rate_list = ["Savings","Current","Fixed Deposit","Recurring Deposit","Salary Account"]
        for i, atype in enumerate(rate_list):
            with (c1 if i % 2 == 0 else c2):
                inputs[atype] = st.number_input(f"{atype} (% p.a.)",
                    min_value=0.0, max_value=15.0, step=0.25, value=rate_map.get(atype, 0.0))
        sub = st.form_submit_button("Save All Rates", use_container_width=True)
    if sub:
        for atype, rval in inputs.items():
            ok, msg = M.update_interest_rate(atype, rval, user["user_id"])
            if ok:  st.success(msg)
            else:   st.error(msg)
        M.log_audit(user["user_id"], user["username"], "UPDATE_RATES", "Updated all interest rates")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
PLOT_COLORS = ["#c9a84c","#7fb3f5","#a78bfa","#6ee7b7","#67e8f9","#f9a8d4","#fca5a5"]

def admin_analytics_page():
    user = st.session_state.user
    show_header("Analytics", "Bank performance overview")

    c1, c2 = st.columns(2)
    with c1:
        section("Account Balances by Type")
        dist = M.get_account_type_distribution()
        if dist:
            df  = pd.DataFrame(dist)
            fig = px.bar(df, x="account_type", y=df["total_balance"].astype(float),
                labels={"account_type":"Account Type","y":"Balance (INR)"},
                color="account_type", color_discrete_sequence=PLOT_COLORS)
            fig.update_layout(showlegend=False, height=300,
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#2a3d6b"))
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        section("Transaction Volume — Last 7 Days")
        trend = M.get_transaction_trend(7)
        if trend:
            df_t = pd.DataFrame(trend)
            df_t["txn_date"] = pd.to_datetime(df_t["txn_date"])
            fig2 = px.line(df_t, x="txn_date", y="count", markers=True,
                labels={"txn_date":"Date","count":"Transactions"},
                color_discrete_sequence=["#0f2552"])
            fig2.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#2a3d6b"))
            st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        section("Loan Portfolio by Purpose")
        portfolio = M.get_loan_portfolio_by_purpose()
        if portfolio:
            df_l = pd.DataFrame(portfolio)
            fig3 = px.pie(df_l, values="total_amount", names="loan_purpose",
                color_discrete_sequence=PLOT_COLORS, hole=.36)
            fig3.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10,b=10))
            st.plotly_chart(fig3, use_container_width=True)
        else:
            info_box("No approved loans on record.")
    with c4:
        section("Loans by Collateral Type")
        coll = M.get_loan_by_collateral()
        if coll:
            df_c = pd.DataFrame(coll)
            fig4 = px.bar(df_c, x="collateral_type", y="count",
                color="collateral_type", color_discrete_sequence=PLOT_COLORS)
            fig4.update_layout(showlegend=False, height=300,
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#2a3d6b"))
            st.plotly_chart(fig4, use_container_width=True)
        else:
            info_box("No loan records found.")


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN / MANAGER — AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════
def audit_log_page():
    user = st.session_state.user
    show_header("Audit Log", "System activity — all critical events are logged")
    c1, c2, c3 = st.columns(3)
    with c1: limit    = st.selectbox("Show entries", [50,100,200,500], index=1)
    with c2: action_f = st.text_input("Filter by Action", placeholder="e.g. LOGIN, FUND_TRANSFER")
    with c3: user_f   = st.text_input("Filter by Username")
    logs = M.get_audit_logs(limit)
    if action_f: logs = [l for l in logs if action_f.upper() in (l["action"] or "").upper()]
    if user_f:   logs = [l for l in logs if user_f.lower() in (l["username"] or "").lower()]
    section(f"{len(logs)} Log Entries")
    if logs:
        rows = [{"ID": l["log_id"], "Username": l.get("username") or "—",
            "Action": l["action"], "Details": (l.get("details") or "")[:80],
            "IP Address": l.get("ip_address") or "—",
            "Timestamp": str(l["created_at"])[:19]} for l in logs]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=500)
    else:
        info_box("No entries match the filter criteria.")


# ══════════════════════════════════════════════════════════════════════════════
# MANAGER — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def manager_dashboard():
    user = st.session_state.user
    show_header("Manager Dashboard", f"Executive Overview — {user['full_name']}")
    s = M.get_bank_summary()
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("Pending Loans",    str(s["pending_loans"]),        "clock",     "#b45309")
    with c2: metric_card("Loan Portfolio",   inr(s["total_loans_amount"]),   "loans",     "#0f2552")
    with c3: metric_card("Active Accounts",  str(s["total_accounts"]),       "accounts",  "#1d4ed8")
    with c4: metric_card("Total Deposits",   inr(s["total_balance"]),        "balance",   "#15803d")

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns(2)

    with left:
        section("Pending Loan Applications")
        pending = M.get_pending_loans()
        if not pending:
            st.success("No pending loan applications.")
        for loan in pending[:5]:
            st.markdown(f"""
            <div class="account-card" style="border-left-color:#b45309">
              <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                  <div style="font-weight:700;color:#0f2552">{loan['applicant_name']}</div>
                  <div style="font-size:.78rem;color:#6b7280;margin-top:2px">
                    {loan['loan_id']} &nbsp;|&nbsp; {loan['loan_purpose']} &nbsp;|&nbsp; {inr(loan['loan_amount'])}
                  </div>
                  <div style="font-size:.74rem;color:#9ca3af;margin-top:2px">
                    Rate: {loan['computed_interest_rate']}% &nbsp;|&nbsp; EMI: {inr(loan['emi_amount'])} &nbsp;|&nbsp; Collateral: {loan['collateral_type']}
                  </div>
                </div>
                <div style="font-size:.72rem;color:#9ca3af">{str(loan['applied_at'])[:10]}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    with right:
        section("Recent Messages")
        msgs = M.get_manager_inbox()[:5]
        if not msgs:
            info_box("No messages in inbox.")
        for m in msgs:
            status_lbl = "Unread" if not m["is_read"] else "Read"
            weight     = "700" if not m["is_read"] else "400"
            st.markdown(f"""
            <div style="background:white;border-radius:7px;padding:10px 14px;
              margin-bottom:6px;box-shadow:0 1px 4px rgba(0,0,0,.07);
              border-left:3px solid {'#0f2552' if not m['is_read'] else '#e5e7eb'}">
              <div style="font-weight:{weight};font-size:.85rem;color:#0f2552">{m['subject']}</div>
              <div style="font-size:.72rem;color:#9ca3af;margin-top:2px">
                From: {m['sender_name']} ({m['sender_role'].title()}) &nbsp;&middot;&nbsp; {str(m['sent_at'])[:16]} &nbsp;&middot;&nbsp; {status_lbl}
              </div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# MANAGER — LOAN APPROVAL
# ══════════════════════════════════════════════════════════════════════════════
def loan_approval_page():
    user = st.session_state.user
    show_header("Loan Approval", "Review and decide on pending loan applications")

    tab1, tab2 = st.tabs(["Pending Applications", "All Loans"])

    with tab1:
        pending = M.get_pending_loans()
        if not pending:
            st.success("No pending applications. All loan requests have been reviewed.")
        else:
            st.markdown(f"**{len(pending)} application(s) awaiting decision**")
            for loan in pending:
                with st.expander(
                    f"{loan['loan_id']}  |  {loan['applicant_name']}  |  {inr(loan['loan_amount'])}  |  {loan['loan_purpose']}",
                    expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**Applicant:** {loan['applicant_name']}  \n**Username:** @{loan['username']}  \n**Employment:** {loan['employment_status']}  \n**Monthly Income:** {inr(loan['monthly_income'])}")
                    c2.markdown(f"**Loan Amount:** {inr(loan['loan_amount'])}  \n**Purpose:** {loan['loan_purpose']}  \n**Tenure:** {loan['tenure_years']} year(s)  \n**Interest Rate:** {loan['computed_interest_rate']}% p.a.")
                    c3.markdown(f"**Monthly EMI:** {inr(loan['emi_amount'])}  \n**CIBIL Score:** {loan['credit_score']}  \n**Collateral:** {loan['collateral_type']}  \n**Existing Loans:** {loan['existing_loans_count']}")
                    c4, c5 = st.columns(2)
                    c4.markdown(f"**Gender:** {loan['gender']}  |  **DOB:** {loan['date_of_birth']}  \n**KYC Reference:** `{loan['kyc_reference']}`  \n**Applied:** {str(loan['applied_at'])[:10]}")
                    c5.markdown(f"**Disbursement Account:** `{loan['disbursement_account']}`")

                    try:
                        p = LoanProfile(date_of_birth=loan["date_of_birth"], gender=loan["gender"],
                               employment_status=loan["employment_status"],
                               monthly_income=float(loan["monthly_income"]),
                               loan_amount=float(loan["loan_amount"]),
                               tenure_years=loan["tenure_years"], credit_score=loan["credit_score"],
                               collateral_type=loan["collateral_type"],
                               existing_loans_count=loan["existing_loans_count"],
                               loan_purpose=loan["loan_purpose"])
                        bd     = calculate_rate(p)
                        ok_aff, aff_msg = affordability_check(float(loan["monthly_income"]), bd.emi)
                        if ok_aff: st.success(aff_msg)
                        else:      st.warning(aff_msg)
                    except: pass

                    with st.form(f"decide_{loan['loan_id']}"):
                        remarks  = st.text_area("Decision Remarks (required) *",
                            placeholder="Provide reason for approval or rejection.", height=75)
                        ca, cb   = st.columns(2)
                        approve  = ca.form_submit_button("Approve and Disburse", use_container_width=True)
                        reject   = cb.form_submit_button("Reject Application", use_container_width=True)
                    if approve or reject:
                        if not remarks.strip():
                            st.error("Remarks are required before submitting a decision.")
                        else:
                            decision = "Approved" if approve else "Rejected"
                            ok, msg  = M.decide_loan(loan["loan_id"], decision, remarks, user["user_id"])
                            if ok:
                                st.success(msg)
                                M.log_audit(user["user_id"], user["username"], f"LOAN_{decision.upper()}",
                                            f"{loan['loan_id']} | {inr(loan['loan_amount'])}")
                                st.rerun()
                            else:
                                st.error(msg)

    with tab2:
        all_loans = M.get_all_loans()
        if not all_loans: info_box("No loan records found."); return
        c_filt = st.selectbox("Filter by Status", ["All","Pending","Approved","Disbursed","Rejected"])
        if c_filt != "All": all_loans = [l for l in all_loans if l["status"] == c_filt]
        rows = [{"Loan ID": l["loan_id"], "Applicant": l["applicant_name"],
            "Amount (INR)": f"{float(l['loan_amount']):,.2f}", "Purpose": l["loan_purpose"],
            "Collateral": l["collateral_type"], "Rate": f"{l['computed_interest_rate']}%",
            "EMI (INR)": f"{float(l['emi_amount']):,.2f}", "Status": l["status"],
            "Applied On": str(l["applied_at"])[:10]} for l in all_loans]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=420)


# ══════════════════════════════════════════════════════════════════════════════
# MANAGER — PROMOTE EMPLOYEE
# ══════════════════════════════════════════════════════════════════════════════
def promote_employee_page():
    user      = st.session_state.user
    show_header("Promote Employee", "Update employee grade, designation and salary")

    employees = M.get_all_employees()
    if not employees: info_box("No employees on record."); return

    emp_opts = {f"{e['full_name']}  (@{e['username']})  —  {e.get('designation','—')}  |  {e['role'].title()}": e["user_id"]
                for e in employees}

    section("Select Employee")
    with st.form("promote_form"):
        selected  = st.selectbox("Employee *", list(emp_opts.keys()))
        emp_uid   = emp_opts[selected]
        emp_data  = next((e for e in employees if e["user_id"] == emp_uid), {})
        c1, c2    = st.columns(2)
        with c1:
            cur_grade  = emp_data.get("grade", "Junior")
            grade_opts = ["Junior","Mid","Senior","Lead","Head"]
            new_grade  = st.selectbox("New Grade *", grade_opts,
                index=grade_opts.index(cur_grade) if cur_grade in grade_opts else 0)
            new_desig  = st.text_input("New Designation *", value=emp_data.get("designation") or "")
        with c2:
            new_salary = st.number_input("New Monthly Salary (INR) *", min_value=0.0, step=1000.0,
                                          value=float(emp_data.get("salary") or 0))
            role_opts  = ["— No Change —","cashier","admin","manager"]
            new_role   = st.selectbox("Change Role (optional)", role_opts)
        sub = st.form_submit_button("Apply Promotion", use_container_width=True)

    if sub:
        role_change = None if new_role == "— No Change —" else new_role
        ok, msg = M.promote_employee(emp_uid, new_grade, new_desig, new_salary, role_change)
        if ok:
            st.success(msg)
            M.log_audit(user["user_id"], user["username"], "EMPLOYEE_PROMOTED",
                        f"User {emp_uid} — Grade: {new_grade} | Salary: {inr(new_salary)}/mo")
        else:
            st.error(msg)

    st.markdown("<br>", unsafe_allow_html=True)
    section("Employee Directory")
    rows = [{"Name": e["full_name"], "Username": e["username"],
        "Role": e["role"].title(), "Grade": e.get("grade","—"),
        "Designation": e.get("designation","—"),
        "Monthly Salary (INR)": f"{float(e.get('salary',0)):,.2f}",
        "Department": e.get("department","—")} for e in employees]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# MANAGER — INTEREST ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
def interest_analytics_page():
    user  = st.session_state.user
    show_header("Interest Analytics", "Portfolio analytics and interest income overview")
    s     = M.get_bank_summary()
    rates = M.get_interest_rates()

    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Total Deposits",  inr(s["total_balance"]),         "balance")
    with c2: metric_card("Loan Portfolio",  inr(s["total_loans_amount"]),    "loans")
    with c3:
        avg = sum(float(r["rate"]) for r in rates if r["account_type"] != "Current") / \
              max(len([r for r in rates if r["account_type"] != "Current"]), 1)
        metric_card("Avg Deposit Rate", f"{avg:.2f}% p.a.", "chart")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)

    with c1:
        section("Balance vs Projected Annual Interest")
        dist = M.get_account_type_distribution()
        if dist:
            df     = pd.DataFrame(dist)
            rmap   = {r["account_type"]: float(r["rate"]) for r in rates}
            df["projected_interest"] = df.apply(
                lambda r: float(r["total_balance"]) * rmap.get(r["account_type"], 0) / 100, axis=1)
            fig = go.Figure(data=[
                go.Bar(name="Balance", x=df["account_type"], y=df["total_balance"].astype(float),
                       marker_color="#0f2552"),
                go.Bar(name="Annual Interest", x=df["account_type"], y=df["projected_interest"],
                       marker_color="#c9a84c"),
            ])
            fig.update_layout(barmode="group", height=320, legend=dict(orientation="h", y=1.05),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#2a3d6b"))
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        section("Loan Portfolio by Purpose")
        portfolio = M.get_loan_portfolio_by_purpose()
        if portfolio:
            df_l = pd.DataFrame(portfolio)
            fig2 = px.pie(df_l, values="total_amount", names="loan_purpose",
                color_discrete_sequence=PLOT_COLORS, hole=.38)
            fig2.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10,b=10))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            info_box("No approved loans on record.")

    c3, c4 = st.columns(2)
    with c3:
        section("Collateral Risk Distribution")
        coll = M.get_loan_by_collateral()
        if coll:
            df_c = pd.DataFrame(coll)
            fig3 = px.bar(df_c, x="collateral_type", y="count", text="count",
                color="collateral_type", color_discrete_sequence=PLOT_COLORS)
            fig3.update_layout(showlegend=False, height=280,
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            info_box("No loan data available.")

    with c4:
        section("Transaction Volume — Last 30 Days")
        trend = M.get_transaction_trend(30)
        if trend:
            df_t = pd.DataFrame(trend)
            df_t["txn_date"] = pd.to_datetime(df_t["txn_date"])
            fig4 = px.area(df_t, x="txn_date", y="total_amount",
                labels={"txn_date":"Date","total_amount":"Amount (INR)"},
                color_discrete_sequence=["#0f2552"])
            fig4.update_layout(height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            info_box("No transactions in the last 30 days.")

    section("Current Interest Rate Schedule")
    r_rows = [{"Account Type": r["account_type"], "Rate (% p.a.)": r["rate"],
               "Last Updated": str(r["updated_at"])[:16]} for r in rates]
    st.dataframe(pd.DataFrame(r_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# MANAGER — INBOX
# ══════════════════════════════════════════════════════════════════════════════
def manager_inbox_page():
    user  = st.session_state.user
    show_header("Manager Inbox", "Reports and messages from cashiers")
    msgs  = M.get_manager_inbox()
    unread = [m for m in msgs if not m["is_read"]]

    c1, c2 = st.columns(2)
    with c1: metric_card("Total Messages", str(len(msgs)),   "inbox")
    with c2: metric_card("Unread",         str(len(unread)), "inbox", "#b45309")

    if not msgs: info_box("Inbox is empty."); return

    st.markdown("<br>", unsafe_allow_html=True)
    show_unread = st.checkbox("Show unread only", value=False)
    display     = unread if show_unread else msgs

    for m in display:
        weight = "700" if not m["is_read"] else "400"
        border = "#0f2552" if not m["is_read"] else "#d1d5db"
        with st.expander(
            f"{'[UNREAD]  ' if not m['is_read'] else ''}{m['subject']}  —  {m['sender_name']}  —  {str(m['sent_at'])[:16]}",
            expanded=not m["is_read"]):
            st.markdown(m["body"])
            if not m["is_read"]:
                if st.button("Mark as Read", key=f"rd_{m['message_id']}"):
                    M.mark_message_read(m["message_id"]); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════════════════
def main():
    if not st.session_state.user:
        login_page(); return
    check_timeout()
    sidebar_nav()

    role  = st.session_state.user["role"]
    page  = st.session_state.page

    ROUTES = {
        "customer": {
            "Dashboard": customer_dashboard, "My Accounts": customer_accounts,
            "Open Account": open_account_page, "Fund Transfer": fund_transfer_page,
            "Transaction History": transaction_history_page,
            "Apply for Loan": loan_application_page, "Loan Status": loan_status_page,
        },
        "cashier": {
            "Dashboard": cashier_dashboard, "Process Transaction": process_transaction_page,
            "Disburse Salary": disburse_salary_page, "Send Report": send_report_page,
            "All Transactions": all_transactions_page,
        },
        "admin": {
            "Dashboard": admin_dashboard, "Manage Users": manage_users_page,
            "Admin Fund Transfer": admin_fund_transfer_page,
            "Interest Rate Settings": interest_rate_settings_page,
            "Analytics": admin_analytics_page, "Audit Log": audit_log_page,
        },
        "manager": {
            "Dashboard": manager_dashboard, "Loan Approval": loan_approval_page,
            "Promote Employee": promote_employee_page,
            "Interest Analytics": interest_analytics_page,
            "Manager Inbox": manager_inbox_page, "Audit Log": audit_log_page,
        },
    }

    route = ROUTES.get(role, {})
    fn    = route.get(page) or route.get("Dashboard")
    if fn: fn()
    else:  st.error("Page not found.")

if __name__ == "__main__":
    main()