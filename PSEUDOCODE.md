# Bank of Bharat — Backend Pseudocode
> Style: Code-like (Python-indented) · Scope: `database.py`, `loan_engine.py`, `models.py`

---

## 1. database.py

```python
CONST DB_CONFIG = { host, port, user, password, database }

def get_connection():
    return mysql.connect(DB_CONFIG)  # or None on failure

def fetchall(query, params):
    conn = get_connection()
    return conn.cursor(dict=True).execute(query, params).fetchall()

def fetchone(query, params):
    return fetchall(query, params)[0]  # or None

def execute(query, params):
    conn = get_connection()
    conn.cursor().execute(query, params)
    conn.commit()
    return cursor.lastrowid          # rollback on error

def execute_transaction([(sql, params), ...]):
    # Executes all statements atomically
    # If any fails → rollback ALL, raise error
    for sql, params in queries:
        cursor.execute(sql, params)
    conn.commit()
```

---

## 2. loan_engine.py

```python
BASE_RATE  = 8.00
RATE_FLOOR = 6.00
RATE_CAP   = 22.00

def calc_age(dob):
    age = today.year - dob.year
    if birthday not yet passed this year: age -= 1
    return age

def calculate_rate(profile):
    age           = calc_age(profile.dob)
    annual_income = profile.monthly_income * 12
    lti_ratio     = profile.loan_amount / annual_income

    age_adj = {<25: +2.00, 25-35: 0.00, 36-50: +0.50,
                51-60: +1.00, >60: +2.00}[age]

    gender_adj     = -0.50 if Female else 0.00

    tenure_adj = {≤1yr: 0.00, 2-3yr: +0.50, 4-5yr: +1.00,
                  6-10yr: +1.50, >10yr: +2.00}[tenure]

    employment_adj = {Employed: 0.00, Self-Employed: +1.00,
                      Unemployed: +3.00}[status]

    credit_adj = {≥750: -1.50, 650-749: 0.00,
                  550-649: +1.50, <550: +3.00}[cibil]

    collateral_adj = {Gold: -1.50, FD: -1.25, Property: -1.00,
                      Vehicle: -0.75, None: +2.00}[type]

    loans_adj = {0: 0.00, 1: +0.50, ≥2: +1.50}[existing_loans]

    lti_adj = {<2x: 0.00, 2-4x: +0.50, >4x: +1.50}[lti_ratio]

    purpose_adj = {Gold Loan: -0.75, Education: -0.50, Home: -0.25,
                   Vehicle: 0.00, Personal: +0.50,
                   Business: +0.75, Vacation: +1.00}[purpose]

    raw_rate   = BASE_RATE + sum(all adjustments)
    final_rate = clamp(raw_rate, RATE_FLOOR, RATE_CAP)

    # EMI = P × r(1+r)^n / ((1+r)^n − 1)
    r   = final_rate / 100 / 12
    n   = tenure_years * 12
    emi = P * r * (1+r)^n / ((1+r)^n - 1)   # if r=0: emi = P/n

    total_payable  = emi * n
    total_interest = total_payable - P

    return RateBreakdown(all adjustments, final_rate,
                         emi, total_payable, total_interest)

def affordability_check(income, emi):
    return income >= 3 * emi    # True = passes, False = rejected
```

---

## 3. models.py

### 3.1 ID Generators & Password

```python
def new_account_id():  return "BOB" + short_timestamp() + rand(4)
def new_txn_id():      return "TXN" + short_timestamp() + rand(4)
def new_loan_id():     return "LN"  + short_timestamp() + rand(4)

def hash_password(plain):   return bcrypt.hashpw(plain, salt)
def verify_password(p, h):  return bcrypt.checkpw(p, h)
```

---

### 3.2 Authentication

```python
def authenticate(username, password):
    user = fetchone("SELECT * FROM users WHERE username=?", username)

    if not user:                         return None, "Invalid credentials"
    if now() < user.locked_until:        return None, "Account locked N min"
    if not user.is_active:               return None, "Account deactivated"

    if not verify_password(password, user.hash):
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.locked_until = now() + 15min
        return None, f"Wrong password. {5 - attempts} left"

    user.failed_attempts = 0             # reset on success
    return user, "Login successful"

def log_audit(user_id, username, action, details):
    INSERT INTO audit_log(user_id, username, action, details, ip, created_at)
```

---

### 3.3 User Management

```python
def create_user(username, password, role, ...):
    if username_exists: return False, "Username taken"
    uid = INSERT INTO users(username, bcrypt_hash, role, ...)
    if role in [cashier, admin, manager]:
        INSERT INTO employees(uid, code, dept, grade, salary, ...)
    return True, f"User created (ID={uid})"

def update_user_status(user_id, is_active):
    UPDATE users SET is_active=? WHERE user_id=?

def reset_password(user_id, new_password):
    UPDATE users SET password_hash=bcrypt(new_password)

def promote_employee(user_id, grade, designation, salary, new_role=None):
    UPDATE employees SET grade, designation, salary WHERE user_id=?
    if new_role: UPDATE users SET role=new_role
```

---

### 3.4 Accounts

```python
MIN_BALANCE = {Savings:500, Current:1000, FD:5000, RD:500, Salary:0}

def open_account(user_id, account_type, deposit, tenure=None):
    if deposit < MIN_BALANCE[account_type]:
        return False, "Minimum deposit is ₹X", None

    rate   = fetchone("SELECT rate FROM interest_rates WHERE type=?")
    acc_id = new_account_id()

    INSERT INTO accounts(acc_id, user_id, type, deposit, rate, today, ...)
    INSERT INTO transactions(new_txn_id(), to=acc_id, "Opening Deposit")
    return True, "Account opened", acc_id

def get_customer_accounts(user_id):
    return fetchall("SELECT * FROM accounts WHERE user_id=?")

def get_account_with_owner(account_id):
    return fetchone("SELECT accounts.*, users.full_name
                     FROM accounts JOIN users ... WHERE account_id=?")
```

---

### 3.5 Transactions

```python
# All use execute_transaction() — atomic, rollback on failure

def deposit(to_acc, amount, narration, by):
    validate: account exists, Active, amount > 0
    txn_id = new_txn_id()
    execute_transaction([
        UPDATE accounts SET balance += amount WHERE id=to_acc,
        INSERT INTO transactions(txn_id, to=to_acc, amount, "Deposit")
    ])

def withdraw(from_acc, amount, narration, by):
    validate: exists, Active, amount > 0, balance >= amount
    txn_id = new_txn_id()
    execute_transaction([
        UPDATE accounts SET balance -= amount WHERE id=from_acc,
        INSERT INTO transactions(txn_id, from=from_acc, amount, "Withdrawal")
    ])

def transfer(from_acc, to_acc, amount, narration, by):
    validate: from ≠ to, both exist, both Active, balance >= amount
    txn_id = new_txn_id()
    execute_transaction([
        UPDATE accounts SET balance -= amount WHERE id=from_acc,
        UPDATE accounts SET balance += amount WHERE id=to_acc,
        INSERT INTO transactions(txn_id, from, to, amount, "Transfer")
    ])

def admin_credit(to_acc, amount, narration, admin_id):
    validate: account exists, Active
    execute_transaction([
        UPDATE accounts SET balance += amount,
        INSERT INTO transactions(..., "Admin Transfer")
    ])
```

---

### 3.6 Loans

```python
def submit_loan(user_id, disb_account, full_name, dob, gender,
                employment, income, amount, purpose, tenure,
                cibil, collateral, existing_loans, kyc,
                interest_rate, emi):
    loan_id = new_loan_id()
    INSERT INTO loans(loan_id, user_id, all fields..., status="Pending")
    return True, f"Loan {loan_id} submitted"

def decide_loan(loan_id, decision, remarks, manager_id):
    # decision ∈ {"Approved", "Rejected"}
    UPDATE loans SET status=decision, remarks, approved_by, decided_at=NOW()
    WHERE loan_id=? AND status="Pending"

    if decision == "Approved":
        loan = fetchone loans WHERE loan_id=?
        execute_transaction([
            UPDATE accounts SET balance += loan.amount
                WHERE id=loan.disbursement_account,
            INSERT INTO transactions(..., "Loan Disbursement")
        ])
        UPDATE loans SET status="Disbursed"
```

---

### 3.7 Salary

```python
def disburse_salary(emp_id, cashier_id, amount, month_year):
    # month_year = "YYYY-MM"
    if record exists for (emp_id, month_year):
        return False, "Already disbursed"
    INSERT INTO salary_disbursements(emp_id, cashier_id, amount, month_year)
    # DB UNIQUE(emp_id, month_year) blocks concurrent duplicates too
```

---

### 3.8 Messages & Interest Rates

```python
def send_message(sender_id, subject, body):
    INSERT INTO messages(sender_id, subject, body, is_read=False)

def mark_message_read(message_id):
    UPDATE messages SET is_read=True WHERE message_id=?

def update_interest_rate(account_type, rate, updated_by):
    UPDATE interest_rates SET rate=?, updated_by=?, updated_at=NOW()
```

---

### 3.9 Analytics

```python
def get_bank_summary():
    return {
        total_customers:    COUNT users WHERE role=customer AND active,
        total_accounts:     COUNT accounts WHERE status=Active,
        total_balance:      SUM   accounts.balance WHERE Active,
        pending_loans:      COUNT loans WHERE status=Pending,
        total_loans_amount: SUM   loans.loan_amount WHERE Approved/Disbursed,
        transactions_today: COUNT transactions WHERE DATE=today
    }

def get_transaction_trend(days):
    return GROUP BY DATE(created_at) → {date, count, total_amount}
           WHERE created_at >= NOW() - N days

def get_account_type_distribution():
    return GROUP BY account_type → {type, count, total_balance}

def get_loan_by_collateral():
    return GROUP BY collateral_type → {type, count, total_amount, avg_rate}
```

---

## Data Flow Summary

```
LOGIN:
  authenticate() → verify_password() → fetchone(users)
                 → execute(UPDATE failed_attempts)
                 → return user

FUND TRANSFER:
  transfer() → validate both accounts
             → execute_transaction([debit, credit, insert txn])

LOAN APPLICATION:
  calculate_rate(profile) → affordability_check(income, emi)
  → submit_loan() → INSERT loans (status=Pending)

LOAN APPROVAL:
  decide_loan("Approved") → execute_transaction([
      credit disbursement account,
      insert Loan Disbursement txn,
      update loan status = Disbursed
  ])

SALARY DISBURSE:
  disburse_salary() → check duplicate (app + DB constraint)
                    → INSERT salary_disbursements
```
