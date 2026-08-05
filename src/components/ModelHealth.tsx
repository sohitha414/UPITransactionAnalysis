import React, { useState, useEffect } from 'react';
import { ModelMetrics } from '../types';
import { Cpu, RefreshCw, Activity, CheckCircle, BarChart, Layers } from 'lucide-react';

export const ModelHealth: React.FC = () => {
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [retraining, setRetraining] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/metrics');
      if (!res.ok) throw new Error('Failed to fetch model metrics');
      const data = await res.json();
      if (data.status === 'success') {
        setMetrics(data.metrics);
      } else {
        setError('No trained model metrics found.');
      }
    } catch (err: any) {
      setError(err.message || 'Error loading model metrics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleRetrain = async () => {
    if (!confirm('Re-train Random Forest classifier on latest database transactions?')) return;
    setRetraining(true);
    try {
      const res = await fetch('/api/train', { method: 'POST' });
      if (!res.ok) throw new Error('Model training execution failed');
      const data = await res.json();
      alert(`Model successfully trained! New Accuracy: ${(data.metrics.accuracy * 100).toFixed(2)}%`);
      fetchMetrics();
    } catch (err: any) {
      alert(err.message || 'Re-training failed');
    } finally {
      setRetraining(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="h-6 w-6 text-indigo-600" />
            Random Forest ML Model Pipeline & Health
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Evaluation metrics computed on held-out test set and persisted directly to PostgreSQL database.
          </p>
        </div>

        <button
          onClick={handleRetrain}
          disabled={retraining}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${retraining ? 'animate-spin' : ''}`} />
          {retraining ? 'Training Model...' : 'Re-train Model Pipeline'}
        </button>
      </div>

      {loading ? (
        <div className="py-20 text-center bg-white rounded-2xl border border-slate-200">
          <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-500 font-medium">Fetching evaluation metrics from DB...</p>
        </div>
      ) : metrics ? (
        <>
          {/* Top KPI Grid */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Accuracy</p>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {(metrics.accuracy * 100).toFixed(2)}%
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Precision</p>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {(metrics.precision * 100).toFixed(2)}%
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">Recall</p>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {(metrics.recall * 100).toFixed(2)}%
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">F1-Score</p>
              <p className="text-2xl font-black text-indigo-600 mt-1">
                {(metrics.f1_score * 100).toFixed(2)}%
              </p>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
              <p className="text-xs font-semibold text-slate-400 uppercase">ROC-AUC</p>
              <p className="text-2xl font-black text-emerald-600 mt-1">
                {metrics.roc_auc.toFixed(4)}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Confusion Matrix */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Layers className="h-5 w-5 text-indigo-600" />
                Confusion Matrix (Test Evaluation Set)
              </h3>
              <p className="text-xs text-slate-500">
                Performance breakdown on {metrics.sample_count} held-out validation samples.
              </p>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                  <p className="text-xs text-slate-500 font-semibold uppercase">True Negatives (TN)</p>
                  <p className="text-2xl font-bold text-slate-800 mt-1">{metrics.confusion_matrix[0]?.[0] ?? 0}</p>
                  <p className="text-[11px] text-slate-400 mt-0.5">Legit correctly identified</p>
                </div>
                <div className="bg-amber-50 p-4 rounded-xl border border-amber-200 text-center">
                  <p className="text-xs text-amber-700 font-semibold uppercase">False Positives (FP)</p>
                  <p className="text-2xl font-bold text-amber-900 mt-1">{metrics.confusion_matrix[0]?.[1] ?? 0}</p>
                  <p className="text-[11px] text-amber-600 mt-0.5">Legit flagged as fraud</p>
                </div>
                <div className="bg-rose-50 p-4 rounded-xl border border-rose-200 text-center">
                  <p className="text-xs text-rose-700 font-semibold uppercase">False Negatives (FN)</p>
                  <p className="text-2xl font-bold text-rose-900 mt-1">{metrics.confusion_matrix[1]?.[0] ?? 0}</p>
                  <p className="text-[11px] text-rose-600 mt-0.5">Fraud missed by model</p>
                </div>
                <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-200 text-center">
                  <p className="text-xs text-emerald-700 font-semibold uppercase">True Positives (TP)</p>
                  <p className="text-2xl font-bold text-emerald-900 mt-1">{metrics.confusion_matrix[1]?.[1] ?? 0}</p>
                  <p className="text-[11px] text-emerald-600 mt-0.5">Fraud correctly caught</p>
                </div>
              </div>
            </div>

            {/* Feature Importances */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-3">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <BarChart className="h-5 w-5 text-indigo-600" />
                Random Forest Feature Importance
              </h3>
              <p className="text-xs text-slate-500">
                Relative contribution of engineered features to fraud decision boundaries.
              </p>

              <div className="space-y-2 pt-2">
                {Object.entries(metrics.feature_importances || {})
                  .slice(0, 8)
                  .map(([feat, score]) => {
                    const pct = (score * 100).toFixed(1);
                    return (
                      <div key={feat} className="space-y-1">
                        <div className="flex justify-between text-xs font-semibold text-slate-700">
                          <span className="font-mono">{feat}</span>
                          <span>{pct}%</span>
                        </div>
                        <div className="w-full bg-slate-100 rounded-full h-2">
                          <div
                            className="bg-indigo-600 h-2 rounded-full transition-all"
                            style={{ width: `${Math.min(100, score * 250)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

          </div>
        </>
      ) : (
        <div className="p-8 text-center bg-slate-50 border border-slate-200 rounded-2xl text-slate-600">
          {error || 'No metrics found.'}
        </div>
      )}

    </div>
  );
};
