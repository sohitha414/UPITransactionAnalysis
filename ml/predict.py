import os
import sys
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_pipeline.db import get_connection

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

_cached_model = None

def get_model():
    global _cached_model
    if _cached_model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Train model first.")
        _cached_model = joblib.load(MODEL_PATH)
    return _cached_model

def compute_single_features(txn):
    """
    Computes feature row for a single incoming transaction dict.
    Fields expected: amount, timestamp, sender, receiver, transaction_type
    """
    ts = pd.to_datetime(txn.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    amount = float(txn.get('amount', 0.0))
    sender = str(txn.get('sender', ''))
    receiver = str(txn.get('receiver', ''))
    txn_type = str(txn.get('transaction_type', 'P2P'))

    hour = ts.hour
    day = ts.dayofweek
    is_night = 1 if hour in [23, 0, 1, 2, 3, 4] else 0

    if amount < 500:
        amt_cat = 'LOW'
    elif amount < 3000:
        amt_cat = 'MEDIUM'
    elif amount < 15000:
        amt_cat = 'HIGH'
    else:
        amt_cat = 'VERY_HIGH'

    is_high_val = 1 if amount >= 15000 else 0

    # Query DB for sender/receiver rolling frequency & time gap if available
    s_freq = 1
    r_freq = 1
    time_gap = 1440.0

    try:
        conn = get_connection()
        c = conn.cursor()
        
        # Last 24h count for sender
        c.execute("""
            SELECT COUNT(*), MAX(timestamp) FROM transactions 
            WHERE sender = ? AND timestamp >= datetime(?, '-24 hours')
        """, (sender, ts.strftime("%Y-%m-%d %H:%M:%S")))
        row = c.fetchone()
        if row and row[0]:
            s_freq = row[0] + 1
            if row[1]:
                last_ts = pd.to_datetime(row[1])
                gap = (ts - last_ts).total_seconds() / 60.0
                time_gap = max(0.1, round(gap, 2))

        # Last 24h count for receiver
        c.execute("""
            SELECT COUNT(*) FROM transactions 
            WHERE receiver = ? AND timestamp >= datetime(?, '-24 hours')
        """, (receiver, ts.strftime("%Y-%m-%d %H:%M:%S")))
        r_row = c.fetchone()
        if r_row and r_row[0]:
            r_freq = r_row[0] + 1

        conn.close()
    except Exception:
        pass

    feat_dict = {
        'amount': amount,
        'transaction_type': txn_type,
        'amount_category': amt_cat,
        'transaction_hour': hour,
        'day_of_week': day,
        'sender_txn_freq_24h': s_freq,
        'receiver_txn_freq_24h': r_freq,
        'time_since_last_txn_mins': time_gap,
        'is_night_txn': is_night,
        'is_high_value': is_high_val
    }

    df_feats = pd.DataFrame([feat_dict])
    return df_feats, feat_dict

def predict_transaction(txn):
    """
    Given a transaction dict, computes features, loads ML model,
    returns prediction dict with probability, boolean flag, and risk explanation.
    """
    model = get_model()
    df_feats, feat_dict = compute_single_features(txn)
    
    proba = float(model.predict_proba(df_feats)[0, 1])
    is_fraud = bool(proba >= 0.50)

    # Risk level classification
    if proba < 0.25:
        risk_level = "LOW"
    elif proba < 0.50:
        risk_level = "MEDIUM"
    elif proba < 0.80:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    # Explain risk factors
    reasons = []
    if feat_dict['is_night_txn']:
        reasons.append("Unusual transaction hour (Night: 11 PM - 5 AM)")
    if feat_dict['is_high_value']:
        reasons.append(f"High-value amount (₹{feat_dict['amount']:,.2f})")
    if feat_dict['sender_txn_freq_24h'] >= 4:
        reasons.append(f"High transaction velocity ({feat_dict['sender_txn_freq_24h']} in 24h)")
    if feat_dict['time_since_last_txn_mins'] < 5.0:
        reasons.append(f"Rapid successive transaction ({feat_dict['time_since_last_txn_mins']:.1f} mins since last)")
    if not reasons and is_fraud:
        reasons.append("Anomalous pattern detected by Random Forest model ensemble")

    return {
        'fraud_probability': round(proba, 4),
        'fraud_percentage': round(proba * 100, 2),
        'is_fraud': is_fraud,
        'risk_level': risk_level,
        'risk_reasons': reasons,
        'engineered_features': feat_dict
    }

if __name__ == "__main__":
    sample_txn = {
        'amount': 45000.0,
        'transaction_type': 'P2P',
        'sender': 'user_0001@upi',
        'receiver': 'unknown_merchant@ybl',
        'timestamp': datetime.now().strftime("%Y-%m-%d 02:15:00")
    }
    res = predict_transaction(sample_txn)
    print("Inference result for sample transaction:")
    print(res)
