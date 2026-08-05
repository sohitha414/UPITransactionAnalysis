-- UPI Transaction Analysis Database Schema

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    sender VARCHAR(128) NOT NULL,
    receiver VARCHAR(128) NOT NULL,
    transaction_type VARCHAR(32) NOT NULL,
    device_id VARCHAR(64) NOT NULL,
    location VARCHAR(64) NOT NULL,
    is_fraud INTEGER DEFAULT 0,
    fraud_probability REAL DEFAULT 0.0,
    review_status VARCHAR(32) DEFAULT 'pending', -- pending, verified_legit, confirmed_fraud
    review_notes TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engineered_features (
    transaction_id VARCHAR(64) PRIMARY KEY,
    transaction_hour INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    amount_category VARCHAR(16) NOT NULL,
    sender_txn_freq_24h INTEGER NOT NULL,
    receiver_txn_freq_24h INTEGER NOT NULL,
    time_since_last_txn_mins REAL NOT NULL,
    is_night_txn INTEGER NOT NULL,
    is_high_value INTEGER NOT NULL,
    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS model_metrics (
    id SERIAL PRIMARY KEY,
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(32) NOT NULL,
    sample_count INTEGER NOT NULL,
    accuracy REAL NOT NULL,
    precision REAL NOT NULL,
    recall REAL NOT NULL,
    f1_score REAL NOT NULL,
    roc_auc REAL NOT NULL,
    confusion_matrix TEXT NOT NULL, -- JSON string [[TN, FP], [FN, TP]]
    feature_importances TEXT NOT NULL -- JSON string key-value object
);
