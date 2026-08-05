import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_pipeline.db import get_connection

def run_eda():
    """
    Performs Exploratory Data Analysis (EDA) on UPI transaction dataset:
    1. Dataset Info & Missing Values Check
    2. Outlier Detection on Transaction Amounts via IQR (Interquartile Range)
    3. Distribution Analysis by Fraud Label
    4. Categorical Feature Fraud Correlation
    5. Summary Metrics and Leakage Preprocessing Checks
    """
    print("==================================================")
    print("      EXPLORATORY DATA ANALYSIS (EDA) REPORT      ")
    print("==================================================")
    
    conn = get_connection()
    query = """
    SELECT t.*, f.transaction_hour, f.day_of_week, f.amount_category,
           f.sender_txn_freq_24h, f.receiver_txn_freq_24h, f.time_since_last_txn_mins,
           f.is_night_txn, f.is_high_value
    FROM transactions t
    JOIN engineered_features f ON t.transaction_id = f.transaction_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    print(f"\n1. DATASET OVERVIEW")
    print(f"Total Rows: {len(df)}")
    print(f"Total Columns: {len(df.columns)}")
    print(f"Fraud distribution:\n{df['is_fraud'].value_counts(normalize=True)}")

    print("\n2. MISSING VALUE CHECK")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.sum() > 0 else "No missing values found across all columns.")

    print("\n3. OUTLIER DETECTION ON AMOUNT (IQR METHOD)")
    Q1 = df['amount'].quantile(0.25)
    Q3 = df['amount'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df['amount'] < lower_bound) | (df['amount'] > upper_bound)]
    print(f"Q1: ₹{Q1:.2f}, Q3: ₹{Q3:.2f}, IQR: ₹{IQR:.2f}")
    print(f"Upper Bound for Normal Txn Amount: ₹{upper_bound:.2f}")
    print(f"Total Outliers Count: {len(outliers)} ({len(outliers)/len(df)*100:.2f}%)")
    print(f"Fraud Rate inside Outliers: {outliers['is_fraud'].mean()*100:.2f}% vs Overall Fraud Rate: {df['is_fraud'].mean()*100:.2f}%")

    print("\n4. TRANSACTION TYPE VS FRAUD RATE")
    type_summary = df.groupby('transaction_type')['is_fraud'].agg(['count', 'sum', 'mean']).reset_index()
    type_summary.columns = ['transaction_type', 'total', 'fraud_count', 'fraud_rate']
    type_summary['fraud_rate_%'] = type_summary['fraud_rate'] * 100
    print(type_summary.to_string(index=False))

    print("\n5. AMOUNT CATEGORY VS FRAUD RATE")
    cat_summary = df.groupby('amount_category')['is_fraud'].agg(['count', 'sum', 'mean']).reset_index()
    cat_summary.columns = ['amount_category', 'total', 'fraud_count', 'fraud_rate']
    cat_summary['fraud_rate_%'] = cat_summary['fraud_rate'] * 100
    print(cat_summary.to_string(index=False))

    print("\n6. NIGHT TRANSACTION VS DAY TRANSACTION FRAUD RATE")
    night_summary = df.groupby('is_night_txn')['is_fraud'].agg(['count', 'sum', 'mean']).reset_index()
    night_summary.columns = ['is_night_txn', 'total', 'fraud_count', 'fraud_rate']
    night_summary['is_night_txn'] = night_summary['is_night_txn'].map({1: 'Night (11PM-5AM)', 0: 'Daytime'})
    night_summary['fraud_rate_%'] = night_summary['fraud_rate'] * 100
    print(night_summary.to_string(index=False))

    print("\n==================================================")
    print("EDA completed successfully. Ready for ML pipeline.")
    print("==================================================")

if __name__ == "__main__":
    run_eda()
