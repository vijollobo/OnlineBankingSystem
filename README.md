# Bank of Bharat — Online Banking System

> A full-featured, multi-role online banking web application.

**Stack:** Python 3.11 · Streamlit · MySQL 8.0 · bcrypt · Plotly

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Repository Structure](#3-repository-structure)
4. [User Roles and Capabilities](#4-user-roles-and-capabilities)
5. [Loan Interest Rate Engine](#5-loan-interest-rate-engine)
6. [Function Reference](#6-function-reference)
7. [Database Schema](#7-database-schema)
8. [Sample Users and Credentials](#8-sample-users-and-credentials)
9. [Installation and Setup](#9-installation-and-setup)
10. [Running the Application](#10-running-the-application)
11. [Project Documents](#11-project-documents)

---

## 1. Project Overview

**Bank of Bharat** is a browser-based, multi-role online banking system that simulates the core operations of a modern Indian retail bank. It is developed as a prototype for demonstration purposes.

The system supports **four distinct user roles**, each with a dedicated dashboard and strictly enforced permissions:

| Role | Primary Responsibility |
|---|---|
| Customer | Account management, fund transfers, loan applications |
| Cashier | Process deposits/withdrawals, disburse salaries, send reports |
| Bank Admin | User management, admin transfers, interest rate configuration |
| Manager | Loan approval, employee promotion, analytics, inbox |

### Key Features

- Role-Based Access Control (RBAC) — every page is gated by role
- **Loan Interest Rate Engine** — 10-factor personalised rate calculated live as the form is filled
- Five account types: Savings, Current, Fixed Deposit, Recurring Deposit, Salary Account
- Seven loan types with purpose-based rate adjustments
- Five collateral types with differentiated security discounts
- bcrypt password hashing (salted, cost factor ≥ 12)
- Account lockout after 5 consecutive failed login attempts (15-minute cooldown)
- Session timeout after 10 minutes of inactivity
- Complete, tamper-evident audit log for all critical system events
- Real-time Plotly analytics dashboards for Admin and Manager
- Both **customer self-registration** and **admin-created accounts**

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Streamlit Frontend (app.py)                 │
│     Role-specific dashboards, forms, charts, navigation       │
└───────────────────────┬──────────────────────────────────────┘
                        │  Python function calls
        ┌───────────────┼──────────────────┐
        ▼               ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  models.py   │ │loan_engine.py│ │   database.py    │
│ All DB ops   │ │Rate & EMI    │ │ Connection pool  │
│ Auth, RBAC   │ │calculation   │ │ fetchone/execute │
└──────┬───────┘ └──────────────┘ └────────┬─────────┘
       └──────────────────┬────────────────┘
                          ▼
          ┌───────────────────────────────┐
          │   MySQL Database (local)      │
          │   bank_of_bharat              │
          │   9 tables, ACID transactions │
          └───────────────────────────────┘
```

The application is a **single-process, three-tier** system with no separate API server. Streamlit handles the presentation layer, Python modules contain all business logic, and MySQL provides ACID-compliant persistence.

---

## 3. Repository Structure

```
bank-of-bharat/
│
├── app.py                        # Main Streamlit application — all UI pages and routing
├── models.py                     # All database read/write operations
├── loan_engine.py                # Loan Interest Rate Engine (10-factor model + EMI)
├── database.py                   # MySQL connection helper — fetchone, fetchall, execute
├── init_db.py                    # One-time setup: runs schema, seeds default users
├── setup.sql                     # Full MySQL DDL — all CREATE TABLE statements
├── fix_columns.sql               # One-time migration for existing installations
├── requirements.txt              # Python dependencies
│
├── .streamlit/
│   └── config.toml               # Dark theme configuration (navy + gold)
│
└── BankOfBharat_SRS_v1_0.docx   # Software Requirements Specification
```

---

## 4. User Roles and Capabilities

### Customer
- Self-register on the login page, or be created by Bank Admin
- Open any of the 5 account types with applicable minimum balance
- View real-time balance, projected annual interest, and transaction history (last 50)
- Initiate fund transfers to any valid account number
- Apply for loans with a live interest rate preview panel (rate updates as each field is filled)
- Track the status, rate breakdown, and manager remarks for every loan application

### Cashier
- Look up any customer account by account ID and process cash deposits or withdrawals
- View per-employee paid/pending salary status for a selected month and disburse salary (duplicate disbursement for the same employee-month is blocked at database level)
- Compose and send operational reports to the Manager with a sent-message history
- View the full system-wide transaction history with filters

### Bank Admin
- Create user accounts for all roles — Customer, Cashier, Admin, **and Manager**
- Activate or deactivate accounts without deleting them; reset any user's password
- Filter and search users by role, status, name, or username
- Execute admin-initiated fund credits to customer accounts (every transfer is audit-logged with a mandatory narration)
- Configure base interest rates for all five account types
- View the analytics dashboard and full audit log

### Manager
- Review pending loan applications with full applicant details and an auto-run affordability check
- Approve or reject loans with mandatory remarks; approved loans are disbursed automatically to the customer's account in one atomic transaction
- Update employee grade, designation, salary, and role (promotion)
- View interest analytics: balance vs projected interest, loan portfolio by purpose, collateral risk distribution, and 30-day transaction volume
- Read, filter, and mark-as-read messages from Cashiers in the Manager Inbox
- View the full audit log

---

## 5. Loan Interest Rate Engine

**File:** `loan_engine.py`

The engine computes a personalised annual interest rate using an **additive model** on top of a fixed base rate. The result is clamped to a floor and a cap.

### 5.1 Rate Formula

$$R_{\text{raw}} = R_{\text{base}} + \Delta_{\text{age}} + \Delta_{\text{gender}} + \Delta_{\text{tenure}} + \Delta_{\text{employment}} + \Delta_{\text{CIBIL}} + \Delta_{\text{collateral}} + \Delta_{\text{loans}} + \Delta_{\text{LTI}} + \Delta_{\text{purpose}}$$

$$R_{\text{final}} = \max\!\left(6.00,\; \min\!\left(22.00,\; R_{\text{raw}}\right)\right)$$

where $R_{\text{base}} = 8.00\%$ p.a.

### 5.2 Factor Adjustment Table

| Factor | Condition | Δ (% p.a.) |
|---|---|:---:|
| **Base Rate** | Fixed | +8.00 |
| **Age** | < 25 yrs | +2.00 |
| | 25–35 yrs | 0.00 |
| | 36–50 yrs | +0.50 |
| | 51–60 yrs | +1.00 |
| | > 60 yrs | +2.00 |
| **Gender** | Female | −0.50 |
| | Male / Other | 0.00 |
| **Tenure** | ≤ 1 yr | 0.00 |
| | 2–3 yrs | +0.50 |
| | 4–5 yrs | +1.00 |
| | 6–10 yrs | +1.50 |
| | > 10 yrs | +2.00 |
| **Employment** | Employed | 0.00 |
| | Self-Employed | +1.00 |
| | Unemployed | +3.00 |
| **CIBIL Score** | ≥ 750 | −1.50 |
| | 650–749 | 0.00 |
| | 550–649 | +1.50 |
| | < 550 | +3.00 |
| **Collateral** | Gold | −1.50 |
| | Fixed Deposit | −1.25 |
| | Property / Real Estate | −1.00 |
| | Vehicle | −0.75 |
| | None | +2.00 |
| **Existing Loans** | 0 | 0.00 |
| | 1 | +0.50 |
| | ≥ 2 | +1.50 |
| **LTI Ratio** | $\text{LTI} < 2\times$ | 0.00 |
| | $2\times \leq \text{LTI} \leq 4\times$ | +0.50 |
| | $\text{LTI} > 4\times$ | +1.50 |
| **Loan Purpose** | Gold Loan | −0.75 |
| | Education | −0.50 |
| | Home | −0.25 |
| | Vehicle / Car | 0.00 |
| | Personal | +0.50 |
| | Business | +0.75 |
| | Vacation | +1.00 |

### 5.3 Loan-to-Income Ratio

$$\text{LTI} = \frac{P}{I_{\text{annual}}} = \frac{P}{I_{\text{monthly}} \times 12}$$

where $P$ is the principal and $I_{\text{monthly}}$ is the applicant's declared monthly income.

### 5.4 EMI Calculation

$$\text{EMI} = P \cdot \frac{r\,(1+r)^{n}}{(1+r)^{n} - 1}$$

| Symbol | Meaning |
|---|---|
| $P$ | Principal loan amount (₹) |
| $r$ | Monthly rate $= R_{\text{final}} / (100 \times 12)$ |
| $n$ | Total instalments $= \text{Tenure (yrs)} \times 12$ |

When $r = 0$: $\;\text{EMI} = P / n$

### 5.5 Total Interest and Total Payable

$$\text{Total Payable} = \text{EMI} \times n \qquad \text{Total Interest} = \text{Total Payable} - P$$

### 5.6 Affordability Check

A loan is only accepted if:

$$I_{\text{monthly}} \;\geq\; 3 \times \text{EMI}$$

Failing this condition blocks submission regardless of the computed rate.

### 5.7 Worked Example

> Female · Age 30 · Employed · Income ₹60,000/month  
> Loan ₹5,00,000 · Home Loan · 5 years · CIBIL 760 · Collateral: FD · 0 existing loans

$$R_{\text{raw}} = 8.00 + 0.00 - 0.50 + 1.00 + 0.00 - 1.50 - 1.25 + 0.00 + 0.00 - 0.25 = 5.50\%$$

$$R_{\text{final}} = \max(6.00,\;5.50) = \mathbf{6.00\%}\text{ p.a.}$$

$$r = \frac{6.00}{1200} = 0.005, \quad n = 60$$

$$\text{EMI} = 5{,}00{,}000 \times \frac{0.005 \times (1.005)^{60}}{(1.005)^{60} - 1} \approx \mathbf{₹9{,}666.44}$$

$$\text{Affordability: } 60{,}000 \;\geq\; 3 \times 9{,}666.44 = 28{,}999.32 \quad \checkmark$$

---

## 6. Function Reference

### `database.py` — Connection Utilities

| Function | Signature | Description |
|---|---|---|
| `get_connection()` | `() → Connection\|None` | Opens a fresh `mysql.connector` connection from `DB_CONFIG`. Shows an error and returns `None` on failure. |
| `fetchall()` | `(query, params) → list[dict]` | Executes a SELECT; returns all rows as list of dicts. |
| `fetchone()` | `(query, params) → dict\|None` | Executes a SELECT; returns the first row or `None`. |
| `execute()` | `(query, params) → int\|None` | Runs INSERT/UPDATE/DELETE; commits on success, rolls back on error, returns `lastrowid`. |
| `execute_transaction()` | `(queries: list[tuple]) → bool` | Executes multiple `(sql, params)` pairs atomically — all succeed or all roll back. Used for every financial operation. |

---

### `loan_engine.py` — Rate and EMI Engine

| Function | Signature | Description |
|---|---|---|
| `_calc_age()` | `(dob: date) → int` | Returns exact completed age in years, correctly handling whether the birthday has passed this year. |
| `calculate_rate()` | `(profile: LoanProfile) → RateBreakdown` | Applies the 10-factor additive model, clamps to [6%, 22%], computes EMI, total payable, and total interest. Returns a `RateBreakdown` dataclass containing every individual adjustment. |
| `affordability_check()` | `(income, emi) → (bool, str)` | Returns `(True, msg)` if $I_{\text{monthly}} \geq 3 \times \text{EMI}$, else `(False, reason_string)`. |

**Input dataclass — `LoanProfile`** (10 fields):
`date_of_birth`, `gender`, `employment_status`, `monthly_income`, `loan_amount`, `tenure_years`, `credit_score`, `collateral_type`, `existing_loans_count`, `loan_purpose`

**Output dataclass — `RateBreakdown`** (19 fields):
All 10 adjustment values + `raw_rate` + `final_rate` + `emi` + `age` + `lti_ratio` + `annual_income` + `total_payable` + `total_interest`

---

### `models.py` — Database Operations

#### Authentication

| Function | Description |
|---|---|
| `authenticate(username, password)` | Verifies credentials against the stored bcrypt hash. Tracks `failed_attempts`; locks account for 15 min after 5 failures. Resets counter on success. |
| `hash_password(plain)` | Wraps `bcrypt.hashpw` with an auto-generated salt. Plain text is never stored. |
| `verify_password(plain, hashed)` | Wraps `bcrypt.checkpw` for constant-time comparison — prevents timing attacks. |
| `log_audit(user_id, username, action, details)` | Inserts a row into `audit_log` with timestamp and IP for every critical event. |

#### User Management

| Function | Description |
|---|---|
| `create_user(...)` | Creates a `users` row and, for staff roles, a linked `employees` row. Rejects duplicate usernames. |
| `update_user_status(user_id, is_active)` | Activates or deactivates without deleting. |
| `reset_password(user_id, new_password)` | Re-hashes and updates; old password not required (admin action). |
| `get_all_users(role=None)` | Returns all users, optionally filtered by role. |
| `promote_employee(uid, grade, designation, salary, role)` | Updates `employees` table; optionally updates `role` in `users` if a role change is specified. |

#### Account Operations

| Function | Description |
|---|---|
| `open_account(user_id, account_type, initial_deposit, ...)` | Creates an account, looks up the current base rate from `interest_rates`, optionally sets `maturity_date` for FD/RD, and records the opening deposit as the first transaction. |
| `get_customer_accounts(user_id)` | Returns all accounts for a customer. |
| `get_account_with_owner(account_id)` | JOINs `accounts` with `users`; returns account details plus the holder's name and username. Used to verify destination accounts during transfers. |

#### Transactions

All financial mutations use `execute_transaction()` — atomicity is guaranteed.

| Function | Description |
|---|---|
| `deposit(to_account, amount, narration, processed_by)` | Atomically increments balance and inserts a `Deposit` record in one transaction. |
| `withdraw(from_account, amount, narration, processed_by)` | Validates sufficient balance, then atomically decrements balance and inserts a `Withdrawal` record. |
| `transfer(from_account, to_account, amount, ...)` | Atomically decrements source, increments destination, and inserts one `Transfer` record. All three operations commit or none do. |
| `admin_credit(to_account, amount, narration, admin_id)` | Credits a customer account without a corresponding debit (admin-funded injection). Logged with `Admin Transfer` type. |

#### Loans

| Function | Description |
|---|---|
| `submit_loan(...)` | Stores all 17 loan fields including the pre-computed `interest_rate` and `emi`. Status defaults to `Pending`. |
| `decide_loan(loan_id, decision, remarks, manager_id)` | Sets status to `Approved` or `Rejected`. On approval: atomically credits `loan_amount` to the disbursement account, inserts a `Loan Disbursement` transaction, and sets status to `Disbursed` — all in one transaction. |

#### Salary

| Function | Description |
|---|---|
| `disburse_salary(emp_uid, cashier_uid, amount, month_year)` | Inserts into `salary_disbursements`. The DB-level `UNIQUE(employee_user_id, month_year)` constraint blocks any duplicate, even if two cashiers try simultaneously. |

#### Analytics

| Function | Description |
|---|---|
| `get_bank_summary()` | Returns 6 KPIs: total customers, active accounts, total balance, pending loans, total loan portfolio, today's transaction count. All computed in one pass via 6 SQL aggregates. |
| `get_transaction_trend(days)` | Returns daily count and volume for the last N days — feeds the line/area chart. |
| `get_account_type_distribution()` | Returns count and total balance grouped by account type — feeds pie and bar charts. |
| `get_loan_by_collateral()` | Returns count, total amount, and average rate grouped by collateral type — feeds the risk distribution chart. |

---

## 7. Database Schema

All 9 tables in the `bank_of_bharat` MySQL database:

| Table | Description |
|---|---|
| `users` | All user accounts across all roles. Stores bcrypt hash, lockout state, and self-registered flag. |
| `employees` | Extended profile for Cashier, Admin, and Manager — grade, designation, salary, department. |
| `accounts` | Customer bank accounts for all 5 types. Stores balance, interest rate, status, and optional maturity/instalment fields. |
| `transactions` | Every financial event — Deposit, Withdrawal, Transfer, Salary, Loan Disbursement, Admin Transfer. |
| `loans` | Loan applications with all 17 data fields, computed rate, EMI, status, and manager remarks. |
| `interest_rates` | Base rates per account type — admin-configurable, timestamped with the last updater. |
| `salary_disbursements` | Monthly salary records. `UNIQUE(employee_user_id, month_year)` prevents duplicate payments at DB level. |
| `messages` | Cashier-to-Manager inbox — subject, body, read status. |
| `audit_log` | Append-only event log for all critical actions with user, action, details, IP, and timestamp. |

**Key design decisions:**
- `execute_transaction()` wraps all multi-table financial writes in a single MySQL transaction — no partial updates are possible
- Duplicate salary prevention is enforced at both the application layer and with a database-level `UNIQUE` constraint
- `account_id`, `transaction_id`, and `loan_id` use a 12-digit timestamp prefix plus 4 random digits — format `BOB/TXN/LN + YYMMDDHHMMSS + NNNN`
- All password storage uses bcrypt — the plain-text password is never written to disk

---

## 8. Sample Users and Credentials

These accounts are created automatically by `python init_db.py`:

| Username | Password | Role | Full Name | Notes |
|---|---|---|---|---|
| `admin` | `Admin@123` | Bank Admin | System Administrator | Can create all roles including Manager |
| `manager` | `Manager@123` | Manager | Rajesh Kumar | Approves loans, promotes staff, views analytics |
| `cashier1` | `Cashier@123` | Cashier | Priya Sharma | Processes transactions, disburses salary |
| `cashier2` | `Cashier@123` | Cashier | Vikram Mehta | Second cashier — test parallel salary workflows |
| `customer1` | `Customer@123` | Customer | Amit Patel | Pre-seeded with a Savings and a Salary Account |
| `customer2` | `Customer@123` | Customer | Sunita Devi | No accounts — use to test the account-opening flow |

> **Change all default passwords before any non-demonstration deployment.**

`customer1` is pre-seeded with two accounts whose IDs are generated at `init_db.py` runtime (timestamp-based). Log in as `customer1` or as `admin` → Manage Users to see the exact IDs.

---

## 9. Installation and Setup

### Prerequisites

| Requirement | Minimum Version | Check Command |
|---|---|---|
| Python | 3.11 | `python --version` |
| MySQL Server | 8.0 | `mysql --version` |
| pip | Latest | `pip --version` |
| Node.js (optional) | 18+ | Only needed to regenerate the SRS `.docx` |

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/<your-username>/bank-of-bharat.git
cd bank-of-bharat
```

---

### Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

> On some Linux systems: `pip install --break-system-packages -r requirements.txt`

Dependencies installed:

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.32.0 | Web UI framework |
| `mysql-connector-python` | ≥ 8.3.0 | MySQL database driver |
| `bcrypt` | ≥ 4.1.2 | Password hashing |
| `pandas` | ≥ 2.2.0 | Tabular data display |
| `plotly` | ≥ 5.20.0 | Interactive charts |

---

### Step 3 — Configure MySQL Credentials

Open **`database.py`** and update `DB_CONFIG`:

```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "YOUR_MYSQL_PASSWORD",   # ← change this
    "database": "bank_of_bharat",
}
```

Open **`init_db.py`** and update the constants at the top:

```python
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = "YOUR_MYSQL_PASSWORD"          # ← change this
```

---

### Step 4 — Initialise the Database

Run this **once only**. It creates the database, all 9 tables, seeds the default users, and creates sample accounts for `customer1`.

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
    Created 'admin'     (ID=1, role=admin)
    Created 'manager'   (ID=2, role=manager)
    Created 'cashier1'  (ID=3, role=cashier)
    Created 'cashier2'  (ID=4, role=cashier)
    Created 'customer1' (ID=5, role=customer)
    Created 'customer2' (ID=6, role=customer)
    Sample account BOB... (Savings) for customer1
    Sample account BOB... (Salary Account) for customer1
==============================================================
   Database initialised successfully!
==============================================================
```

> **Getting a "Data too long for column account_id" error?**  
> This means you are running an older schema. Run the one-time column fix first:
> ```bash
> mysql -u root -p bank_of_bharat < fix_columns.sql
> ```
> Then re-run `python init_db.py`.

---

### Step 5 — Verify the Theme Config

Confirm that `.streamlit/config.toml` exists with the following content (it is included in the repository):

```toml
[theme]
base                     = "dark"
primaryColor             = "#c9a84c"
backgroundColor          = "#0f1729"
secondaryBackgroundColor = "#1a2744"
textColor                = "#e8edf5"
font                     = "sans serif"
```

---

## 10. Running the Application

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** in your default browser.  
Stop the server: `Ctrl + C`.

### Recommended Testing Workflow

A suggested sequence to exercise all four roles end-to-end:

1. **Admin** → Create a new customer account
2. **Customer (new)** → Self-register, open a Savings account, apply for a Home Loan
3. **Cashier1** → Deposit cash into a customer account; disburse salary for all staff for the current month
4. **Cashier1** → Send a daily cash summary report to the Manager
5. **Manager** → Open Manager Inbox, read the cashier report; go to Loan Approval and approve the loan with remarks
6. **Customer** → Check Loan Status — verify the status shows "Disbursed" and the balance has increased
7. **Admin** → Open Audit Log — verify all events from steps 1–6 are recorded

---

## 11. Project Documents

The full Software Requirements Specification for this project is in the `docs/` folder:

```
BankOfBharat_SRS_v1_0.docx
```
[SRS Document](https://github.com/vijollobo/OnlineBankingSystem/blob/main/BankOfBharat_SRS_v1_0.docx)

This SRS is written specifically for Bank of Bharat and covers:
- All 18 use cases across 4 roles
- Complete functional requirements with MoSCoW priority ratings
- Non-functional requirements (security, reliability, usability, maintainability)
- The full Loan Interest Rate Engine specification with mathematical formulae
- Database schema overview
- Sample credentials and revision history

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit 1.32+ |
| Backend Logic | Python 3.11 |
| Database | MySQL 8.0 |
| DB Driver | mysql-connector-python |
| Password Security | bcrypt (salted) |
| Data Manipulation | pandas |
| Charts | Plotly Express + Graph Objects |
| Theme | Streamlit dark theme via `.streamlit/config.toml` |
| Custom Styling | CSS injected via `st.markdown` (custom HTML cards only) |

---

## License

This project is intended for **educational and demonstration purposes only**. It is not suitable for production banking use.

---

*Bank of Bharat*
