import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_pipeline.db import get_connection

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

def train_and_evaluate_model():
    """
    Trains a Random Forest classifier on engineered features from the DB,
    evaluates real test set metrics, saves model artifact, and logs performance to DB.
    """
    print("--- 1. Fetching Data from DB for Training ---")
    conn = get_connection()
    query = """
    SELECT t.transaction_id, t.amount, t.transaction_type, t.is_fraud,
           f.transaction_hour, f.day_of_week, f.amount_category,
           f.sender_txn_freq_24h, f.receiver_txn_freq_24h,
           f.time_since_last_txn_mins, f.is_night_txn, f.is_high_value
    FROM transactions t
    JOIN engineered_features f ON t.transaction_id = f.transaction_id
    """
    df = pd.read_sql_query(query, conn)

    if len(df) == 0:
        conn.close()
        raise ValueError("No transaction data found in database. Please run seed_db.py first.")

    # Target variable
    y = df['is_fraud'].values

    # Feature sets
    categorical_cols = ['transaction_type', 'amount_category']
    numerical_cols = [
        'amount', 'transaction_hour', 'day_of_week',
        'sender_txn_freq_24h', 'receiver_txn_freq_24h',
        'time_since_last_txn_mins', 'is_night_txn', 'is_high_value'
    ]

    X = df[categorical_cols + numerical_cols]

    # Stratified Train-Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"Dataset split: Train = {len(X_train)} rows, Test = {len(X_test)} rows.")

    # Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_cols),
            ('num', StandardScaler(), numerical_cols)
        ]
    )

    # Random Forest Classifier with balanced class weight to handle imbalance
    model_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=120,
            max_depth=12,
            min_samples_split=4,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])

    print("--- 2. Training Random Forest Classifier ---")
    model_pipeline.fit(X_train, y_train)

    print("--- 3. Evaluating Model on Held-out Test Set ---")
    y_pred = model_pipeline.predict(X_test)
    y_proba = model_pipeline.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_proba))
    cm = confusion_matrix(y_test, y_pred).tolist() # [[TN, FP], [FN, TP]]

    print(f"=== TEST METRICS ===")
    print(f"Accuracy:  {acc*100:.2f}%")
    print(f"Precision: {prec*100:.2f}%")
    print(f"Recall:    {rec*100:.2f}%")
    print(f"F1 Score:  {f1*100:.2f}%")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"Confusion Matrix (TN, FP, FN, TP): {cm}")

    # Extract Feature Importances
    preproc = model_pipeline.named_steps['preprocessor']
    cat_feature_names = list(preproc.named_transformers_['cat'].get_feature_names_out(categorical_cols))
    all_feature_names = cat_feature_names + numerical_cols
    importances = model_pipeline.named_steps['classifier'].feature_importances_

    feature_imp_dict = {
        name: round(float(imp), 4)
        for name, imp in sorted(zip(all_feature_names, importances), key=lambda x: x[1], reverse=True)
    }

    # Save trained model pipeline artifact
    joblib.dump(model_pipeline, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")

    print("--- 4. Scoring All Database Transactions with Trained Model ---")
    all_probas = model_pipeline.predict_proba(X)[:, 1]
    df['fraud_probability'] = np.round(all_probas, 4)

    # Batch update fraud probabilities in transactions table
    update_data = [(float(prob), tid) for prob, tid in zip(df['fraud_probability'], df['transaction_id'])]
    cursor = conn.cursor()
    cursor.executemany("UPDATE transactions SET fraud_probability = ? WHERE transaction_id = ?", update_data)

    print("--- 5. Persisting Model Metrics to Database ---")
    cursor.execute("""
    INSERT INTO model_metrics (
        model_version, sample_count, accuracy, precision, recall, f1_score, roc_auc,
        confusion_matrix, feature_importances
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "RF_v1.0",
        len(df),
        round(acc, 4),
        round(prec, 4),
        round(rec, 4),
        round(f1, 4),
        round(roc_auc, 4),
        json.dumps(cm),
        json.dumps(feature_imp_dict)
    ))

    conn.commit()
    conn.close()

    return {
        'accuracy': acc,
        'precision': prec,
        'recall': rec,
        'f1_score': f1,
        'roc_auc': roc_auc,
        'confusion_matrix': cm,
        'feature_importances': feature_imp_dict
    }

if __name__ == "__main__":
    train_and_evaluate_model()
