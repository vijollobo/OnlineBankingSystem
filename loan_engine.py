"""
loan_engine.py  –  Loan Interest Rate Engine for Bank of Bharat (v2)
Implements an enhanced additive model:
  Base: 8.00%  |  Floor: 6.00%  |  Cap: 22.00%

Factors (v2 enhancements):
  Age, Gender, Tenure, Employment, Credit Score,
  Collateral TYPE (Gold / Property / FD / Vehicle / None),
  Existing Loans, LTI Ratio, Loan Purpose
"""
from dataclasses import dataclass
from datetime import date

RATE_FLOOR = 6.00
RATE_CAP   = 22.00
BASE_RATE  = 8.00

# ── Loan purpose descriptions shown in UI ────────────────────────
LOAN_PURPOSES = {
    "Home":        ("🏠", "Purchase or construct a home",                   -0.25),
    "Education":   ("🎓", "Finance higher education / professional courses", -0.50),
    "Personal":    ("👤", "Personal expenses — medical, wedding, etc.",      +0.50),
    "Vehicle/Car": ("🚗", "Purchase a new or used vehicle",                  0.00),
    "Business":    ("🏢", "Fund business operations or expansion",           +0.75),
    "Gold Loan":   ("🥇", "Loan against gold ornaments/jewellery",          -0.75),
    "Vacation":    ("✈️", "Travel and leisure — higher risk",                +1.00),
}

# ── Collateral type: (display label, description, rate_adjustment) ─
COLLATERAL_TYPES = {
    "None":                ("❌", "No security offered",                      +2.00),
    "Gold":                ("🥇", "Gold jewellery / coins pledged",           -1.50),
    "Property/Real Estate":("🏘️", "Land or building as security",            -1.00),
    "Fixed Deposit":       ("📄", "FD receipt pledged with bank",             -1.25),
    "Vehicle":             ("🚗", "Vehicle RC pledged as collateral",         -0.75),
}


@dataclass
class LoanProfile:
    date_of_birth:       date
    gender:              str    # Male | Female | Other
    employment_status:   str    # Employed | Self-Employed | Unemployed
    monthly_income:      float
    loan_amount:         float
    tenure_years:        int
    credit_score:        int    # 300–900
    collateral_type:     str    # one of COLLATERAL_TYPES keys
    existing_loans_count: int
    loan_purpose:        str    # one of LOAN_PURPOSES keys


@dataclass
class RateBreakdown:
    base_rate:           float
    age_adj:             float
    gender_adj:          float
    tenure_adj:          float
    employment_adj:      float
    credit_adj:          float
    collateral_adj:      float
    existing_loans_adj:  float
    lti_adj:             float
    purpose_adj:         float
    raw_rate:            float
    final_rate:          float
    emi:                 float
    age:                 int
    lti_ratio:           float
    annual_income:       float
    total_payable:       float
    total_interest:      float


def _calc_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def calculate_rate(profile: LoanProfile) -> RateBreakdown:
    age          = _calc_age(profile.date_of_birth)
    annual_income = profile.monthly_income * 12
    lti_ratio    = profile.loan_amount / annual_income if annual_income > 0 else 99.0

    # Age
    if   age < 25:                age_adj = +2.00
    elif 25 <= age <= 35:         age_adj =  0.00
    elif 36 <= age <= 50:         age_adj = +0.50
    elif 51 <= age <= 60:         age_adj = +1.00
    else:                         age_adj = +2.00

    # Gender
    gender_adj = -0.50 if profile.gender == "Female" else 0.00

    # Tenure
    t = profile.tenure_years
    if   t <= 1:  tenure_adj = 0.00
    elif t <= 3:  tenure_adj = +0.50
    elif t <= 5:  tenure_adj = +1.00
    elif t <= 10: tenure_adj = +1.50
    else:         tenure_adj = +2.00

    # Employment
    if   profile.employment_status == "Employed":     employment_adj = 0.00
    elif profile.employment_status == "Self-Employed": employment_adj = +1.00
    else:                                              employment_adj = +3.00

    # Credit Score (CIBIL)
    cs = profile.credit_score
    if   cs >= 750: credit_adj = -1.50
    elif cs >= 650: credit_adj =  0.00
    elif cs >= 550: credit_adj = +1.50
    else:           credit_adj = +3.00

    # Collateral TYPE (replaces binary yes/no)
    _, _, collateral_adj = COLLATERAL_TYPES.get(profile.collateral_type, ("","", +2.00))

    # Existing Loans
    el = profile.existing_loans_count
    if   el == 0: existing_loans_adj = 0.00
    elif el == 1: existing_loans_adj = +0.50
    else:         existing_loans_adj = +1.50

    # LTI Ratio
    if   lti_ratio < 2:  lti_adj = 0.00
    elif lti_ratio <= 4: lti_adj = +0.50
    else:                lti_adj = +1.50

    # Loan Purpose
    _, _, purpose_adj = LOAN_PURPOSES.get(profile.loan_purpose, ("","", 0.00))

    raw_rate = (BASE_RATE + age_adj + gender_adj + tenure_adj + employment_adj
                + credit_adj + collateral_adj + existing_loans_adj + lti_adj + purpose_adj)
    final_rate = max(RATE_FLOOR, min(RATE_CAP, raw_rate))

    # EMI = P × r × (1+r)^n / ((1+r)^n − 1)
    n = profile.tenure_years * 12
    r = final_rate / 100 / 12
    if r == 0:
        emi = profile.loan_amount / n if n > 0 else 0.0
    else:
        emi = profile.loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)

    total_payable  = round(emi * n, 2)
    total_interest = round(total_payable - profile.loan_amount, 2)

    return RateBreakdown(
        base_rate=BASE_RATE,
        age_adj=age_adj,
        gender_adj=gender_adj,
        tenure_adj=tenure_adj,
        employment_adj=employment_adj,
        credit_adj=credit_adj,
        collateral_adj=collateral_adj,
        existing_loans_adj=existing_loans_adj,
        lti_adj=lti_adj,
        purpose_adj=purpose_adj,
        raw_rate=round(raw_rate, 2),
        final_rate=round(final_rate, 2),
        emi=round(emi, 2),
        age=age,
        lti_ratio=round(lti_ratio, 2),
        annual_income=annual_income,
        total_payable=total_payable,
        total_interest=total_interest,
    )


def affordability_check(monthly_income: float, emi: float) -> tuple[bool, str]:
    if monthly_income >= 3 * emi:
        return True, f"Affordability check passed — income ≥ 3× EMI"
    return False, (
        f"Affordability check failed: Monthly income ₹{monthly_income:,.0f} "
        f"must be ≥ 3× EMI (₹{3 * emi:,.0f})"
    )
