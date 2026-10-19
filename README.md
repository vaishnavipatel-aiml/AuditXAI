🌐 **Live Demo:** https://auditxai-vaish.streamlit.app/

# AuditXAI — Explainable AI for Internal Audit

An AI-powered audit analytics prototype that helps auditors identify unusual corporate reimbursement and procurement transactions, understand the reasons behind flagged records, and prioritize cases for human review.

## Overview

AuditXAI combines rule-based audit checks with machine learning to surface potentially unusual transactions. Instead of treating an anomaly as proof of fraud, the system provides review indicators and contextual explanations to support human decision-making.

## Key Features

- **Login and Registration:** Local account management for the prototype.
- **Audit Dashboard:** Summary metrics and visualizations of analyzed transactions.
- **Transaction Analysis:** Upload a CSV dataset or explore synthetic demonstration data.
- **Rule-Based Checks:** Flags issues such as missing invoices, repeated vendor–invoice combinations, duplicate transaction IDs, unusually high amounts, and pending approvals.
- **Machine Learning:** Isolation Forest identifies transactions with unusual patterns.
- **Explainability:** Presents audit flags and contextual reasons to help users understand why a transaction may need review.
- **Findings Explorer:** Filter flagged records and export analysis results.
- **Analysis History:** Stores previous analysis runs locally using SQLite.

## Technology Stack

- Python
- Streamlit
- Pandas and NumPy
- Scikit-learn
- Plotly
- SQLite

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/vaishnavipatel-aiml/AuditXAI.git
cd AuditXAI
```

### 2. Create and activate a virtual environment

Windows:

```bash
py -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
streamlit run app.py
```

Open the local URL displayed in the terminal.

## Dataset

You can use the built-in synthetic demonstration data or upload a CSV file that follows the column requirements described in the application.

Do not upload real employee, vendor, reimbursement, or financial records to a public repository.

## Responsible Use

AuditXAI is an academic prototype for anomaly detection and internal audit support. An anomaly score is not a fraud probability, and a flagged transaction is not proof of misconduct. Findings should be investigated and validated by an authorized human reviewer.

The current version uses local storage and is not designed for production deployment or public internet exposure.

## Current Scope

The prototype includes a local web interface, authentication, audit rules, anomaly detection, explanations, visualizations, and analysis history. Future work may include stronger explainability methods, broader evaluation, improved security, and testing with appropriately anonymized or synthetic datasets.

## Author

**Vaishnavi Patel**

B.Tech — Computer Science and Engineering (AI & ML)

[GitHub Profile](https://github.com/vaishnavipatel-aiml)
