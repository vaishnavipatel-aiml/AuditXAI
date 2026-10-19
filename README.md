# AuditXAI — Local Prototype

A local, laptop-friendly Streamlit prototype for explainable internal-audit anomaly review.

## Included
- Login, registration, logout, and SQLite-backed user accounts (passwords are PBKDF2-hashed).
- Dashboard with audit metrics and charts.
- Synthetic reimbursement/procurement dataset generator.
- CSV upload with required-column validation.
- Rule checks: missing invoice, repeated vendor/invoice pair, high amount, pending approval.
- Isolation Forest anomaly detection.
- Plain-English rule findings plus feature-deviation context for ML-flagged records.
- Findings filters, transaction detail, CSV export, and local history for the signed-in user.
- No API keys, cloud services, or GPU required.

## Demo login
- Email: `admin@auditxai.local`
- Password: `AuditXAI@123`

This is a local academic demo account. Change the password after first login. Do not expose this demo app to the public internet as-is.

## Setup (Windows)
1. Install Python 3.11 or 3.12.
2. Extract this ZIP.
3. Open Command Prompt in the extracted `AuditXAI_Prototype` folder.
4. Run:

```bat
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If `py -3.12` is unavailable, use a Python version installed on your computer.

## CSV columns
Required columns:
`transaction_id, transaction_date, employee_id, department, transaction_type, vendor, amount, invoice_id, approval_status`

Use synthetic or properly authorized data only. Do not upload confidential company data to an unapproved environment.

## Important limitations
- Alerts are review indicators, not proof of fraud or misconduct.
- Isolation Forest is unsupervised; its output depends on the selected data and model settings.
- Feature-deviation explanations are contextual clues, not SHAP values or causal explanations.
- Synthetic demo data is for testing the workflow, not evidence of real-world accuracy.
- The local authentication flow is suitable for a classroom prototype, not a security-audited production deployment.
