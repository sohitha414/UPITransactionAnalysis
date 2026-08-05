import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as gg
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_pipeline.db import get_connection

st.set_page_config(
    page_title="UPI Transaction Analysis & Fraud Detection Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 0.2rem;
    }
    .badge-fraud {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-legit {
        background-color: #DCFCE7;
        color: #166534;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Query Helper with caching
@st.cache_data(ttl=5)
def load_data():
    conn = get_connection()
    q = """
    SELECT t.id, t.transaction_id, t.timestamp, t.amount, t.sender, t.receiver,
           t.transaction_type, t.device_id, t.location, t.is_fraud,
           t.fraud_probability, t.review_status, t.review_notes,
           f.transaction_hour, f.day_of_week, f.amount_category,
           f.sender_txn_freq_24h, f.receiver_txn_freq_24h, f.time_since_last_txn_mins,
           f.is_night_txn, f.is_high_value
    FROM transactions t
    JOIN engineered_features f ON t.transaction_id = f.transaction_id
    """
    df = pd.read_sql_query(q, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

@st.cache_data(ttl=5)
def load_latest_metrics():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT trained_at, model_version, sample_count, accuracy, precision,
           recall, f1_score, roc_auc, confusion_matrix, feature_importances
    FROM model_metrics
    ORDER BY id DESC LIMIT 1
    """)
    row = c.fetchone()
    conn.close()
    if row:
        d = dict(row)
        d['confusion_matrix'] = json.loads(d['confusion_matrix'])
        d['feature_importances'] = json.loads(d['feature_importances'])
        return d
    return None

# App Layout
st.markdown('<div class="main-header">🛡️ UPI Transaction Analysis & Fraud Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Live Machine Learning Fraud Scoring Pipeline & Risk Intelligence Center</div>', unsafe_allow_html=True)

df_all = load_data()
metrics = load_latest_metrics()

if df_all.empty:
    st.warning("⚠️ Database is empty. Please run the seed script or train pipeline to populate transactions.")
    st.stop()

# Sidebar Filters
st.sidebar.title("🔍 Live Filter Panel")

min_date = df_all['timestamp'].min().date()
max_date = df_all['timestamp'].max().date()

date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
all_types = list(df_all['transaction_type'].unique())
selected_types = st.sidebar.multiselect("Transaction Types", all_types, default=all_types)

all_tiers = ['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']
selected_tiers = st.sidebar.multiselect("Amount Categories", all_tiers, default=all_tiers)

hour_range = st.sidebar.slider("Hour of Day", 0, 23, (0, 23))

# Filter Application
df_filtered = df_all.copy()
if len(date_range) == 2:
    start_dt, end_dt = date_range
    df_filtered = df_filtered[(df_filtered['timestamp'].dt.date >= start_dt) & (df_filtered['timestamp'].dt.date <= end_dt)]

if selected_types:
    df_filtered = df_filtered[df_filtered['transaction_type'].isin(selected_types)]

if selected_tiers:
    df_filtered = df_filtered[df_filtered['amount_category'].isin(selected_tiers)]

df_filtered = df_filtered[(df_filtered['transaction_hour'] >= hour_range[0]) & (df_filtered['transaction_hour'] <= hour_range[1])]

# Top KPI Summary Cards
total_txns = len(df_filtered)
flagged_txns = (df_filtered['fraud_probability'] >= 0.50).sum()
fraud_rate = (flagged_txns / total_txns * 100) if total_txns > 0 else 0.0
total_amt = df_filtered['amount'].sum()
avg_amt = df_filtered['amount'].mean() if total_txns > 0 else 0.0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Transactions", f"{total_txns:,}")
with col2:
    st.metric("Flagged Fraud", f"{flagged_txns:,}", delta=f"{fraud_rate:.1f}% rate", delta_color="inverse")
with col3:
    st.metric("Fraud Rate", f"{fraud_rate:.2f}%")
with col4:
    st.metric("Total Volume", f"₹{total_amt:,.0f}")
with col5:
    acc_text = f"{metrics['accuracy']*100:.1f}%" if metrics else "N/A"
    f1_text = f"{metrics['f1_score']*100:.1f}%" if metrics else "N/A"
    st.metric("Model Accuracy / F1", f"{acc_text}", delta=f"F1: {f1_text}")

st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Live Analytics Dashboard", "🚨 Flagged Transactions Drill-down", "🤖 Model Evaluation & Metrics", "📄 Static Tableau Export Charts"])

# TAB 1: LIVE ANALYTICS DASHBOARD
with tab1:
    c_left, c_right = st.columns(2)

    with c_left:
        st.subheader("⏰ Transactions & Fraud Rate by Hour of Day")
        hourly_df = df_filtered.groupby('transaction_hour').agg(
            total=('id', 'count'),
            fraud=('is_fraud', 'sum')
        ).reset_index()
        hourly_df['fraud_rate_%'] = (hourly_df['fraud'] / hourly_df['total'] * 100).round(2)

        fig_hour = px.bar(
            hourly_df, x='transaction_hour', y='total',
            color='fraud_rate_%',
            color_continuous_scale='Reds',
            labels={'transaction_hour': 'Hour of Day (0-23)', 'total': 'Transaction Count', 'fraud_rate_%': 'Fraud Rate %'},
            title="Hourly Volume Heat-mapped by Fraud Rate %"
        )
        st.plotly_chart(fig_hour, use_container_width=True)

    with c_right:
        st.subheader("💳 Fraud Rate by Transaction Type")
        type_df = df_filtered.groupby('transaction_type').agg(
            total=('id', 'count'),
            fraud=('is_fraud', 'sum')
        ).reset_index()
        type_df['fraud_rate_%'] = (type_df['fraud'] / type_df['total'] * 100).round(2)

        fig_type = px.bar(
            type_df, x='transaction_type', y='fraud_rate_%',
            color='transaction_type',
            text='fraud_rate_%',
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={'transaction_type': 'Type', 'fraud_rate_%': 'Fraud Rate (%)'},
            title="Fraud Percentage Across Categories"
        )
        fig_type.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        st.plotly_chart(fig_type, use_container_width=True)

    c_left2, c_right2 = st.columns(2)

    with c_left2:
        st.subheader("📈 Daily Transaction & Fraud Trend")
        df_filtered['date_only'] = df_filtered['timestamp'].dt.date
        daily_df = df_filtered.groupby('date_only').agg(
            total=('id', 'count'),
            fraud=('is_fraud', 'sum')
        ).reset_index()

        fig_daily = px.line(
            daily_df, x='date_only', y=['total', 'fraud'],
            labels={'date_only': 'Date', 'value': 'Count', 'variable': 'Legend'},
            title="Daily Transaction Trend (Legit vs Fraud)",
            color_discrete_map={'total': '#3B82F6', 'fraud': '#EF4444'}
        )
        st.plotly_chart(fig_daily, use_container_width=True)

    with c_right2:
        st.subheader("💰 Amount Category Distribution")
        tier_df = df_filtered.groupby(['amount_category', 'is_fraud']).size().reset_index(name='count')
        tier_df['Status'] = tier_df['is_fraud'].map({1: 'Fraud', 0: 'Legit'})

        fig_tier = px.bar(
            tier_df, x='amount_category', y='count', color='Status',
            barmode='stack',
            color_discrete_map={'Legit': '#10B981', 'Fraud': '#F43F5E'},
            title="Volume & Fraud Breakdown by Amount Tier"
        )
        st.plotly_chart(fig_tier, use_container_width=True)

# TAB 2: FLAGGED TRANSACTIONS DRILL-DOWN
with tab2:
    st.subheader("🚨 High-Risk Flagged Transactions (Live DB)")
    flagged_df = df_filtered[df_filtered['fraud_probability'] >= 0.50].sort_values(by='fraud_probability', ascending=False)
    
    st.write(f"Showing **{len(flagged_df)}** transactions flagged by the Random Forest model (Fraud Probability ≥ 50%).")

    if not flagged_df.empty:
        display_cols = [
            'transaction_id', 'timestamp', 'amount', 'sender', 'receiver',
            'transaction_type', 'location', 'fraud_probability', 'review_status', 'is_night_txn'
        ]
        st.dataframe(
            flagged_df[display_cols].style.format({
                'amount': '₹{:,.2f}',
                'fraud_probability': '{:.1%}'
            }),
            use_container_width=True,
            height=350
        )

        st.markdown("### 🔍 Select Transaction for Deep Inspection")
        selected_txn_id = st.selectbox("Choose Transaction ID", flagged_df['transaction_id'].tolist())
        
        if selected_txn_id:
            txn_row = flagged_df[flagged_df['transaction_id'] == selected_txn_id].iloc[0]
            
            d_col1, d_col2, d_col3 = st.columns(3)
            with d_col1:
                st.info(f"**Transaction ID:** {txn_row['transaction_id']}")
                st.write(f"**Amount:** ₹{txn_row['amount']:,.2f}")
                st.write(f"**Timestamp:** {txn_row['timestamp']}")
                st.write(f"**Location:** {txn_row['location']}")
            with d_col2:
                st.warning(f"**Sender:** {txn_row['sender']}")
                st.write(f"**Receiver:** {txn_row['receiver']}")
                st.write(f"**Device ID:** {txn_row['device_id']}")
                st.write(f"**Txn Type:** {txn_row['transaction_type']}")
            with d_col3:
                prob_val = txn_row['fraud_probability'] * 100
                st.error(f"**Fraud Probability:** {prob_val:.1f}%")
                st.write(f"**Sender 24h Freq:** {txn_row['sender_txn_freq_24h']} txns")
                st.write(f"**Time Since Last Txn:** {txn_row['time_since_last_txn_mins']:.1f} mins")
                st.write(f"**Night Hours (11PM-5AM):** {'Yes 🌙' if txn_row['is_night_txn'] else 'No ☀️'}")
    else:
        st.success("🎉 No flagged transactions under current filter criteria.")

# TAB 3: MODEL EVALUATION & METRICS
with tab3:
    st.subheader("🤖 Random Forest Classifier Performance & Evaluation")
    
    if metrics:
        m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
        m_col1.metric("Accuracy", f"{metrics['accuracy']*100:.2f}%")
        m_col2.metric("Precision", f"{metrics['precision']*100:.2f}%")
        m_col3.metric("Recall", f"{metrics['recall']*100:.2f}%")
        m_col4.metric("F1-Score", f"{metrics['f1_score']*100:.2f}%")
        m_col5.metric("ROC-AUC", f"{metrics['roc_auc']:.4f}")

        st.caption(f"Last trained on: **{metrics['trained_at']}** | Total Evaluation Samples: **{metrics['sample_count']}**")

        c_cm, c_fi = st.columns(2)
        
        with c_cm:
            st.markdown("### 🧩 Confusion Matrix (Held-out Test Set)")
            cm_data = np.array(metrics['confusion_matrix'])
            fig_cm, ax = plt.subplots(figsize=(5, 4))
            sns.heatmap(cm_data, annot=True, fmt='d', cmap='Blues',
                        xticklabels=['Predicted Legit', 'Predicted Fraud'],
                        yticklabels=['Actual Legit', 'Actual Fraud'], ax=ax)
            plt.title("Confusion Matrix Heatmap")
            st.pyplot(fig_cm)

        with c_fi:
            st.markdown("### ⚡ Feature Importance Ranking")
            fi_data = metrics['feature_importances']
            fi_df = pd.DataFrame(list(fi_data.items()), columns=['Feature', 'Importance']).sort_values(by='Importance', ascending=True)

            fig_fi = px.bar(
                fi_df, x='Importance', y='Feature', orientation='h',
                color='Importance', color_continuous_scale='Viridis',
                title="Random Forest Feature Importance Scores"
            )
            st.plotly_chart(fig_fi, use_container_width=True)

    else:
        st.warning("No model metrics available yet.")

# TAB 4: STATIC TABLEAU EXPORT CHARTS
with tab4:
    st.subheader("📄 Static Tableau-Style Exportable Figures")
    st.write("Generated high-resolution publication figures ready for export or report inclusion.")

    fig_tab, axes = plt.subplots(2, 2, figsize=(12, 8))
    sns.set_theme(style="whitegrid")

    # Chart 1: Amount vs Fraud Probability
    sns.scatterplot(data=df_filtered, x='amount', y='fraud_probability', hue='is_fraud', palette={0: 'teal', 1: 'red'}, alpha=0.7, ax=axes[0,0])
    axes[0,0].set_title("1. Transaction Amount vs Fraud Probability")
    axes[0,0].set_xlabel("Amount (INR)")
    axes[0,0].set_ylabel("Fraud Probability")

    # Chart 2: Hourly Fraud Distribution
    sns.histplot(data=df_filtered, x='transaction_hour', hue='is_fraud', multiple='stack', palette={0: 'skyblue', 1: 'salmon'}, bins=24, ax=axes[0,1])
    axes[0,1].set_title("2. Hourly Distribution (Legit vs Fraud)")

    # Chart 3: Type Breakdown
    sns.countplot(data=df_filtered, x='transaction_type', hue='is_fraud', palette='Set2', ax=axes[1,0])
    axes[1,0].set_title("3. Transaction Count by Type")

    # Chart 4: Fraud Rate by Amount Tier
    tier_order = ['LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH']
    sns.barplot(data=df_filtered, x='amount_category', y='is_fraud', order=tier_order, palette='Reds', ci=None, ax=axes[1,1])
    axes[1,1].set_title("4. Fraud Rate by Amount Tier")
    axes[1,1].set_ylabel("Fraud Rate")

    plt.tight_layout()
    st.pyplot(fig_tab)
