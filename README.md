# 🏦 Bank of Bharat — Online Banking System
### College Demonstration Project | Built with Python + Streamlit + MySQL

---

## 📋 Project Overview

A full-featured multi-role online banking system with:
- **4 User Roles**: Customer, Cashier, Bank Admin, Manager
- **Loan Interest Rate Engine** (personalised rates based on 9 factors)
- **Real-time dashboards** with charts and analytics
- **Audit logging** for all system events
- **Role-based access control (RBAC)**

---

## 🗂️ File Structure

```
bank_of_bharat/
├── app.py               # Main Streamlit application
├── database.py          # MySQL connection utilities
├── loan_engine.py       # Loan Interest Rate Engine (SRS §3.2.5)
├── models.py            # All database operations
├── init_db.py           # One-time DB setup script
├── setup.sql            # MySQL schema
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
- Python 3.11+
- MySQL Server (local)
- pip

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure MySQL
Open `database.py` and update:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_PASSWORD",  # ← change this
    "database": "bank_of_bharat",
}
```
Also update the same credentials in `init_db.py`.

### 4. Initialize the Database (run ONCE)
```bash
python init_db.py
```
This will:
- Create the `bank_of_bharat` database
- Create all tables
- Seed default users

### 5. Run the App
```bash
streamlit run app.py
```
Open: http://localhost:8501

---

## 🔑 Default Login Credentials

| Username   | Password     | Role     |
|------------|--------------|----------|
| admin      | Admin@123    | Admin    |
| manager    | Manager@123  | Manager  |
| cashier1   | Cashier@123  | Cashier  |
| customer1  | Customer@123 | Customer |
| customer2  | Customer@123 | Customer |

> **Change all passwords** after first login in a real deployment.

---

## 🎯 Features by Role

### 👤 Customer
- View account dashboard with balance summary
- Open new accounts (Savings, Current, FD, RD)
- Fund transfers to any account
- View transaction history (last 50 per account)
- Apply for loans with live interest rate preview
- Track loan application status

### 💼 Cashier
- Process deposits and withdrawals for customers
- Disburse monthly employee salaries (duplicate prevention)
- Send operational reports to Manager
- View full transaction history

### 🛡️ Bank Admin
- Create/edit/activate/deactivate all user accounts
- Admin fund transfers to customer accounts
- Configure interest rates for all account types
- View analytics dashboard
- Browse full audit log

### 👔 Manager
- Review and approve/reject loan applications (with disbursement)
- Promote employees (grade, designation, salary)
- View interest analytics and portfolio charts
- Read reports from Cashiers
- Browse audit log

---

## 🏦 Loan Interest Rate Engine

Personalised additive model (SRS §3.2.5):

| Factor            | Range       | Adjustment |
|-------------------|-------------|------------|
| Base Rate         | Fixed       | +8.00%     |
| Age < 25 or > 60  | —           | +2.00%     |
| Gender (Female)   | —           | -0.50%     |
| Tenure > 10 yrs   | —           | +2.00%     |
| Unemployed        | —           | +3.00%     |
| CIBIL ≥ 750       | —           | -1.50%     |
| No Collateral     | —           | +1.00%     |
| ≥2 Existing Loans | —           | +1.50%     |
| LTI > 4×          | —           | +1.50%     |

**Floor: 6.00% | Cap: 22.00%**

EMI = P × r × (1+r)^n / ((1+r)^n − 1)

---

## 📌 Account Minimum Balances

| Account Type      | Minimum     |
|-------------------|-------------|
| Savings           | ₹500        |
| Current           | ₹1,000      |
| Fixed Deposit     | ₹5,000      |
| Recurring Deposit | ₹500/month  |

---

## 🔒 Security Features

- bcrypt password hashing (salted)
- Account lockout after 5 failed attempts (15 min)
- Session timeout after 10 minutes of inactivity
- Full audit log for all critical actions
- RBAC: each role sees only its permitted modules

---

*Bank of Bharat | College Demonstration Project | 2026*
