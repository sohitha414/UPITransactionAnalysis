# UPI Transaction Analysis & Fraud Detection Pipeline

An end-to-end Machine Learning fraud detection pipeline and real-time risk intelligence dashboard for UPI (Unified Payments Interface) transactions.

---

## 📁 Full Project Structure

```
.
├── api/
│   └── main.py                     # FastAPI backend serving predictions, review actions, and analytics
├── data_pipeline/
│   ├── generate_dataset.py         # Synthetic UPI transaction generator (~5,500+ rows)
│   ├── feature_engineering.py      # Derive 24h rolling velocity, night flags, time-delta, and categories
│   ├── schema.sql                  # PostgreSQL & SQLite database schema
│   ├── db.py                       # SQLite / PostgreSQL database connection & query manager
│   └── seed_db.py                  # Seeding script populating transactions & engineered features
├── ml/
│   ├── eda_analysis.py             # Exploratory Data Analysis (EDA), missing checks, IQR outlier bounds
│   ├── train_model.py              # Random Forest classifier training, evaluation, & metric logging
│   ├── predict.py                  # Live inference module loading model.joblib for single & batch scoring
│   └── model.joblib                # Trained Scikit-Learn Pipeline artifact
├── dashboard/
│   └── app.py                      # Interactive Streamlit analytics dashboard with Plotly & Tableau exports
├── src/                            # React + Tailwind Admin Panel Frontend
│   ├── components/
│   │   ├── Navbar.tsx              # Top navigation bar & pipeline status indicator
│   │   ├── TransactionAdmin.tsx    # Searchable, sortable, paginated transaction review table
│   │   ├── FraudPredictor.tsx      # Real-time fraud scoring simulator & DB ingestion form
│   │   ├── StreamlitView.tsx       # Streamlit embedded view
│   │   ├── ModelHealth.tsx         # Live ML model evaluation metrics & re-train trigger
│   │   └── EdaInspector.tsx        # Preprocessing, missing values, & IQR outlier report
│   ├── types/                      # TypeScript interface declarations
│   └── App.tsx                     # Main React entry component
├── server.ts                       # Express + Vite proxy server unifying Port 3000
└── README.md                       # Comprehensive setup guide & architectural documentation
```

---

## 🛠️ Step-by-step Setup & Execution Instructions

### 1. Database Creation & Seeding
To initialize the database schema and generate 5,500 synthetic UPI transactions:
```bash
python3 data_pipeline/seed_db.py
```

### 2. Exploratory Data Analysis (EDA)
To run missing value checks, IQR outlier bounds, and category distributions:
```bash
python3 ml/eda_analysis.py
```

### 3. Model Training & Metric Logging
To train the Random Forest Classifier, compute test-set metrics (Precision, Recall, F1, ROC-AUC), and save `model.joblib`:
```bash
python3 ml/train_model.py
```

### 4. Start FastAPI REST Backend
To run the FastAPI server on port 8000:
```bash
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 5. Start Streamlit Interactive Analytics Dashboard
To launch the Streamlit dashboard on port 8501:
```bash
python3 -m streamlit run dashboard/app.py --server.port 8501
```

### 6. Start Unified Full-Stack Application (Express + Vite React Frontend on Port 3000)
To start the unified server on port 3000:
```bash
npm run dev
```

---

## 📊 Live Database & Model Verification (Proof of Dynamic Queries)

Every metric, KPI card, and interactive chart in the Streamlit and React dashboards is computed dynamically from the database and the trained Random Forest model.

### 1. Total Volume & Fraud Rate KPI Cards
```python
# From /api/main.py and /dashboard/app.py
conn = get_connection()
c = conn.cursor()
c.execute("SELECT COUNT(*), SUM(amount), AVG(amount) FROM transactions")
row_all = c.fetchone()

c.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE is_fraud = 1 OR fraud_probability >= 0.5")
row_fraud = c.fetchone()
fraud_rate = (row_fraud[0] / row_all[0]) * 100
```

### 2. Hourly Transaction Volume & Fraud Rate Chart
```sql
SELECT f.transaction_hour, 
       COUNT(*) as total_count,
       SUM(CASE WHEN t.is_fraud = 1 OR t.fraud_probability >= 0.5 THEN 1 ELSE 0 END) as fraud_count
FROM transactions t
JOIN engineered_features f ON t.transaction_id = f.transaction_id
GROUP BY f.transaction_hour
ORDER BY f.transaction_hour ASC;
```

### 3. Live ML Model Scoring Query (Inference)
```python
# From /ml/predict.py
model = joblib.load("ml/model.joblib")
fraud_probability = model.predict_proba(df_features)[0, 1]
is_fraud = bool(fraud_probability >= 0.50)
```

---

## 🛡️ Key ML Features & Engineered Signals
- `transaction_hour`: Hour of transaction (0-23)
- `is_night_txn`: Flag for high-risk hours (11 PM - 5 AM)
- `amount_category`: Bucketed transaction tier (LOW, MEDIUM, HIGH, VERY_HIGH)
- `sender_txn_freq_24h`: Rolling 24-hour transaction frequency count per sender
- `receiver_txn_freq_24h`: Rolling 24-hour transaction frequency count per receiver
- `time_since_last_txn_mins`: Time delta since sender's previous transaction (detects rapid velocity spikes)
