"""
models.py  –  All database operations for Bank of Bharat (v2)
"""
import random, string
from datetime import datetime, date, timedelta
import bcrypt
from database import fetchall, fetchone, execute, execute_transaction

# ── ID generators ─────────────────────────────────────────────────────────────
def _rand(n=6): return ''.join(random.choices(string.digits, k=n))
def _ts():      return datetime.now().strftime("%Y%m%d%H%M%S")
def _short_ts(): return datetime.now().strftime("%y%m%d%H%M%S")   # 12 chars
def new_account_id(): return f"BOB{_short_ts()}{_rand(4)}"   # 3+12+4 = 19 ✓
def new_txn_id():     return f"TXN{_short_ts()}{_rand(4)}"   # 3+12+4 = 19 ✓
def new_loan_id():    return f"LN{_short_ts()}{_rand(4)}"    # 2+12+4 = 18 ✓

def hash_password(plain): return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
def verify_password(plain, hashed): return bcrypt.checkpw(plain.encode(), hashed.encode())

# ══════════════════════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════════════════════
def get_user_by_username(username):
    return fetchone("SELECT * FROM users WHERE username=%s", (username,))

def authenticate(username, password):
    user = get_user_by_username(username)
    if not user:
        return None, "Invalid username or password."
    if user["locked_until"] and datetime.now() < user["locked_until"]:
        rem = int((user["locked_until"] - datetime.now()).total_seconds() / 60) + 1
        return None, f"Account locked. Try again in {rem} minute(s)."
    if not user["is_active"]:
        return None, "Your account has been deactivated. Contact Bank Admin."
    if not verify_password(password, user["password_hash"]):
        new_fails = user["failed_attempts"] + 1
        if new_fails >= 5:
            locked = datetime.now() + timedelta(minutes=15)
            execute("UPDATE users SET failed_attempts=%s, locked_until=%s WHERE user_id=%s",
                    (new_fails, locked, user["user_id"]))
            return None, "Too many failed attempts. Account locked for 15 minutes."
        execute("UPDATE users SET failed_attempts=%s WHERE user_id=%s",
                (new_fails, user["user_id"]))
        return None, f"Invalid password. {5 - new_fails} attempt(s) remaining."
    execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE user_id=%s",
            (user["user_id"],))
    return user, "Login successful."

def log_audit(user_id, username, action, details, ip="127.0.0.1"):
    execute("INSERT INTO audit_log (user_id,username,action,details,ip_address) VALUES(%s,%s,%s,%s,%s)",
            (user_id, username, action, details, ip))

# ══════════════════════════════════════════════════════════════════════════════
# USERS
# ══════════════════════════════════════════════════════════════════════════════
def create_user(username, password, role, full_name, email, phone, address, dob, gender,
                emp_code=None, dept=None, grade=None, designation=None,
                salary=0.0, joining_date=None, self_registered=False):
    if get_user_by_username(username):
        return False, f"Username '{username}' already exists."
    pw_hash = hash_password(password)
    try:
        uid = execute(
            """INSERT INTO users
               (username,password_hash,role,full_name,email,phone,address,
                date_of_birth,gender,self_registered)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (username, pw_hash, role, full_name, email, phone, address, dob, gender,
             1 if self_registered else 0))
        if role in ("cashier","admin","manager"):
            execute(
                """INSERT INTO employees(user_id,employee_code,department,grade,
                   designation,salary,joining_date) VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                (uid, emp_code, dept, grade, designation, salary, joining_date))
        return True, f"Account created for '{username}' (ID: {uid})."
    except Exception as e:
        return False, str(e)

def update_user_status(user_id, is_active):
    execute("UPDATE users SET is_active=%s WHERE user_id=%s", (is_active, user_id))

def update_user(user_id, full_name, email, phone, address):
    execute("UPDATE users SET full_name=%s,email=%s,phone=%s,address=%s WHERE user_id=%s",
            (full_name, email, phone, address, user_id))

def get_all_users(role=None):
    if role:
        return fetchall("SELECT * FROM users WHERE role=%s ORDER BY created_at DESC", (role,))
    return fetchall("SELECT * FROM users ORDER BY created_at DESC")

def get_user_by_id(uid):
    return fetchone("SELECT * FROM users WHERE user_id=%s", (uid,))

def reset_password(user_id, new_password):
    execute("UPDATE users SET password_hash=%s WHERE user_id=%s",
            (hash_password(new_password), user_id))

# ══════════════════════════════════════════════════════════════════════════════
# EMPLOYEES
# ══════════════════════════════════════════════════════════════════════════════
def get_employee(user_id):
    return fetchone(
        """SELECT e.*,u.full_name,u.role,u.is_active,u.email,u.phone,
                  u.date_of_birth,u.gender,u.username
           FROM employees e JOIN users u ON e.user_id=u.user_id
           WHERE e.user_id=%s""", (user_id,))

def get_all_employees():
    return fetchall(
        """SELECT e.*,u.full_name,u.role,u.is_active,u.username
           FROM employees e JOIN users u ON e.user_id=u.user_id
           WHERE u.is_active=1 ORDER BY u.full_name""")

def promote_employee(user_id, new_grade, new_designation, new_salary, new_role=None):
    try:
        execute("UPDATE employees SET grade=%s,designation=%s,salary=%s WHERE user_id=%s",
                (new_grade, new_designation, new_salary, user_id))
        if new_role:
            execute("UPDATE users SET role=%s WHERE user_id=%s", (new_role, user_id))
        return True, "Employee promoted successfully."
    except Exception as e:
        return False, str(e)

# ══════════════════════════════════════════════════════════════════════════════
# ACCOUNTS
# ══════════════════════════════════════════════════════════════════════════════
MIN_BALANCE = {
    "Savings": 500, "Current": 1000,
    "Fixed Deposit": 5000, "Recurring Deposit": 500, "Salary Account": 0,
}

def open_account(user_id, account_type, initial_deposit,
                 tenure_months=None, monthly_installment=None):
    min_bal = MIN_BALANCE.get(account_type, 500)
    if initial_deposit < min_bal:
        return False, f"Minimum opening deposit for {account_type} is ₹{min_bal:,}.", None
    rate_row = fetchone("SELECT rate FROM interest_rates WHERE account_type=%s", (account_type,))
    rate = rate_row["rate"] if rate_row else 0.0
    acc_id = new_account_id()
    mat_date = None
    if tenure_months and account_type in ("Fixed Deposit","Recurring Deposit"):
        mat_date = (datetime.now() + timedelta(days=tenure_months*30)).date()
    try:
        execute(
            """INSERT INTO accounts
               (account_id,user_id,account_type,balance,interest_rate,opening_date,
                maturity_date,monthly_installment,tenure_months)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (acc_id, user_id, account_type, initial_deposit, rate,
             date.today(), mat_date, monthly_installment, tenure_months))
        txn_id = new_txn_id()
        execute(
            """INSERT INTO transactions
               (transaction_id,to_account,amount,transaction_type,narration,status)
               VALUES(%s,%s,%s,'Deposit','Account Opening Deposit','Success')""",
            (txn_id, acc_id, initial_deposit))
        return True, f"Account {acc_id} opened successfully.", acc_id
    except Exception as e:
        return False, str(e), None

def get_customer_accounts(user_id):
    return fetchall("SELECT * FROM accounts WHERE user_id=%s ORDER BY opening_date DESC", (user_id,))

def get_account(account_id):
    return fetchone("SELECT * FROM accounts WHERE account_id=%s", (account_id,))

def get_account_with_owner(account_id):
    return fetchone(
        """SELECT a.*,u.full_name,u.username
           FROM accounts a JOIN users u ON a.user_id=u.user_id
           WHERE a.account_id=%s""", (account_id,))

def update_account_status(account_id, status):
    execute("UPDATE accounts SET status=%s WHERE account_id=%s", (status, account_id))

# ══════════════════════════════════════════════════════════════════════════════
# TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════
def deposit(to_account, amount, narration, processed_by=None):
    acc = get_account(to_account)
    if not acc:      return False, "Account not found."
    if acc["status"] != "Active": return False, f"Account is {acc['status']}."
    if amount <= 0:  return False, "Amount must be positive."
    txn_id = new_txn_id()
    try:
        execute_transaction([
            ("UPDATE accounts SET balance=balance+%s WHERE account_id=%s", (amount, to_account)),
            ("""INSERT INTO transactions(transaction_id,to_account,amount,transaction_type,
                narration,processed_by) VALUES(%s,%s,%s,'Deposit',%s,%s)""",
             (txn_id, to_account, amount, narration, processed_by)),
        ])
        return True, f"₹{amount:,.2f} deposited. Ref: {txn_id}"
    except Exception as e:
        return False, str(e)

def withdraw(from_account, amount, narration, processed_by=None):
    acc = get_account(from_account)
    if not acc:      return False, "Account not found."
    if acc["status"] != "Active": return False, f"Account is {acc['status']}."
    if amount <= 0:  return False, "Amount must be positive."
    if acc["balance"] < amount:
        return False, f"Insufficient balance. Available: ₹{acc['balance']:,.2f}"
    txn_id = new_txn_id()
    try:
        execute_transaction([
            ("UPDATE accounts SET balance=balance-%s WHERE account_id=%s", (amount, from_account)),
            ("""INSERT INTO transactions(transaction_id,from_account,amount,transaction_type,
                narration,processed_by) VALUES(%s,%s,%s,'Withdrawal',%s,%s)""",
             (txn_id, from_account, amount, narration, processed_by)),
        ])
        return True, f"₹{amount:,.2f} withdrawn. Ref: {txn_id}"
    except Exception as e:
        return False, str(e)

def transfer(from_account, to_account, amount, narration,
             txn_type="Transfer", processed_by=None):
    if from_account == to_account:
        return False, "Source and destination cannot be the same."
    src = get_account(from_account); dst = get_account(to_account)
    if not src: return False, "Source account not found."
    if not dst: return False, "Destination account not found."
    if src["status"] != "Active": return False, f"Source account is {src['status']}."
    if dst["status"] != "Active": return False, f"Destination account is {dst['status']}."
    if amount <= 0: return False, "Amount must be positive."
    if src["balance"] < amount:
        return False, f"Insufficient balance. Available: ₹{src['balance']:,.2f}"
    txn_id = new_txn_id()
    try:
        execute_transaction([
            ("UPDATE accounts SET balance=balance-%s WHERE account_id=%s", (amount, from_account)),
            ("UPDATE accounts SET balance=balance+%s WHERE account_id=%s", (amount, to_account)),
            ("""INSERT INTO transactions(transaction_id,from_account,to_account,amount,
                transaction_type,narration,processed_by) VALUES(%s,%s,%s,%s,%s,%s,%s)""",
             (txn_id, from_account, to_account, amount, txn_type, narration, processed_by)),
        ])
        return True, f"₹{amount:,.2f} transferred. Ref: {txn_id}"
    except Exception as e:
        return False, str(e)

def admin_credit(to_account, amount, narration, admin_id):
    acc = get_account(to_account)
    if not acc:      return False, "Account not found."
    if acc["status"] != "Active": return False, f"Account is {acc['status']}."
    txn_id = new_txn_id()
    try:
        execute_transaction([
            ("UPDATE accounts SET balance=balance+%s WHERE account_id=%s", (amount, to_account)),
            ("""INSERT INTO transactions(transaction_id,to_account,amount,transaction_type,
                narration,processed_by) VALUES(%s,%s,%s,'Admin Transfer',%s,%s)""",
             (txn_id, to_account, amount, narration, admin_id)),
        ])
        return True, f"₹{amount:,.2f} credited. Ref: {txn_id}"
    except Exception as e:
        return False, str(e)

def get_account_transactions(account_id, limit=50):
    return fetchall(
        """SELECT * FROM transactions
           WHERE from_account=%s OR to_account=%s
           ORDER BY created_at DESC LIMIT %s""",
        (account_id, account_id, limit))

def get_all_transactions(limit=100):
    return fetchall("SELECT * FROM transactions ORDER BY created_at DESC LIMIT %s", (limit,))

def get_recent_transactions_for_cashier(limit=50):
    return fetchall(
        """SELECT t.*,u.full_name as processor_name
           FROM transactions t LEFT JOIN users u ON t.processed_by=u.user_id
           ORDER BY t.created_at DESC LIMIT %s""", (limit,))

# ══════════════════════════════════════════════════════════════════════════════
# LOANS
# ══════════════════════════════════════════════════════════════════════════════
def submit_loan(user_id, disbursement_account, full_name, dob, gender,
                employment_status, monthly_income, loan_amount, loan_purpose,
                tenure_years, credit_score, collateral_type, existing_loans,
                kyc_ref, interest_rate, emi):
    loan_id = new_loan_id()
    try:
        execute(
            """INSERT INTO loans(loan_id,user_id,disbursement_account,full_name,date_of_birth,
               gender,employment_status,monthly_income,loan_amount,loan_purpose,tenure_years,
               credit_score,collateral_type,existing_loans_count,kyc_reference,
               computed_interest_rate,emi_amount)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (loan_id, user_id, disbursement_account, full_name, dob, gender,
             employment_status, monthly_income, loan_amount, loan_purpose, tenure_years,
             credit_score, collateral_type, existing_loans, kyc_ref, interest_rate, emi))
        return True, f"Loan application {loan_id} submitted successfully."
    except Exception as e:
        return False, str(e)

def get_loans_by_user(user_id):
    return fetchall("SELECT * FROM loans WHERE user_id=%s ORDER BY applied_at DESC", (user_id,))

def get_pending_loans():
    return fetchall(
        """SELECT l.*,u.full_name as applicant_name,u.username
           FROM loans l JOIN users u ON l.user_id=u.user_id
           WHERE l.status='Pending' ORDER BY l.applied_at ASC""")

def get_all_loans():
    return fetchall(
        """SELECT l.*,u.full_name as applicant_name
           FROM loans l JOIN users u ON l.user_id=u.user_id
           ORDER BY l.applied_at DESC""")

def decide_loan(loan_id, decision, remarks, manager_id):
    if decision not in ("Approved","Rejected"):
        return False, "Invalid decision."
    execute(
        """UPDATE loans SET status=%s,manager_remarks=%s,approved_by=%s,decided_at=NOW()
           WHERE loan_id=%s AND status='Pending'""",
        (decision, remarks, manager_id, loan_id))
    if decision == "Approved":
        loan = fetchone("SELECT * FROM loans WHERE loan_id=%s", (loan_id,))
        if loan and loan["disbursement_account"]:
            txn_id = new_txn_id()
            execute_transaction([
                ("UPDATE accounts SET balance=balance+%s WHERE account_id=%s",
                 (loan["loan_amount"], loan["disbursement_account"])),
                ("""INSERT INTO transactions(transaction_id,to_account,amount,transaction_type,
                    narration,processed_by) VALUES(%s,%s,%s,'Loan Disbursement',%s,%s)""",
                 (txn_id, loan["disbursement_account"], loan["loan_amount"],
                  f"Loan {loan_id} disbursed", manager_id)),
            ])
            execute("UPDATE loans SET status='Disbursed' WHERE loan_id=%s", (loan_id,))
    return True, f"Loan {loan_id} {decision.lower()} successfully."

# ══════════════════════════════════════════════════════════════════════════════
# SALARY
# ══════════════════════════════════════════════════════════════════════════════
def disburse_salary(employee_user_id, cashier_user_id, amount, month_year):
    existing = fetchone(
        "SELECT * FROM salary_disbursements WHERE employee_user_id=%s AND month_year=%s",
        (employee_user_id, month_year))
    if existing:
        return False, f"Salary for {month_year} already disbursed."
    try:
        execute(
            """INSERT INTO salary_disbursements(employee_user_id,cashier_user_id,amount,month_year)
               VALUES(%s,%s,%s,%s)""",
            (employee_user_id, cashier_user_id, amount, month_year))
        return True, f"Salary of ₹{amount:,.2f} disbursed for {month_year}."
    except Exception as e:
        if "Duplicate" in str(e) or "1062" in str(e):
            return False, "Salary already disbursed for this period."
        return False, str(e)

def get_salary_history(employee_user_id=None):
    if employee_user_id:
        return fetchall(
            """SELECT sd.*,u.full_name as cashier_name,eu.full_name as employee_name
               FROM salary_disbursements sd
               JOIN users u ON sd.cashier_user_id=u.user_id
               JOIN users eu ON sd.employee_user_id=eu.user_id
               WHERE sd.employee_user_id=%s ORDER BY sd.disbursed_at DESC""",
            (employee_user_id,))
    return fetchall(
        """SELECT sd.*,u.full_name as cashier_name,eu.full_name as employee_name,
                  eu.role as employee_role
           FROM salary_disbursements sd
           JOIN users u ON sd.cashier_user_id=u.user_id
           JOIN users eu ON sd.employee_user_id=eu.user_id
           ORDER BY sd.disbursed_at DESC LIMIT 100""")

# ══════════════════════════════════════════════════════════════════════════════
# MESSAGES
# ══════════════════════════════════════════════════════════════════════════════
def send_message(sender_id, subject, body, receiver_id=None):
    try:
        execute("INSERT INTO messages(sender_id,receiver_id,subject,body) VALUES(%s,%s,%s,%s)",
                (sender_id, receiver_id, subject, body))
        return True, "Message sent successfully."
    except Exception as e:
        return False, str(e)

def get_manager_inbox(manager_id=None):
    return fetchall(
        """SELECT m.*,u.full_name as sender_name,u.role as sender_role
           FROM messages m JOIN users u ON m.sender_id=u.user_id
           ORDER BY m.sent_at DESC LIMIT 100""")

def mark_message_read(message_id):
    execute("UPDATE messages SET is_read=1 WHERE message_id=%s", (message_id,))

def get_unread_count(manager_id=None):
    row = fetchone("SELECT COUNT(*) as cnt FROM messages WHERE is_read=0")
    return row["cnt"] if row else 0

# ══════════════════════════════════════════════════════════════════════════════
# INTEREST RATES
# ══════════════════════════════════════════════════════════════════════════════
def get_interest_rates():
    return fetchall("SELECT * FROM interest_rates ORDER BY rate_id")

def update_interest_rate(account_type, rate, updated_by):
    try:
        execute(
            "UPDATE interest_rates SET rate=%s,updated_by=%s,updated_at=NOW() WHERE account_type=%s",
            (rate, updated_by, account_type))
        return True, f"{account_type} rate updated to {rate}% p.a."
    except Exception as e:
        return False, str(e)

# ══════════════════════════════════════════════════════════════════════════════
# AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════
def get_audit_logs(limit=200):
    return fetchall("SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s", (limit,))

# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
def get_bank_summary():
    r = lambda q: fetchone(q) or {}
    return {
        "total_accounts":     (r("SELECT COUNT(*) c FROM accounts WHERE status='Active'").get("c") or 0),
        "total_customers":    (r("SELECT COUNT(*) c FROM users WHERE role='customer' AND is_active=1").get("c") or 0),
        "total_balance":      float(r("SELECT COALESCE(SUM(balance),0) s FROM accounts WHERE status='Active'").get("s") or 0),
        "pending_loans":      (r("SELECT COUNT(*) c FROM loans WHERE status='Pending'").get("c") or 0),
        "total_loans_amount": float(r("SELECT COALESCE(SUM(loan_amount),0) s FROM loans WHERE status IN ('Approved','Disbursed')").get("s") or 0),
        "transactions_today": (r("SELECT COUNT(*) c FROM transactions WHERE DATE(created_at)=CURDATE()").get("c") or 0),
    }

def get_loan_portfolio_by_purpose():
    return fetchall(
        """SELECT loan_purpose,COUNT(*) as count,COALESCE(SUM(loan_amount),0) as total_amount
           FROM loans WHERE status IN ('Approved','Disbursed')
           GROUP BY loan_purpose""")

def get_transaction_trend(days=7):
    return fetchall(
        """SELECT DATE(created_at) as txn_date,COUNT(*) as count,
                  COALESCE(SUM(amount),0) as total_amount
           FROM transactions
           WHERE created_at>=DATE_SUB(NOW(), INTERVAL %s DAY)
           GROUP BY DATE(created_at) ORDER BY txn_date""", (days,))

def get_account_type_distribution():
    return fetchall(
        """SELECT account_type,COUNT(*) as count,COALESCE(SUM(balance),0) as total_balance
           FROM accounts WHERE status='Active' GROUP BY account_type""")

def get_loan_by_collateral():
    return fetchall(
        """SELECT collateral_type,COUNT(*) as count,COALESCE(SUM(loan_amount),0) as total_amount,
                  AVG(computed_interest_rate) as avg_rate
           FROM loans GROUP BY collateral_type""")