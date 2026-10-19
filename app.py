import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from engine import make_demo_data, validate_columns, analyze_transactions
from storage import init_db, authenticate, register_user, save_analysis, list_analyses, get_analysis

st.set_page_config(page_title="AuditXAI | Audit Intelligence", page_icon="🔎", layout="wide")
init_db()

st.markdown("""
<style>
:root { --navy:#101A2B; --teal:#0D9488; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #101A2B; }
[data-testid="stSidebar"] * { color: #F4F7FB; }
.hero { padding: 1.4rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg,#101A2B,#1D3653); color:white; margin-bottom:1rem; }
.hero h1 { color:white; margin-bottom:.25rem; }
.hero p { color:#D6E2EF; margin-bottom:0; }
.kpi { border:1px solid rgba(128,145,165,.25); border-radius:14px; padding:1rem; background:rgba(128,145,165,.04); min-height:105px; }
.kpi-label { color:#6B7280; font-size:.88rem; }
.kpi-value { font-size:1.7rem; font-weight:700; margin-top:.25rem; }
.small-muted { color:#778399; font-size:.85rem; }
div.stButton > button[kind="primary"] { background:#0D9488; border-color:#0D9488; }
</style>
""", unsafe_allow_html=True)

def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)

def show_login():
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown("""
        <div style="padding:2rem 1rem 1rem 0">
        <div style="font-size:3.2rem">◈</div>
        <h1 style="font-size:2.7rem;line-height:1.1">AuditXAI</h1>
        <h3 style="font-weight:500">Audit intelligence, with explanations.</h3>
        <p style="color:#748094;font-size:1.05rem">A decision-support workspace for reviewing unusual reimbursement and procurement transactions.</p>
        <hr>
        <p>✓ ML-assisted anomaly detection</p>
        <p>✓ Transparent audit-rule checks</p>
        <p>✓ Transaction-level review explanations</p>
        <p>✓ Local-first academic prototype</p>
        </div>
        """, unsafe_allow_html=True)
    with right:
        st.markdown("### Welcome")
        st.caption("Sign in to your local AuditXAI workspace.")
        tab_login, tab_register = st.tabs(["Sign in", "Create account"])
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@company.com")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submit:
                user = authenticate(email, password)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Email or password is incorrect.")
            with st.expander("Demo account"):
                st.code("Email: admin@auditxai.local\nPassword: AuditXAI@123")
                st.caption("For local academic demonstration only. Change this password after first login.")
        with tab_register:
            with st.form("register_form"):
                name = st.text_input("Full name")
                email_new = st.text_input("Email address")
                pw1 = st.text_input("Create password", type="password")
                pw2 = st.text_input("Confirm password", type="password")
                create = st.form_submit_button("Create local account", type="primary", use_container_width=True)
            if create:
                if not name.strip() or "@" not in email_new or len(pw1) < 10:
                    st.error("Enter your name and a valid email. Password must be at least 10 characters.")
                elif pw1 != pw2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        user = register_user(name, email_new, pw1)
                        st.session_state["user"] = user
                        st.success("Account created.")
                        st.rerun()
                    except Exception:
                        st.error("Could not create account. This email may already be registered.")

if "user" not in st.session_state:
    show_login()
    st.stop()

user = st.session_state["user"]
if "results" not in st.session_state:
    st.session_state["results"] = None
if "source_name" not in st.session_state:
    st.session_state["source_name"] = ""
if "analysis_saved" not in st.session_state:
    st.session_state["analysis_saved"] = False

with st.sidebar:
    st.markdown("## ◈ AuditXAI")
    st.caption("AUDIT INTELLIGENCE")
    st.divider()
    page = st.radio(
        "Workspace",
        ["Overview", "Analyze transactions", "Findings & explanations", "Analysis history", "About & settings"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown(f"**{user['name']}**")
    st.caption(f"{user['role']} · Local workspace")
    if st.button("Sign out", use_container_width=True):
        for key in ["user", "results", "source_name", "analysis_saved"]:
            st.session_state.pop(key, None)
        st.rerun()
    st.caption("Local prototype · No cloud connection")

results = st.session_state.get("results")

if page == "Overview":
    hero("Audit overview", "A clear view of transaction review activity and model-generated alerts.")
    if results is None:
        st.info("Your workspace is ready. Start by analyzing a demo dataset or uploading your own CSV.")
        a, b = st.columns(2)
        with a:
            st.markdown("### Explore the demo")
            st.write("Load synthetic transactions with deliberately injected examples to test the audit workflow.")
            if st.button("Load demo data & analyze", type="primary", use_container_width=True):
                demo = make_demo_data()
                st.session_state["results"] = analyze_transactions(demo)
                st.session_state["source_name"] = "Synthetic demo dataset"
                st.session_state["analysis_saved"] = False
                st.rerun()
        with b:
            st.markdown("### Analyze your data")
            st.write("Use a CSV with the required transaction columns. The app validates it before analysis.")
            st.page_link("app.py", label="Go to Analyze transactions", icon=":material/upload_file:")
        st.divider()
        st.markdown("### Workflow")
        cols = st.columns(4)
        for col, num, title, desc in zip(cols, ["01","02","03","04"], ["Import","Detect","Explain","Review"], ["Validate a CSV","Run audit rules + ML","Inspect alert reasons","Export findings"]):
            with col:
                st.markdown(f'<div class="kpi"><div class="kpi-label">{num}</div><b>{title}</b><p class="small-muted">{desc}</p></div>', unsafe_allow_html=True)
    else:
        flagged = results[results["review_required"]]
        c1,c2,c3,c4 = st.columns(4)
        metrics = [
            ("Transactions analyzed", f"{len(results):,}"),
            ("Needs review", f"{len(flagged):,}"),
            ("ML anomalies", f"{int(results['ml_anomaly'].sum()):,}"),
            ("Rule alerts", f"{int(results['rule_alert'].sum()):,}")
        ]
        for col,(label,value) in zip([c1,c2,c3,c4],metrics):
            with col:
                st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>', unsafe_allow_html=True)
        st.write("")
        chart1, chart2 = st.columns(2)
        with chart1:
            fig = px.histogram(results, x="amount", color="review_required", nbins=30, title="Transaction amount distribution", labels={"review_required":"Needs review","amount":"Amount"})
            st.plotly_chart(fig, use_container_width=True)
        with chart2:
            counts = results["review_priority"].value_counts().rename_axis("Priority").reset_index(name="Transactions")
            fig = px.bar(counts, x="Priority", y="Transactions", color="Priority", title="Review priority distribution")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("### Highest-priority items")
        st.dataframe(flagged[["transaction_id","transaction_date","department","vendor","amount","review_priority","audit_reasons"]].head(10), use_container_width=True, hide_index=True)
        st.caption("All alerts are review indicators, not determinations of fraud.")

elif page == "Analyze transactions":
    hero("Analyze transactions", "Import transaction data, validate it, then run explainable anomaly detection.")
    source = st.radio("Data source", ["Use synthetic demo data", "Upload a CSV file"], horizontal=True)
    threshold = st.number_input("High-amount review threshold", min_value=1000, max_value=10000000, value=25000, step=1000, help="A configurable review rule, not a universal policy threshold.")
    contamination = st.slider("Expected anomaly proportion for Isolation Forest", 0.01, 0.20, 0.05, 0.01, help="This is a model parameter, not the expected fraud rate.")
    n_estimators = st.select_slider("Model complexity (number of trees)", options=[50,100,150,200,300], value=150)
    input_df = None
    source_name = ""
    if source == "Use synthetic demo data":
        input_df = make_demo_data()
        source_name = "Synthetic demo dataset"
        st.success(f"Demo dataset ready: {len(input_df)} synthetic rows.")
        with st.expander("Preview input data"):
            st.dataframe(input_df.head(15), use_container_width=True, hide_index=True)
    else:
        uploaded = st.file_uploader("Upload CSV", type=["csv"], key="csv_upload")
        if uploaded:
            try:
                input_df = pd.read_csv(uploaded)
                input_df, missing = validate_columns(input_df)
                source_name = uploaded.name
                if missing:
                    st.error("Missing required columns: " + ", ".join(missing))
                    input_df = None
                else:
                    st.success(f"CSV loaded: {len(input_df)} rows.")
                    with st.expander("Preview input data"):
                        st.dataframe(input_df.head(15), use_container_width=True, hide_index=True)
            except Exception as exc:
                st.error(f"Unable to read this CSV: {exc}")
    st.markdown("#### Required columns")
    st.code("transaction_id, transaction_date, employee_id, department, transaction_type, vendor, amount, invoice_id, approval_status")
    if st.button("Run AuditXAI analysis", type="primary", disabled=input_df is None, use_container_width=True):
        with st.spinner("Validating transactions and running the anomaly model..."):
            try:
                st.session_state["results"] = analyze_transactions(input_df, threshold, contamination, n_estimators)
                st.session_state["source_name"] = source_name
                st.session_state["analysis_saved"] = False
                st.success("Analysis completed.")
                st.rerun()
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
    if results is not None:
        st.divider()
        st.markdown("### Current analysis")
        st.write(f"Source: **{st.session_state.get('source_name','')}** · {len(results):,} valid-amount transactions")
        if st.button("Save analysis to my local history", disabled=st.session_state.get("analysis_saved",False)):
            save_analysis(user["id"], st.session_state.get("source_name","Uploaded data"), results)
            st.session_state["analysis_saved"] = True
            st.success("Saved to local analysis history for this account.")

elif page == "Findings & explanations":
    hero("Findings & explanations", "Review individual alerts and understand the checks that triggered them.")
    if results is None:
        st.warning("Run an analysis first.")
        st.stop()
    f1,f2,f3 = st.columns(3)
    with f1:
        priority_filter = st.multiselect("Priority", ["High","Medium","Routine"], default=["High","Medium"])
    with f2:
        status_filter = st.selectbox("Finding type", ["All findings","ML anomalies","Rule-based alerts","Both ML and rules"])
    with f3:
        search = st.text_input("Search transaction, vendor, employee")
    view = results[results["review_required"]].copy()
    view = view[view["review_priority"].isin(priority_filter)]
    if status_filter == "ML anomalies":
        view = view[view["ml_anomaly"]]
    elif status_filter == "Rule-based alerts":
        view = view[view["rule_alert"]]
    elif status_filter == "Both ML and rules":
        view = view[view["ml_anomaly"] & view["rule_alert"]]
    if search:
        mask = view.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
        view = view[mask]
    st.caption(f"{len(view)} finding(s) match your filters.")
    st.dataframe(view[["transaction_id","transaction_date","employee_id","department","transaction_type","vendor","amount","invoice_id","approval_status","ml_anomaly","rule_alert","review_priority","anomaly_score","audit_reasons"]], use_container_width=True, hide_index=True)
    if not view.empty:
        selected_id = st.selectbox("Open a transaction for detailed review", view["transaction_id"].astype(str).tolist())
        row = view[view["transaction_id"].astype(str) == selected_id].iloc[0]
        st.divider()
        st.markdown(f"### Transaction {row['transaction_id']}")
        a,b,c = st.columns(3)
        a.metric("Amount", f"₹{row['amount']:,.2f}")
        b.metric("Review priority", row["review_priority"])
        c.metric("ML anomaly score", f"{row['anomaly_score']:.4f}")
        st.markdown("#### Why is this transaction listed?")
        if row["audit_reasons"]:
            for reason in row["audit_reasons"].split("; "):
                st.markdown(f"- {reason}")
        else:
            st.write("No rule-specific reason was generated.")
        st.markdown("#### Suggested auditor action")
        st.info("Check the supporting invoice, applicable policy, approval trail, and similar transactions. Document the outcome after human review.")
        st.caption("The ML score ranks unusualness within this analysis; it is not a probability of fraud. Feature-context explanations are not causal claims.")
    st.download_button("Export filtered findings (CSV)", data=view.to_csv(index=False).encode("utf-8"), file_name="auditxai_filtered_findings.csv", mime="text/csv", use_container_width=True)

elif page == "Analysis history":
    hero("Analysis history", "Locally saved analysis summaries for your signed-in account.")
    history = list_analyses(user["id"])
    if not history:
        st.info("No saved analyses yet. Run an analysis and choose 'Save analysis to my local history'.")
    else:
        st.dataframe(pd.DataFrame(history), use_container_width=True, hide_index=True)
        ids = [r["id"] for r in history]
        chosen = st.selectbox("Inspect a saved analysis", ids, format_func=lambda x: f"Analysis #{x}")
        record = get_analysis(user["id"], int(chosen))
        if record:
            st.write(f"**Source:** {record['source_name']}")
            st.write(f"**Created:** {record['created_at']}")
            st.write(f"**Transactions:** {record['transaction_count']} · **Flagged:** {record['flagged_count']}")
            st.download_button("Download saved findings JSON", record["findings_json"].encode("utf-8"), file_name=f"auditxai_analysis_{chosen}.json", mime="application/json")
    st.caption("History is stored in a local SQLite database on this computer.")

else:
    hero("About & settings", "Prototype configuration, responsible-use notes, and project information.")
    st.markdown("### Workspace profile")
    st.write(f"**Name:** {user['name']}")
    st.write(f"**Email:** {user['email']}")
    st.write(f"**Role:** {user['role']}")
    st.write("**Storage:** Local SQLite database and session memory.")
    st.markdown("### AI components")
    st.markdown("""
    - **Isolation Forest:** unsupervised anomaly detection over amount, transaction timing, department, transaction type, approval status, and invoice presence.
    - **Audit rules:** missing invoice, repeated vendor/invoice pair, repeated transaction ID, high amount, pending approval, and data-quality issues.
    - **Explanations:** explicit rule findings plus a plain-language summary of the ML signal. These are not causal explanations and are not SHAP values.
    """)
    st.markdown("### Responsible use")
    st.warning("AuditXAI prioritizes records for human review. It does not establish fraud, intent, policy violation, or employee misconduct.")
    st.markdown("### Demo security")
    st.info("This app hashes local passwords and stores data on this computer. It is an academic prototype, not a production identity system. Do not expose it publicly or use sensitive corporate data without authorization.")
    st.markdown("### Project details")
    st.write("Version 1.0 · Local academic prototype · No external APIs required.")
