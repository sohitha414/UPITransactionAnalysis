import pandas as pd
import numpy as np

def compute_engineered_features(df_raw):
    """
    Takes a DataFrame of raw transactions and computes engineered features:
    - transaction_hour
    - day_of_week
    - amount_category
    - sender_txn_freq_24h
    - receiver_txn_freq_24h
    - time_since_last_txn_mins
    - is_night_txn
    - is_high_value
    """
    df = df_raw.copy()
    
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values(by='timestamp').reset_index(drop=True)
    
    # Time-based features
    df['transaction_hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_night_txn'] = df['transaction_hour'].apply(lambda h: 1 if h in [23, 0, 1, 2, 3, 4] else 0)
    
    # Amount categories
    def get_amount_category(amt):
        if amt < 500:
            return 'LOW'
        elif amt < 3000:
            return 'MEDIUM'
        elif amt < 15000:
            return 'HIGH'
        else:
            return 'VERY_HIGH'
            
    df['amount_category'] = df['amount'].apply(get_amount_category)
    df['is_high_value'] = (df['amount'] >= 15000).astype(int)
    
    # Calculate rolling frequency and time gaps efficiently
    sender_freqs = []
    receiver_freqs = []
    time_gaps = []
    
    # Map to track last transaction timestamp per sender
    last_txn_time = {}
    
    # Group timestamps for rolling 24h count
    # For speed on large datasets, we use indexed time lookups
    timestamps = df['timestamp'].values
    senders = df['sender'].values
    receivers = df['receiver'].values
    
    for i in range(len(df)):
        curr_ts = pd.Timestamp(timestamps[i])
        s = senders[i]
        r = receivers[i]
        
        # Time since last transaction for sender (in minutes)
        if s in last_txn_time:
            gap = (curr_ts - last_txn_time[s]).total_seconds() / 60.0
            time_gaps.append(max(0.1, round(gap, 2)))
        else:
            time_gaps.append(1440.0) # default 24h for first transaction
        last_txn_time[s] = curr_ts
        
        # 24h window count
        window_start = curr_ts - pd.Timedelta(hours=24)
        
        # Count sender txns in past 24h prior to or including current
        # Slice search window for efficiency
        sub_df = df.iloc[max(0, i - 150):i + 1]
        s_count = ((sub_df['sender'] == s) & (sub_df['timestamp'] >= window_start)).sum()
        r_count = ((sub_df['receiver'] == r) & (sub_df['timestamp'] >= window_start)).sum()
        
        sender_freqs.append(int(s_count))
        receiver_freqs.append(int(r_count))
        
    df['sender_txn_freq_24h'] = sender_freqs
    df['receiver_txn_freq_24h'] = receiver_freqs
    df['time_since_last_txn_mins'] = time_gaps
    
    features_df = df[[
        'transaction_id',
        'transaction_hour',
        'day_of_week',
        'amount_category',
        'sender_txn_freq_24h',
        'receiver_txn_freq_24h',
        'time_since_last_txn_mins',
        'is_night_txn',
        'is_high_value'
    ]]
    
    return features_df, df

if __name__ == "__main__":
    import os
    if os.path.exists("data_pipeline/synthetic_upi_transactions.csv"):
        raw_df = pd.read_csv("data_pipeline/synthetic_upi_transactions.csv")
        feats, full = compute_engineered_features(raw_df)
        print("Engineered features computed successfully:")
        print(feats.head())
