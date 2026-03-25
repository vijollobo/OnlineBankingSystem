-- ============================================================
-- Bank of Bharat - Database Schema  (v2)
-- Run via:  mysql -u root -p < setup.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS bank_of_bharat
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE bank_of_bharat;

CREATE TABLE IF NOT EXISTS users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(50) UNIQUE NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    role           ENUM('customer','cashier','admin','manager') NOT NULL,
    full_name      VARCHAR(100) NOT NULL,
    email          VARCHAR(100),
    phone          VARCHAR(15),
    address        TEXT,
    date_of_birth  DATE,
    gender         ENUM('Male','Female','Other'),
    is_active      TINYINT(1) DEFAULT 1,
    failed_attempts INT DEFAULT 0,
    locked_until   DATETIME DEFAULT NULL,
    self_registered TINYINT(1) DEFAULT 0,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    emp_id         INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT NOT NULL UNIQUE,
    employee_code  VARCHAR(20) UNIQUE,
    department     VARCHAR(50),
    grade          VARCHAR(20) DEFAULT 'Junior',
    designation    VARCHAR(50),
    salary         DECIMAL(12,2) DEFAULT 0.00,
    joining_date   DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id           VARCHAR(20) PRIMARY KEY,
    user_id              INT NOT NULL,
    account_type         ENUM('Savings','Current','Fixed Deposit','Recurring Deposit','Salary Account') NOT NULL,
    balance              DECIMAL(15,2) DEFAULT 0.00,
    interest_rate        DECIMAL(5,2) DEFAULT 0.00,
    status               ENUM('Active','Inactive','Frozen') DEFAULT 'Active',
    opening_date         DATE NOT NULL,
    maturity_date        DATE DEFAULT NULL,
    monthly_installment  DECIMAL(12,2) DEFAULT NULL,
    tenure_months        INT DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   VARCHAR(25) PRIMARY KEY,
    from_account     VARCHAR(20) DEFAULT NULL,
    to_account       VARCHAR(20) DEFAULT NULL,
    amount           DECIMAL(15,2) NOT NULL,
    transaction_type ENUM('Deposit','Withdrawal','Transfer','Salary','Loan Disbursement','Admin Transfer') NOT NULL,
    narration        TEXT,
    status           ENUM('Success','Failed','Pending') DEFAULT 'Success',
    processed_by     INT DEFAULT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (processed_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS interest_rates (
    rate_id      INT AUTO_INCREMENT PRIMARY KEY,
    account_type ENUM('Savings','Current','Fixed Deposit','Recurring Deposit','Salary Account') UNIQUE NOT NULL,
    rate         DECIMAL(5,2) NOT NULL,
    updated_by   INT DEFAULT NULL,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id               VARCHAR(20) PRIMARY KEY,
    user_id               INT NOT NULL,
    disbursement_account  VARCHAR(20),
    full_name             VARCHAR(100),
    date_of_birth         DATE,
    gender                ENUM('Male','Female','Other'),
    employment_status     ENUM('Employed','Self-Employed','Unemployed'),
    monthly_income        DECIMAL(12,2),
    loan_amount           DECIMAL(15,2),
    loan_purpose          ENUM('Home','Education','Personal','Vehicle/Car','Business','Gold Loan','Vacation') NOT NULL,
    tenure_years          INT,
    credit_score          INT,
    collateral_type       ENUM('None','Gold','Property/Real Estate','Fixed Deposit','Vehicle') DEFAULT 'None',
    existing_loans_count  INT DEFAULT 0,
    kyc_reference         VARCHAR(20),
    computed_interest_rate DECIMAL(5,2),
    emi_amount            DECIMAL(12,2),
    status                ENUM('Pending','Approved','Rejected','Disbursed') DEFAULT 'Pending',
    manager_remarks       TEXT,
    approved_by           INT DEFAULT NULL,
    applied_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at            TIMESTAMP DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS salary_disbursements (
    disbursement_id  INT AUTO_INCREMENT PRIMARY KEY,
    employee_user_id INT NOT NULL,
    cashier_user_id  INT NOT NULL,
    amount           DECIMAL(12,2) NOT NULL,
    month_year       VARCHAR(7) NOT NULL,
    disbursed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_emp_month (employee_user_id, month_year),
    FOREIGN KEY (employee_user_id) REFERENCES users(user_id),
    FOREIGN KEY (cashier_user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS messages (
    message_id  INT AUTO_INCREMENT PRIMARY KEY,
    sender_id   INT NOT NULL,
    receiver_id INT DEFAULT NULL,
    subject     VARCHAR(200),
    body        TEXT,
    is_read     TINYINT(1) DEFAULT 0,
    sent_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id    INT DEFAULT NULL,
    username   VARCHAR(50),
    action     VARCHAR(100),
    details    TEXT,
    ip_address VARCHAR(45) DEFAULT '127.0.0.1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO interest_rates (account_type, rate) VALUES
    ('Savings', 4.00),
    ('Current', 0.00),
    ('Fixed Deposit', 6.50),
    ('Recurring Deposit', 5.50),
    ('Salary Account', 3.50)
ON DUPLICATE KEY UPDATE rate = VALUES(rate);
