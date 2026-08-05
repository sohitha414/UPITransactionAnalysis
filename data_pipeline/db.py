import sqlite3
import os
import json
import pandas as pd

DB_FILE = os.getenv("DATABASE_PATH", "upi_analytics.db")

def get_connection():
    """Returns a SQLite connection with dict-like row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes schema tables if not existing."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        amount REAL NOT NULL,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        transaction_type TEXT NOT NULL,
        device_id TEXT NOT NULL,
        location TEXT NOT NULL,
        is_fraud INTEGER DEFAULT 0,
        fraud_probability REAL DEFAULT 0.0,
        review_status TEXT DEFAULT 'pending',
        review_notes TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create engineered_features table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS engineered_features (
        transaction_id TEXT PRIMARY KEY,
        transaction_hour INTEGER NOT NULL,
        day_of_week INTEGER NOT NULL,
        amount_category TEXT NOT NULL,
        sender_txn_freq_24h INTEGER NOT NULL,
        receiver_txn_freq_24h INTEGER NOT NULL,
        time_since_last_txn_mins REAL NOT NULL,
        is_night_txn INTEGER NOT NULL,
        is_high_value INTEGER NOT NULL,
        FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
    );
    """)

    # Create model_metrics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        model_version TEXT NOT NULL,
        sample_count INTEGER NOT NULL,
        accuracy REAL NOT NULL,
        precision REAL NOT NULL,
        recall REAL NOT NULL,
        f1_score REAL NOT NULL,
        roc_auc REAL NOT NULL,
        confusion_matrix TEXT NOT NULL,
        feature_importances TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def save_transactions_to_db(df_raw, features_df):
    """Saves raw transactions and engineered features to SQLite database."""
    conn = get_connection()
    
    # Upsert/Insert raw transactions
    raw_records = df_raw.to_dict(orient='records')
    conn.executemany("""
    INSERT OR REPLACE INTO transactions (
        transaction_id, timestamp, amount, sender, receiver,
        transaction_type, device_id, location, is_fraud,
        fraud_probability, review_status, review_notes
    ) VALUES (
        :transaction_id, :timestamp, :amount, :sender, :receiver,
        :transaction_type, :device_id, :location, :is_fraud,
        0.0, 'pending', ''
    );
    """, raw_records)

    # Insert engineered features
    feature_records = features_df.to_dict(orient='records')
    conn.executemany("""
    INSERT OR REPLACE INTO engineered_features (
        transaction_id, transaction_hour, day_of_week, amount_category,
        sender_txn_freq_24h, receiver_txn_freq_24h, time_since_last_txn_mins,
        is_night_txn, is_high_value
    ) VALUES (
        :transaction_id, :transaction_hour, :day_of_week, :amount_category,
        :sender_txn_freq_24h, :receiver_txn_freq_24h, :time_since_last_txn_mins,
        :is_night_txn, :is_high_value
    );
    """, feature_records)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
