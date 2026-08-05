import random
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def generate_upi_dataset(num_records=5500, random_seed=42):
    """
    Generates a realistic synthetic UPI transaction dataset with realistic
    behavior patterns and fraud indicators.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    locations = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Jaipur', 'Ahmedabad', 'Lucknow']
    txn_types = ['P2P', 'P2M', 'BILL_PAYMENT', 'ONLINE_SHOPPING', 'RECHARGE']
    
    # Generate user pool
    senders = [f"user_{i:04d}@upi" for i in range(1, 401)]
    merchants = [f"merchant_{i:03d}@okbiz" for i in range(1, 101)] + [f"store_{i:03d}@ybl" for i in range(1, 101)]
    users_all = senders + merchants
    
    # User device mapping
    user_devices = {u: [f"DEV_{uuid.uuid4().hex[:8].upper()}"] for u in senders}

    start_date = datetime.now() - timedelta(days=60)
    data = []

    for i in range(num_records):
        txn_id = f"TXN_UPI_{100000 + i}"
        
        # Determine if this transaction should be fraudulent (~5% fraud rate)
        is_fraud = 1 if random.random() < 0.052 else 0

        sender = random.choice(senders)
        
        # Fraud patterns
        if is_fraud:
            # Fraudulent characteristics:
            # 1. Unusual high amount or strange amounts
            amount = round(random.choice([
                random.uniform(15000, 95000),
                random.uniform(49000, 100000),
                random.uniform(25000, 75000)
            ]), 2)
            
            # 2. Night hours (11 PM to 5 AM) or rapid velocity
            if random.random() < 0.65:
                # Night time
                hour = random.choice([23, 0, 1, 2, 3, 4])
            else:
                hour = random.randint(5, 22)
            
            # 3. High tendency to send to unknown new merchants or random receivers
            receiver = random.choice(merchants if random.random() < 0.7 else senders)
            while receiver == sender:
                receiver = random.choice(senders)
                
            # 4. Unknown or new device ID
            if random.random() < 0.7:
                device_id = f"DEV_FRAUD_{uuid.uuid4().hex[:8].upper()}"
            else:
                device_id = user_devices[sender][0]
                
            txn_type = random.choice(['P2P', 'ONLINE_SHOPPING', 'P2M'])
            location = random.choice(locations)
            
        else:
            # Normal transaction characteristics
            # Most UPI txns are smaller (₹50 to ₹5000)
            if random.random() < 0.7:
                amount = round(float(np.random.exponential(scale=600) + 10), 2)
                amount = min(amount, 15000)
            elif random.random() < 0.9:
                amount = round(random.uniform(1000, 8000), 2)
            else:
                amount = round(random.uniform(8000, 25000), 2)
                
            p_dist = np.array([0.01,0.01,0.01,0.01,0.01,0.02,0.03,0.05,0.06,0.07,0.08,0.08,0.08,0.07,0.07,0.07,0.08,0.08,0.06,0.05,0.04,0.02,0.01,0.01])
            p_dist = p_dist / p_dist.sum()
            hour = int(np.random.choice(range(24), p=p_dist))
            
            receiver = random.choice(merchants if random.random() < 0.65 else senders)
            while receiver == sender:
                receiver = random.choice(senders)
                
            device_id = user_devices[sender][0]
            txn_type = random.choice(txn_types)
            location = random.choice(locations)

        # Random timestamp over 60 days matching hour
        days_offset = random.randint(0, 59)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        dt = start_date + timedelta(days=days_offset, hours=hour, minutes=minute, seconds=second)
        timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        data.append({
            'transaction_id': txn_id,
            'timestamp': timestamp_str,
            'amount': amount,
            'sender': sender,
            'receiver': receiver,
            'transaction_type': txn_type,
            'device_id': device_id,
            'location': location,
            'is_fraud': is_fraud
        })

    df = pd.DataFrame(data)
    df.sort_values(by='timestamp', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

if __name__ == "__main__":
    df = generate_upi_dataset(num_records=5500)
    df.to_csv("data_pipeline/synthetic_upi_transactions.csv", index=False)
    print(f"Generated synthetic dataset with {len(df)} rows.")
    print(f"Fraud count: {df['is_fraud'].sum()} ({df['is_fraud'].mean()*100:.2f}%)")
