# Bank of Bharat — Online Banking System

> A full-featured multi-role online banking web application built as a college Software Engineering Lab project.  
> **Stack:** Python · Streamlit · MySQL · bcrypt · Plotly

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [File Structure](#3-file-structure)
4. [User Roles & Capabilities](#4-user-roles--capabilities)
5. [Loan Interest Rate Engine](#5-loan-interest-rate-engine)
6. [Function Reference](#6-function-reference)
7. [Database Schema](#7-database-schema)
8. [Sample Users & Credentials](#8-sample-users--credentials)
9. [Installation & Setup](#9-installation--setup)
10. [Running the Application](#10-running-the-application)
11. [Screenshots](#11-screenshots)
12. [Project Documents](#12-project-documents)

---

## 1. Project Overview

**Bank of Bharat** is a browser-based, multi-role online banking system that simulates the core operations of a modern Indian retail bank. It is designed as a demonstration/prototype for a college Software Engineering lab assignment.

The system supports **four user roles**, each with a dedicated dashboard and a strictly enforced set of permissions:

| Role | Primary Responsibility |
|---|---|
| Customer | Account management, fund transfers, loan applications |
| Cashier | Process deposits/withdrawals, disburse salaries, send reports |
| Bank Admin | User management, admin transfers, interest rate configuration |
| Manager | Loan approval, employee promotion, analytics, inbox |

### Key Features

- Role-Based Access Control (RBAC) — every route is gated by role
- **Loan Interest Rate Engine** — 10-factor personalised rate calculation
- Five account types: Savings, Current, Fixed Deposit, Recurring Deposit, Salary Account
- Seven loan types with purpose-based rate adjustments
- Five collateral types with differentiated security discounts
- bcrypt password hashing with salted rounds
- Account lockout after 5 consecutive failed login attempts (15-minute cooldown)
- Session timeout after 10 minutes of inactivity
- Complete audit log for all critical system events
- Real-time Plotly analytics dashboards
- Both self-registration (customers) and admin-created accounts

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  (app.py — role-specific dashboards, forms, charts)         │
└──────────────────────┬──────────────────────────────────────┘
                       │  Python function calls
┌──────────────────────▼──────────────────────────────────────┐
│                   Business Logic Layer                       │
│  models.py          loan_engine.py         database.py       │
│  (all DB ops)       (rate & EMI calc)      (connection pool)  │
└──────────────────────┬──────────────────────────────────────┘
                       │  mysql-connector-python
┌──────────────────────▼──────────────────────────────────────┐
│               MySQL Database (local)                         │
│  bank_of_bharat — 9 tables, ACID-compliant transactions      │
└─────────────────────────────────────────────────────────────┘
```

The application is a **single-process, three-tier** system:
- **Presentation:** Streamlit pages rendered in the browser
- **Logic:** Pure Python modules — no separate API server needed
- **Data:** MySQL with atomic multi-statement transactions for financial operations

---

## 3. File Structure

```
bank_of_bharat/
│
├── app.py                  # Main Streamlit application — all UI pages & routing
├── models.py               # All database read/write operations
├── loan_engine.py          # Loan Interest Rate Engine (10-factor model + EMI)
├── database.py             # MySQL connection helper, fetchone/fetchall/execute
├── init_db.py              # One-time setup: runs schema, seeds default users
├── setup.sql               # Full MySQL DDL — all CREATE TABLE statements
├── requirements.txt        # Python dependencies
│
├── .streamlit/
   └── config.toml         # Streamlit dark theme configuration

```

---

## 4. User Roles & Capabilities

### Customer
- Self-register or be created by Bank Admin
- Open any of the 5 account types
- Check account balances and view transaction history (last 50 transactions)
- Initiate fund transfers to any valid account
- Apply for loans with live interest rate preview
- Track loan application status

### Cashier
- Process cash deposits and withdrawals on customer accounts
- Disburse monthly salary for all employees (duplicate-prevention enforced per employee per month)
- Compose and send operational reports to the Manager
- View full system transaction history

### Bank Admin
- Create, activate, and deactivate user accounts for all roles (including Manager)
- Execute admin-initiated fund credits to customer accounts (fully audit-logged)
- Configure base interest rates for all five account types
- View analytics dashboard and full audit log

### Manager
- Review and approve or reject pending loan applications (with mandatory remarks)
- On approval — loan amount is automatically disbursed to the customer's account
- Promote employees: update grade, designation, and salary
- View interest analytics and portfolio breakdown charts
- Read reports sent by Cashiers via the Manager Inbox

---

## 5. Loan Interest Rate Engine

**File:** `loan_engine.py`

The engine computes a personalised annual interest rate using an **additive model** on top of a fixed base rate. The result is clamped to a floor and cap.

### 5.1 Rate Formula

$$
R_{\text{raw}} = R_{\text{base}} + \Delta_{\text{age}} + \Delta_{\text{gender}} + \Delta_{\text{tenure}} + \Delta_{\text{employment}} + \Delta_{\text{CIBIL}} + \Delta_{\text{collateral}} + \Delta_{\text{existing\_loans}} + \Delta_{\text{LTI}} + \Delta_{\text{purpose}}
$$

$$
R_{\text{final}} = \max\!\left(6.00,\ \min\!\left(22.00,\ R_{\text{raw}}\right)\right)
$$

Where $R_{\text{base}} = 8.00\%$ p.a.

### 5.2 Factor Adjustment Table

| Factor | Condition | Adjustment (% p.a.) |
|---|---|---|
| **Base Rate** | Always applied | +8.00 |
| **Age** | < 25 years | +2.00 |
| | 25–35 years | 0.00 |
| | 36–50 years | +0.50 |
| | 51–60 years | +1.00 |
| | > 60 years | +2.00 |
| **Gender** | Female | −0.50 |
| | Male / Other | 0.00 |
| **Loan Tenure** | ≤ 1 year | 0.00 |
| | 2–3 years | +0.50 |
| | 4–5 years | +1.00 |
| | 6–10 years | +1.50 |
| | > 10 years | +2.00 |
| **Employment** | Employed (Salaried) | 0.00 |
| | Self-Employed | +1.00 |
| | Unemployed | +3.00 |
| **CIBIL Score** | ≥ 750 (Excellent) | −1.50 |
| | 650–749 (Good) | 0.00 |
| | 550–649 (Fair) | +1.50 |
| | < 550 (Poor) | +3.00 |
| **Collateral Type** | Gold | −1.50 |
| | Fixed Deposit | −1.25 |
| | Property / Real Estate | −1.00 |
| | Vehicle | −0.75 |
| | None | +2.00 |
| **Existing Loans** | 0 active loans | 0.00 |
| | 1 active loan | +0.50 |
| | ≥ 2 active loans | +1.50 |
| **LTI Ratio** | $\text{LTI} < 2\times$ annual income | 0.00 |
| | $2\times \leq \text{LTI} \leq 4\times$ | +0.50 |
| | $\text{LTI} > 4\times$ | +1.50 |
| **Loan Purpose** | Gold Loan | −0.75 |
| | Education | −0.50 |
| | Home | −0.25 |
| | Vehicle / Car | 0.00 |
| | Personal | +0.50 |
| | Business | +0.75 |
| | Vacation | +1.00 |

### 5.3 Loan-to-Income (LTI) Ratio

$$
\text{LTI} = \frac{P}{I_{\text{annual}}} = \frac{P}{I_{\text{monthly}} \times 12}
$$

Where $P$ is the principal loan amount and $I_{\text{monthly}}$ is the applicant's monthly income.

### 5.4 EMI Calculation

The Equated Monthly Instalment uses the standard reducing-balance formula:

$$
\text{EMI} = P \cdot \frac{r\,(1+r)^{n}}{(1+r)^{n} - 1}
$$

Where:
- $P$ = Principal loan amount (INR)
- $r$ = Monthly interest rate $= \dfrac{R_{\text{final}}}{100 \times 12}$
- $n$ = Total number of monthly instalments $= \text{Tenure (years)} \times 12$

**Special case** — when $r = 0$ (zero-interest loan):

$$
\text{EMI} = \frac{P}{n}
$$

### 5.5 Total Interest and Total Payable

$$
\text{Total Payable} = \text{EMI} \times n
$$

$$
\text{Total Interest} = \text{Total Payable} - P
$$

### 5.6 Affordability Check

A loan application is only accepted if the applicant's monthly income is **at least 3× the EMI**:

$$
I_{\text{monthly}} \geq 3 \times \text{EMI}
$$

If this condition fails, the application is rejected at submission time regardless of the interest rate computed.

### 5.7 Worked Example

> Applicant: Female, Age 30, Employed, Income ₹60,000/month  
> Loan: ₹5,00,000 | Home Loan | 5 years | CIBIL 760 | Collateral: FD | 0 existing loans

$$
R_{\text{raw}} = 8.00 + 0.00 - 0.50 + 1.00 + 0.00 - 1.50 - 1.25 + 0.00 + 0.00 - 0.25 = 5.50\%
$$

$$
R_{\text{final}} = \max(6.00,\ 5.50) = \mathbf{6.00\%}\ \text{p.a.}
$$

$$
r = \frac{6.00}{100 \times 12} = 0.005, \quad n = 60
$$

$$
\text{EMI} = 5{,}00{,}000 \times \frac{0.005 \times (1.005)^{60}}{(1.005)^{60} - 1} \approx \mathbf{₹9{,}666.44}
$$

$$
\text{Affordability: } 60{,}000 \geq 3 \times 9{,}666.44 = 28{,}999.32 \quad \checkmark
$$

---

## 6. Function Reference

### 6.1 `database.py` — Connection Utilities

| Function | Signature | Description |
|---|---|---|
| `get_connection()` | `() → Connection \| None` | Opens and returns a fresh `mysql.connector` connection using `DB_CONFIG`. Returns `None` and shows an error on failure. |
| `fetchall()` | `(query, params) → list[dict]` | Executes a SELECT query and returns all matching rows as a list of dictionaries. |
| `fetchone()` | `(query, params) → dict \| None` | Executes a SELECT query and returns the first row as a dictionary, or `None`. |
| `execute()` | `(query, params) → int \| None` | Executes INSERT / UPDATE / DELETE. Commits on success, rolls back on error. Returns `lastrowid`. |
| `execute_transaction()` | `(queries: list[tuple]) → bool` | Executes a list of `(sql, params)` tuples atomically — all succeed or all roll back. Used for all financial operations. |

---

### 6.2 `loan_engine.py` — Rate & EMI Engine

| Function | Signature | Description |
|---|---|---|
| `_calc_age()` | `(dob: date) → int` | Computes exact age in completed years, correctly handling birthday not yet passed in the current year. |
| `calculate_rate()` | `(profile: LoanProfile) → RateBreakdown` | Applies the 10-factor additive model, clamps result to [6%, 22%], computes EMI, total payable, and total interest. Returns a `RateBreakdown` dataclass. |
| `affordability_check()` | `(monthly_income, emi) → (bool, str)` | Returns `(True, message)` if $I_{\text{monthly}} \geq 3 \times \text{EMI}$, else `(False, reason)`. |

**Data classes:**

- `LoanProfile` — input to the engine (10 fields: dob, gender, employment, income, loan amount, tenure, CIBIL, collateral type, existing loans, loan purpose)
- `RateBreakdown` — engine output (all 10 adjustment values + final rate + EMI + totals)

---

### 6.3 `models.py` — Database Operations

#### Authentication

| Function | Description |
|---|---|
| `authenticate(username, password)` | Verifies credentials against bcrypt hash. Tracks failed attempts; locks account for 15 min after 5 failures. Resets counter on success. |
| `hash_password(plain)` | Wraps `bcrypt.hashpw` with auto-generated salt. Plain text is never stored. |
| `verify_password(plain, hashed)` | Wraps `bcrypt.checkpw` for constant-time comparison. |
| `log_audit(user_id, username, action, details)` | Inserts a row into `audit_log` with a timestamp and IP address for every critical action. |

#### User Management

| Function | Description |
|---|---|
| `create_user(...)` | Creates a row in `users` and, for staff roles, a linked row in `employees`. Prevents duplicate usernames. |
| `update_user_status(user_id, is_active)` | Activates or deactivates an account without deleting it. |
| `reset_password(user_id, new_password)` | Re-hashes and stores a new password. Old password is not required (admin action). |
| `get_all_users(role)` | Returns all users, optionally filtered by role. |

#### Account Operations

| Function | Description |
|---|---|
| `open_account(user_id, account_type, initial_deposit, ...)` | Creates a new account record, looks up the current base rate, optionally sets maturity date for FD/RD, and records the opening deposit as the first transaction. |
| `get_customer_accounts(user_id)` | Returns all accounts belonging to a customer. |
| `get_account_with_owner(account_id)` | JOINs `accounts` with `users` to return account details plus the holder's name and username. |

#### Transactions

All financial mutations use `execute_transaction()` to guarantee atomicity.

| Function | Description |
|---|---|
| `deposit(to_account, amount, narration, processed_by)` | Atomically increments balance and inserts a `Deposit` transaction record. |
| `withdraw(from_account, amount, narration, processed_by)` | Checks sufficient balance, then atomically decrements balance and inserts a `Withdrawal` record. |
| `transfer(from_account, to_account, amount, narration, ...)` | Atomically decrements source balance, increments destination balance, and inserts a single `Transfer` record in one transaction. |
| `admin_credit(to_account, amount, narration, admin_id)` | Credits a customer account without a corresponding debit (admin-funded). Logged separately for audit. |

#### Loans

| Function | Description |
|---|---|
| `submit_loan(...)` | Stores all 17 loan fields including the pre-computed interest rate and EMI. Status defaults to `Pending`. |
| `decide_loan(loan_id, decision, remarks, manager_id)` | Sets status to `Approved` or `Rejected`. On approval, atomically credits the loan amount to the disbursement account and updates status to `Disbursed`. |

#### Salary

| Function | Description |
|---|---|
| `disburse_salary(employee_user_id, cashier_user_id, amount, month_year)` | Inserts a disbursement record. The unique constraint `(employee_user_id, month_year)` prevents duplicate payments for the same employee in the same month. |

#### Analytics

| Function | Description |
|---|---|
| `get_bank_summary()` | Returns 6 aggregate KPIs: total customers, active accounts, total balance, pending loans, total loan portfolio, and today's transaction count. |
| `get_transaction_trend(days)` | Returns daily transaction count and volume for the last N days, used to render trend charts. |
| `get_account_type_distribution()` | Returns count and total balance grouped by account type. |
| `get_loan_by_collateral()` | Returns loan count, total amount, and average rate grouped by collateral type. |

---

## 7. Database Schema

Nine tables, all in the `bank_of_bharat` database:

```
users               — All users (all roles), authentication, lockout state
employees           — Extended profile for cashier / admin / manager
accounts            — Customer bank accounts (5 types)
transactions        — Every financial event (deposit, withdrawal, transfer, etc.)
loans               — Loan applications with all 17 data fields
interest_rates      — Base rates for each account type (admin-configurable)
salary_disbursements — Monthly salary records with duplicate-prevention constraint
messages            — Cashier → Manager reports/messages
audit_log           — Immutable event log for all critical actions
```

**Key design decisions:**
- `execute_transaction()` wraps all multi-table financial writes in a single MySQL transaction
- `salary_disbursements` has a `UNIQUE(employee_user_id, month_year)` constraint at the DB level — not just application logic
- Passwords stored as bcrypt hashes only — plain text never persisted
- `account_id`, `transaction_id`, `loan_id` use timestamp + random digits to avoid collisions

---

## 8. Sample Users & Credentials

These users are created automatically when you run `python init_db.py`:

| Username | Password | Role | Full Name | Details |
|---|---|---|---|---|
| `admin` | `Admin@123` | Bank Admin | System Administrator | Can create all user types including Manager |
| `manager` | `Manager@123` | Manager | Rajesh Kumar | Approves loans, promotes employees |
| `cashier1` | `Cashier@123` | Cashier | Priya Sharma | Processes transactions, disburses salary |
| `cashier2` | `Cashier@123` | Cashier | Vikram Mehta | Second cashier for testing salary workflows |
| `customer1` | `Customer@123` | Customer | Amit Patel | Pre-seeded with a Savings and a Salary Account |
| `customer2` | `Customer@123` | Customer | Sunita Devi | No accounts — use to test account opening flow |

> **Note:** Change all default passwords before any non-demo use.

### Pre-seeded Accounts for `customer1`

| Account ID | Type | Opening Balance |
|---|---|---|
| Auto-generated (BOB...) | Savings Account | ₹25,000.00 |
| Auto-generated (BOB...) | Salary Account | ₹50,000.00 |

The exact account IDs are generated at `init_db.py` runtime (timestamp-based). Check them from the Admin → Manage Users panel or log in as `customer1` to see them on the dashboard.

---

## 9. Installation & Setup

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11 or higher | `python --version` to check |
| MySQL Server | 8.0 or higher | Must be running locally |
| pip | Latest | Comes with Python |

### Step 1 — Clone the Repository

```bash
git clone https://github.com/<your-username>/bank-of-bharat.git
cd bank-of-bharat
```

### Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

The dependencies are:

```
streamlit>=1.32.0
mysql-connector-python>=8.3.0
bcrypt>=4.1.2
pandas>=2.2.0
plotly>=5.20.0
```

> On some Linux systems you may need `pip install --break-system-packages -r requirements.txt`

### Step 3 — Configure MySQL Credentials

Open **both** `database.py` and `init_db.py` and update the connection details:

**`database.py`** — find the `DB_CONFIG` dictionary:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "YOUR_MYSQL_PASSWORD",   # ← change this
    "database": "bank_of_bharat",
}
```

**`init_db.py`** — find the constants at the top:
```python
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "YOUR_MYSQL_PASSWORD"         # ← change this
```

### Step 4 — Initialise the Database

Run this **once only**. It creates the database, all tables, and the default users:

```bash
python init_db.py
```

Expected output:
```
==============================================================
  Bank of Bharat — Database Initialiser
==============================================================
Running setup.sql …
 Seeding default users …
  ✅  Created 'admin'    (ID=1, role=admin)
  ✅  Created 'manager'  (ID=2, role=manager)
  ✅  Created 'cashier1' (ID=3, role=cashier)
  ✅  Created 'cashier2' (ID=4, role=cashier)
  ✅  Created 'customer1'(ID=5, role=customer)
  ✅  Created 'customer2'(ID=6, role=customer)
  ✅  Sample account BOB... (Savings) for customer1
  ✅  Sample account BOB... (Salary Account) for customer1
==============================================================
 ✅  Database initialised successfully!
==============================================================
```

> **Already ran init_db.py before and getting column-width errors?**  
> Run this one-time fix first:
> ```bash
> mysql -u root -p bank_of_bharat < fix_columns.sql
> ```
> Then re-run `python init_db.py`.

### Step 5 — Verify the `.streamlit` Folder

Make sure `bank-of-bharat/.streamlit/config.toml` exists with:
```toml
[theme]
base                     = "dark"
primaryColor             = "#c9a84c"
backgroundColor          = "#0f1729"
secondaryBackgroundColor = "#1a2744"
textColor                = "#e8edf5"
font                     = "sans serif"
```

This file is included in the repository. If it is missing, create it manually.

---

## 10. Running the Application

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

To stop the server: press `Ctrl + C` in the terminal.

### Recommended Testing Workflow

1. Log in as **admin** → create a new customer account
2. Log in as **customer1** → open an FD account, apply for a loan
3. Log in as **cashier1** → process a deposit on customer1's account, disburse salary for all staff
4. Log in as **manager** → approve the loan, check the inbox for cashier reports
5. Log in as **admin** → check the Audit Log to see all events recorded

---

## 11. Screenshots

> Add screenshots to a `docs/screenshots/` folder and reference them here.

| Screen | Description |
|---|---|
| `login.png` | Login page with Sign In and Registration tabs |
| `admin_dashboard.png` | Admin dashboard with metric cards and charts |
| `loan_application.png` | Loan form with live rate preview panel |
| `manager_loan_approval.png` | Loan approval screen with affordability check |
| `cashier_salary.png` | Salary disbursement panel with per-employee status |


---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit 1.32+ |
| Backend Logic | Python 3.11 |
| Database | MySQL 8.0 |
| ORM / DB Driver | mysql-connector-python |
| Password Security | bcrypt (salted hashing) |
| Data Manipulation | pandas |
| Charts | Plotly Express + Graph Objects |
| Styling | Custom CSS injected via `st.markdown` |

---

## License

This project is submitted as a college academic assignment and is intended for **educational and demonstration purposes only**. It is not suitable for production banking use.

---
