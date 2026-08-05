import os
import sys
import json
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from data_pipeline.db import get_connection, init_db
from data_pipeline.feature_engineering import compute_engineered_features
from ml.predict import predict_transaction
from ml.train_model import train_and_evaluate_model

app = FastAPI(
    title="UPI Transaction Analysis & Fraud Detection API",
    description="REST API powering live transaction scoring, fraud analytics, review workflows, and model evaluation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database schema on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Pydantic Request/Response Models
class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0, example=12500.0)
    sender: str = Field(..., example="user_0012@upi")
    receiver: str = Field(..., example="store_888@ybl")
    transaction_type: str = Field(default="P2P", example="P2P")
    device_id: Optional[str] = Field(default=None, example="DEV_8A9B0C")
    location: Optional[str] = Field(default="Mumbai", example="Mumbai")
    timestamp: Optional[str] = None

class TransactionReviewUpdate(BaseModel):
    review_status: str = Field(..., example="verified_legit") # pending, verified_legit, confirmed_fraud
    review_notes: Optional[str] = Field(default="", example="Customer verified via OTP call.")

class PredictRequest(BaseModel):
    amount: float
    sender: str
    receiver: str
    transaction_type: str = "P2P"
    device_id: Optional[str] = "DEV_CURRENT"
    location: Optional[str] = "Mumbai"
    timestamp: Optional[str] = None

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "UPI Fraud Analysis API", "timestamp": datetime.now().isoformat()}

@app.get("/api/transactions")
def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_fraud: Optional[int] = None,
    review_status: Optional[str] = None,
    transaction_type: Optional[str] = None,
    sort_by: str = "timestamp",
    sort_dir: str = "desc"
):
    """
    Searchable, paginated list of transactions directly from PostgreSQL / SQLite database.
    """
    offset = (page - 1) * limit
    conn = get_connection()
    c = conn.cursor()

    conditions = ["1=1"]
    params = []

    if search:
        s_term = f"%{search}%"
        conditions.append("(transaction_id LIKE ? OR sender LIKE ? OR receiver LIKE ? OR location LIKE ?)")
        params.extend([s_term, s_term, s_term, s_term])

    if is_fraud is not None:
        conditions.append("is_fraud = ?")
        params.append(is_fraud)

    if review_status:
        conditions.append("review_status = ?")
        params.append(review_status)

    if transaction_type:
        conditions.append("transaction_type = ?")
        params.append(transaction_type)

    where_clause = " AND ".join(conditions)
    valid_sorts = {"timestamp": "timestamp", "amount": "amount", "fraud_probability": "fraud_probability", "id": "id"}
    sort_column = valid_sorts.get(sort_by, "timestamp")
    order_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"

    # Count query
    count_query = f"SELECT COUNT(*) FROM transactions WHERE {where_clause}"
    c.execute(count_query, params)
    total_records = c.fetchone()[0]

    # Data query
    data_query = f"""
    SELECT id, transaction_id, timestamp, amount, sender, receiver,
           transaction_type, device_id, location, is_fraud,
           fraud_probability, review_status, review_notes, created_at
    FROM transactions
    WHERE {where_clause}
    ORDER BY {sort_column} {order_direction}
    LIMIT ? OFFSET ?
    """
    c.execute(data_query, params + [limit, offset])
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    total_pages = (total_records + limit - 1) // limit if limit > 0 else 1

    return {
        "page": page,
        "limit": limit,
        "total_records": total_records,
        "total_pages": total_pages,
        "data": rows
    }

@app.post("/api/predict")
def predict_fraud_score(req: PredictRequest):
    """
    Predicts fraud score for a transaction without saving to DB.
    """
    txn_dict = req.dict()
    if not txn_dict.get("timestamp"):
        txn_dict["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    prediction = predict_transaction(txn_dict)
    return {
        "status": "success",
        "input": txn_dict,
        "prediction": prediction
    }

@app.post("/api/transactions")
def create_transaction(req: TransactionCreate):
    """
    Inserts a new transaction into DB and automatically scores it with ML model.
    """
    txn_id = f"TXN_UPI_{uuid.uuid4().hex[:8].upper()}"
    ts = req.timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device = req.device_id or f"DEV_{uuid.uuid4().hex[:6].upper()}"

    txn_dict = {
        "transaction_id": txn_id,
        "timestamp": ts,
        "amount": req.amount,
        "sender": req.sender,
        "receiver": req.receiver,
        "transaction_type": req.transaction_type,
        "device_id": device,
        "location": req.location
    }

    # Run ML prediction
    prediction = predict_transaction(txn_dict)
    fraud_prob = prediction["fraud_probability"]
    is_fraud = 1 if prediction["is_fraud"] else 0

    # Save to DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO transactions (
        transaction_id, timestamp, amount, sender, receiver,
        transaction_type, device_id, location, is_fraud, fraud_probability, review_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        txn_id, ts, req.amount, req.sender, req.receiver,
        req.transaction_type, device, req.location, is_fraud, fraud_prob
    ))

    # Compute and save engineered features
    import pandas as pd
    raw_df = pd.DataFrame([txn_dict])
    feats_df, _ = compute_engineered_features(raw_df)
    feat_row = feats_df.iloc[0].to_dict()

    c.execute("""
    INSERT OR REPLACE INTO engineered_features (
        transaction_id, transaction_hour, day_of_week, amount_category,
        sender_txn_freq_24h, receiver_txn_freq_24h, time_since_last_txn_mins,
        is_night_txn, is_high_value
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        txn_id, feat_row['transaction_hour'], feat_row['day_of_week'], feat_row['amount_category'],
        feat_row['sender_txn_freq_24h'], feat_row['receiver_txn_freq_24h'], feat_row['time_since_last_txn_mins'],
        feat_row['is_night_txn'], feat_row['is_high_value']
    ))

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": "Transaction created and scored successfully.",
        "transaction_id": txn_id,
        "is_fraud": bool(is_fraud),
        "fraud_probability": fraud_prob,
        "risk_level": prediction["risk_level"],
        "risk_reasons": prediction["risk_reasons"]
    }

@app.patch("/api/transactions/{transaction_id}/review")
def review_transaction(transaction_id: str, update: TransactionReviewUpdate):
    """
    Manual review action updating review status and notes in the database.
    """
    valid_statuses = ["pending", "verified_legit", "confirmed_fraud"]
    if update.review_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid review_status. Must be one of {valid_statuses}")

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    UPDATE transactions 
    SET review_status = ?, review_notes = ?
    WHERE transaction_id = ?
    """, (update.review_status, update.review_notes or "", transaction_id))

    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found.")

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "message": f"Transaction {transaction_id} marked as {update.review_status}",
        "transaction_id": transaction_id,
        "review_status": update.review_status
    }

@app.get("/api/metrics")
def get_model_metrics():
    """
    Fetches latest trained model evaluation metrics directly from DB.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT trained_at, model_version, sample_count, accuracy, precision,
           recall, f1_score, roc_auc, confusion_matrix, feature_importances
    FROM model_metrics
    ORDER BY id DESC
    LIMIT 1
    """)
    row = c.fetchone()
    conn.close()

    if not row:
        return {"status": "no_metrics", "message": "No model metrics recorded yet. Please run training pipeline."}

    data = dict(row)
    data["confusion_matrix"] = json.loads(data["confusion_matrix"])
    data["feature_importances"] = json.loads(data["feature_importances"])

    return {
        "status": "success",
        "metrics": data
    }

@app.post("/api/train")
def trigger_training():
    """
    Triggers re-training pipeline on DB data and updates saved model & metrics.
    """
    try:
        results = train_and_evaluate_model()
        return {
            "status": "success",
            "message": "Model re-trained and metrics persisted to DB.",
            "metrics": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/summary")
def get_analytics_summary():
    """
    Live KPI summaries computed directly from the database.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*), SUM(amount), AVG(amount) FROM transactions")
    row_all = c.fetchone()
    total_txns = row_all[0] or 0
    total_amount = round(row_all[1] or 0.0, 2)
    avg_amount = round(row_all[2] or 0.0, 2)

    c.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE is_fraud = 1 OR fraud_probability >= 0.5")
    row_fraud = c.fetchone()
    flagged_count = row_fraud[0] or 0
    flagged_amount = round(row_fraud[1] or 0.0, 2)

    c.execute("SELECT COUNT(*) FROM transactions WHERE review_status != 'pending'")
    reviewed_count = c.fetchone()[0] or 0

    fraud_rate = round((flagged_count / total_txns * 100), 2) if total_txns > 0 else 0.0

    conn.close()

    return {
        "total_transactions": total_txns,
        "flagged_transactions": flagged_count,
        "fraud_rate_percentage": fraud_rate,
        "total_volume_inr": total_amount,
        "flagged_volume_inr": flagged_amount,
        "avg_transaction_amount": avg_amount,
        "reviewed_count": reviewed_count
    }

@app.get("/api/analytics/charts")
def get_analytics_charts():
    """
    Live aggregated chart datasets computed directly from database queries.
    """
    conn = get_connection()
    c = conn.cursor()

    # 1. Transactions by Hour
    c.execute("""
    SELECT f.transaction_hour, 
           COUNT(*) as total_count,
           SUM(CASE WHEN t.is_fraud = 1 OR t.fraud_probability >= 0.5 THEN 1 ELSE 0 END) as fraud_count
    FROM transactions t
    JOIN engineered_features f ON t.transaction_id = f.transaction_id
    GROUP BY f.transaction_hour
    ORDER BY f.transaction_hour ASC
    """)
    by_hour = [dict(r) for r in c.fetchall()]

    # 2. Transactions by Type
    c.execute("""
    SELECT transaction_type,
           COUNT(*) as total_count,
           SUM(CASE WHEN is_fraud = 1 OR fraud_probability >= 0.5 THEN 1 ELSE 0 END) as fraud_count,
           AVG(amount) as avg_amount
    FROM transactions
    GROUP BY transaction_type
    ORDER BY total_count DESC
    """)
    by_type = [dict(r) for r in c.fetchall()]

    # 3. Amount Tier Distribution
    c.execute("""
    SELECT f.amount_category,
           COUNT(*) as total_count,
           SUM(CASE WHEN t.is_fraud = 1 OR t.fraud_probability >= 0.5 THEN 1 ELSE 0 END) as fraud_count
    FROM transactions t
    JOIN engineered_features f ON t.transaction_id = f.transaction_id
    GROUP BY f.amount_category
    """)
    by_tier = [dict(r) for r in c.fetchall()]

    # 4. Daily Trend
    c.execute("""
    SELECT DATE(timestamp) as txn_date,
           COUNT(*) as total_count,
           SUM(CASE WHEN is_fraud = 1 OR fraud_probability >= 0.5 THEN 1 ELSE 0 END) as fraud_count,
           SUM(amount) as total_amount
    FROM transactions
    GROUP BY DATE(timestamp)
    ORDER BY txn_date ASC
    """)
    by_date = [dict(r) for r in c.fetchall()]

    conn.close()

    return {
        "by_hour": by_hour,
        "by_type": by_type,
        "by_tier": by_tier,
        "by_date": by_date
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
