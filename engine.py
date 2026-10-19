import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

REQUIRED_COLUMNS = [
    "transaction_id", "transaction_date", "employee_id", "department",
    "transaction_type", "vendor", "amount", "invoice_id", "approval_status"
]

def make_demo_data(n=350, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.Timestamp("2026-01-01") + pd.to_timedelta(rng.integers(0, 180, n), unit="D")
    df = pd.DataFrame({
        "transaction_id": [f"TXN-{i:05d}" for i in range(1, n + 1)],
        "transaction_date": dates.strftime("%Y-%m-%d"),
        "employee_id": [f"EMP-{x:03d}" for x in rng.integers(1, 70, n)],
        "department": rng.choice(["Finance", "Sales", "IT", "Operations", "HR"], n),
        "transaction_type": rng.choice(["Reimbursement", "Procurement"], n),
        "vendor": [f"Vendor-{x:02d}" for x in rng.integers(1, 45, n)],
        "amount": np.round(rng.lognormal(mean=7.7, sigma=0.62, size=n), 2),
        "invoice_id": [f"INV-{i:05d}" for i in range(1, n + 1)],
        "approval_status": rng.choice(["Approved", "Pending"], n, p=[0.84, 0.16])
    })
    # Intentionally injected test cases to demonstrate the workflow.
    if n > 25:
        df.loc[4, "amount"] = 87500
        df.loc[11, "amount"] = 64000
        df.loc[4, "invoice_id"] = ""
        df.loc[20, "invoice_id"] = df.loc[19, "invoice_id"]
        df.loc[20, "vendor"] = df.loc[19, "vendor"]
        df.loc[24, "approval_status"] = "Pending"
    return df

def validate_columns(df):
    cleaned = df.copy()
    cleaned.columns = [str(c).strip().lower() for c in cleaned.columns]
    missing = sorted(set(REQUIRED_COLUMNS) - set(cleaned.columns))
    return cleaned, missing

def analyze_transactions(data, threshold=25000, contamination=0.05, n_estimators=150):
    df = data.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    df["transaction_id"] = df["transaction_id"].fillna("").astype(str).str.strip()
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    for col in ["employee_id", "department", "transaction_type", "vendor", "invoice_id", "approval_status"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["invoice_id"] = df["invoice_id"].replace({"nan": "", "None": ""})
    df["vendor"] = df["vendor"].replace({"nan": "", "None": ""})
    df["approval_status"] = df["approval_status"].str.title()

    original_count = len(df)
    invalid_amount = df["amount"].isna() | (df["amount"] < 0)
    df["data_quality_issue"] = invalid_amount | df["transaction_id"].eq("") | df["transaction_date"].isna()
    df = df.loc[~invalid_amount].copy()
    if len(df) < 10:
        raise ValueError("At least 10 transactions with valid, non-negative amounts are required.")
    if df["transaction_id"].duplicated(keep=False).any():
        df["duplicate_transaction_id"] = df["transaction_id"].duplicated(keep=False)
    else:
        df["duplicate_transaction_id"] = False

    df["missing_invoice"] = df["invoice_id"].eq("")
    valid_invoice = df["invoice_id"].ne("")
    df["duplicate_invoice"] = False
    df.loc[valid_invoice, "duplicate_invoice"] = df.loc[valid_invoice].duplicated(
        subset=["vendor", "invoice_id"], keep=False
    )
    df["high_amount"] = df["amount"] > float(threshold)
    df["pending_approval"] = df["approval_status"].str.lower().eq("pending")

    df["log_amount"] = np.log1p(df["amount"].clip(lower=0))
    df["weekday"] = df["transaction_date"].dt.dayofweek.fillna(-1)
    # One-hot categorical features let the model account for broad transaction context.
    categorical = pd.get_dummies(
        df[["department", "transaction_type", "approval_status"]],
        prefix=["dept", "type", "approval"], dtype=float
    )
    numeric = df[["log_amount", "weekday"]].astype(float)
    model_features = pd.concat([numeric, categorical], axis=1)
    if df["missing_invoice"].nunique() > 1:
        model_features["missing_invoice"] = df["missing_invoice"].astype(float)
    model_features = model_features.replace([np.inf, -np.inf], np.nan).fillna(0)

    model = IsolationForest(
        n_estimators=int(n_estimators),
        contamination=float(contamination),
        random_state=42,
        n_jobs=-1
    )
    df["ml_anomaly"] = model.fit_predict(model_features) == -1
    df["anomaly_score"] = -model.decision_function(model_features)

    # Transparent, record-level contextual explanations; not causal explanations or SHAP.
    median_amount = float(df["amount"].median())
    q3 = float(df["amount"].quantile(0.75))
    reasons = []
    for _, row in df.iterrows():
        r = []
        if row["missing_invoice"]:
            r.append("Invoice reference is missing (rule check)")
        if row["duplicate_invoice"]:
            r.append("Vendor and invoice reference repeat (rule check)")
        if row["duplicate_transaction_id"]:
            r.append("Transaction ID is repeated (data-quality check)")
        if row["high_amount"]:
            r.append(f"Amount exceeds the configured review threshold of {threshold:,.2f}")
        if row["pending_approval"]:
            r.append("Approval status is pending (workflow check)")
        if row["ml_anomaly"]:
            if row["amount"] > q3:
                r.append("ML model flagged an unusual pattern; amount is in the upper quartile of this dataset")
            else:
                r.append("ML model flagged an unusual combination of transaction features")
        if row["data_quality_issue"]:
            r.append("One or more key fields need data-quality review")
        reasons.append("; ".join(r))
    df["audit_reasons"] = reasons
    df["rule_alert"] = (
        df["missing_invoice"] | df["duplicate_invoice"] |
        df["duplicate_transaction_id"] | df["high_amount"] |
        df["pending_approval"] | df["data_quality_issue"]
    )
    df["review_required"] = df["rule_alert"] | df["ml_anomaly"]
    df["review_priority"] = np.select(
        [
            df["missing_invoice"] | df["duplicate_invoice"] | df["duplicate_transaction_id"],
            df["high_amount"] & df["ml_anomaly"],
            df["ml_anomaly"] | df["high_amount"] | df["data_quality_issue"]
        ],
        ["High", "High", "Medium"],
        default="Routine"
    )
    df["amount_vs_median"] = np.where(
        median_amount > 0, df["amount"] / median_amount, np.nan
    )
    df["analysis_note"] = (
        "Review indicator only. Verify supporting documents and applicable policy; this is not a finding of fraud."
    )
    df = df.sort_values(["review_required", "anomaly_score"], ascending=[False, False]).reset_index(drop=True)
    df.attrs["input_rows"] = original_count
    df.attrs["excluded_invalid_amount_rows"] = int(invalid_amount.sum())
    df.attrs["model_features"] = list(model_features.columns)
    return df
