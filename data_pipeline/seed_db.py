import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.generate_dataset import generate_upi_dataset
from data_pipeline.feature_engineering import compute_engineered_features
from data_pipeline.db import init_db, save_transactions_to_db, get_connection

def seed_database():
    print("--- 1. Initializing Database Schema ---")
    init_db()

    print("--- 2. Generating 5,500 Synthetic UPI Transactions ---")
    df_raw = generate_upi_dataset(num_records=5500, random_seed=42)
    print(f"Generated {len(df_raw)} raw transactions. Fraud rate: {df_raw['is_fraud'].mean()*100:.2f}%")

    print("--- 3. Computing Engineered Features ---")
    features_df, _ = compute_engineered_features(df_raw)
    print(f"Computed features for {len(features_df)} rows.")

    print("--- 4. Seeding Database ---")
    save_transactions_to_db(df_raw, features_df)

    # Verify counts
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM transactions")
    t_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM engineered_features")
    f_count = c.fetchone()[0]
    conn.close()

    print(f"Database successfully seeded! Transactions: {t_count}, Engineered Features: {f_count}")

if __name__ == "__main__":
    seed_database()
