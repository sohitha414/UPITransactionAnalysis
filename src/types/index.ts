export interface Transaction {
  id: number;
  transaction_id: string;
  timestamp: string;
  amount: number;
  sender: string;
  receiver: string;
  transaction_type: string;
  device_id: string;
  location: string;
  is_fraud: number;
  fraud_probability: number;
  review_status: 'pending' | 'verified_legit' | 'confirmed_fraud';
  review_notes?: string;
  created_at?: string;
}

export interface PaginatedTransactionsResponse {
  page: number;
  limit: number;
  total_records: number;
  total_pages: number;
  data: Transaction[];
}

export interface AnalyticsSummary {
  total_transactions: number;
  flagged_transactions: number;
  fraud_rate_percentage: number;
  total_volume_inr: number;
  flagged_volume_inr: number;
  avg_transaction_amount: number;
  reviewed_count: number;
}

export interface ModelMetrics {
  trained_at: string;
  model_version: string;
  sample_count: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  confusion_matrix: number[][];
  feature_importances: Record<string, number>;
}

export interface PredictionResult {
  fraud_probability: number;
  fraud_percentage: number;
  is_fraud: boolean;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_reasons: string[];
  engineered_features: Record<string, any>;
}
