"""
init_db.py  –  Run ONCE to create schema and seed default users.
Usage:  python init_db.py
Configure DB_HOST / DB_USER / DB_PASS below first.
"""
import sys, datetime, random, string, time
import mysql.connector
from mysql.connector import Error
import bcrypt

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = ""          # ← update with your MySQL password

def hash_pw(plain): return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def run():
    print("="*62)
    print("  Bank of Bharat — Database Initialiser")
    print("="*62)
    try:
        conn = mysql.connector.connect(host=DB_HOST,port=DB_PORT,
                                        user=DB_USER,password=DB_PASS,charset="utf8mb4")
    except Error as e:
        sys.exit(f"\n❌  MySQL connection failed: {e}\n"
                 "    Update DB_HOST/DB_USER/DB_PASS in init_db.py\n")

    cur = conn.cursor()
    print("\n📄  Running setup.sql …")
    with open("setup.sql","r",encoding="utf-8") as f:
        stmts = [s.strip() for s in f.read().split(";") if s.strip()]
    for stmt in stmts:
        try:
            cur.execute(stmt); conn.commit()
        except Error as e:
            if e.errno not in (1050,1060,1061,1062): print(f"  ⚠️  {e}")
    cur.execute("USE bank_of_bharat;")

    print("\nSeeding default users …")
    USERS = [
        ("admin",    "Admin@123",    "admin",   "System Administrator","admin@bob.in",    "9800000001","IT & Admin","Senior","Bank Administrator",75000),
        ("manager",  "Manager@123",  "manager", "Ambar Bezbaruah",        "manager@bob.in",  "9800000002","Management","Senior","Branch Manager",    90000),
        ("cashier1", "Cashier@123",  "cashier", "Soyam Rai",        "cashier@bob.in",  "9800000003","Operations","Junior","Senior Cashier",    45000),
        ("cashier2", "Cashier@123",  "cashier", "Nikchaya Lamsal",        "cashier2@bob.in", "9800000006","Operations","Mid",  "Cashier",           40000),
        ("customer1","Customer@123", "customer","Sarmishta Mukhopadhyay",          "amit@email.com",  "9800000004",None,None,None,None),
        ("customer2","Customer@123", "customer","Champakalakshmi Iyer",         "sunita@email.com","9800000005",None,None,None,None),
    ]
    created_users = {}
    for row in USERS:
        uname,pwd,role,fname,email,phone,dept,grade,desig,sal = row
        cur.execute("SELECT user_id FROM users WHERE username=%s",(uname,))
        ex = cur.fetchone()
        if ex:
            print(f"  ✅  '{uname}' already exists — skipped.")
            created_users[uname] = ex[0]; continue
        dob = datetime.date(1985,6,15) if role!="customer" else datetime.date(1990,3,10)
        gender = "Male" if uname not in ("cashier1",) else "Female"
        cur.execute("""INSERT INTO users(username,password_hash,role,full_name,email,phone,
                       date_of_birth,gender,is_active) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,1)""",
                    (uname,hash_pw(pwd),role,fname,email,phone,dob,gender))
        conn.commit(); uid = cur.lastrowid
        created_users[uname] = uid
        print(f"  ✅  Created '{uname}' (ID={uid}, role={role})")
        if role in ("cashier","admin","manager"):
            cur.execute("""INSERT INTO employees(user_id,employee_code,department,grade,
                           designation,salary,joining_date) VALUES(%s,%s,%s,%s,%s,%s,%s)""",
                        (uid,f"EMP{uid:04d}",dept,grade,desig,sal,datetime.date(2020,1,1)))
            conn.commit()

    # Seed accounts for customer1
    uid1 = created_users.get("customer1")
    if uid1:
        cur.execute("SELECT COUNT(*) FROM accounts WHERE user_id=%s",(uid1,))
        if cur.fetchone()[0] == 0:
            def rand_acc():
                return "BOB"+datetime.datetime.now().strftime("%Y%m%d%H%M%S")+''.join(random.choices(string.digits,k=4))
            accs = [
                (rand_acc(),uid1,"Savings",      25000.00,4.00),
                (rand_acc(),uid1,"Salary Account",50000.00,3.50),
            ]
            for a in accs:
                time.sleep(1)
                cur.execute("""INSERT INTO accounts(account_id,user_id,account_type,balance,
                               interest_rate,opening_date) VALUES(%s,%s,%s,%s,%s,%s)""",
                            (*a, datetime.date.today()))
                conn.commit()
                print(f"  ✅  Sample account {a[0]} ({a[2]}) for customer1")

    cur.close(); conn.close()
    print("\n"+"="*62)
    print(" ✅ Database initialised successfully!")
    print("="*62)
    print("""
 Default Credentials:
 ┌─────────────┬──────────────┬──────────┐
 │ Username    │ Password     │ Role     │
 ├─────────────┼──────────────┼──────────┤
 │ admin       │ Admin@123    │ Admin    │
 │ manager     │ Manager@123  │ Manager  │
 │ cashier1    │ Cashier@123  │ Cashier  │
 │ cashier2    │ Cashier@123  │ Cashier  │
 │ customer1   │ Customer@123 │ Customer │
 │ customer2   │ Customer@123 │ Customer │
 └─────────────┴──────────────┴──────────┘

 ▶  Run the app:  streamlit run app.py
""")

if __name__=="__main__":
    run()
