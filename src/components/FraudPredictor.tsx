import React, { useState } from 'react';
import { ShieldAlert, Send, Sparkles, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { PredictionResult } from '../types';

export const FraudPredictor: React.FC = () => {
  const [amount, setAmount] = useState<number>(18500);
  const [sender, setSender] = useState<string>('user_0492@upi');
  const [receiver, setReceiver] = useState<string>('merchant_999@ybl');
  const [type, setType] = useState<string>('P2P');
  const [location, setLocation] = useState<string>('Mumbai');
  const [deviceId, setDeviceId] = useState<string>('DEV_FRAUD_8921');

  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [dbInserted, setDbInserted] = useState<boolean>(false);

  const handlePredictOnly = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    setDbInserted(false);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: Number(amount),
          sender,
          receiver,
          transaction_type: type,
          location,
          device_id: deviceId
        })
      });

      if (!res.ok) throw new Error('Prediction API call failed');
      const data = await res.json();
      setResult(data.prediction);
    } catch (err: any) {
      alert(err.message || 'Scoring failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitToDb = async () => {
    setLoading(true);
    setResult(null);
    setDbInserted(false);

    try {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: Number(amount),
          sender,
          receiver,
          transaction_type: type,
          location,
          device_id: deviceId
        })
      });

      if (!res.ok) throw new Error('Failed to insert transaction');
      const data = await res.json();
      
      setDbInserted(true);
      setResult({
        fraud_probability: data.fraud_probability,
        fraud_percentage: Math.round(data.fraud_probability * 1000) / 10,
        is_fraud: data.is_fraud,
        risk_level: data.risk_level,
        risk_reasons: data.risk_reasons,
        engineered_features: {}
      });
    } catch (err: any) {
      alert(err.message || 'Database transaction creation failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 bg-indigo-50 rounded-xl text-indigo-600">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">Live Fraud Scoring Simulator</h1>
            <p className="text-xs text-slate-500">
              Pass transaction payload to trained Random Forest machine learning pipeline for instant risk evaluation.
            </p>
          </div>
        </div>

        <form onSubmit={handlePredictOnly} className="mt-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Transaction Amount (INR ₹)
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold text-slate-900 focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Transaction Type
              </label>
              <select
                value={type}
                onChange={(e) => setType(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800"
              >
                <option value="P2P">P2P (Person to Person)</option>
                <option value="P2M">P2M (Person to Merchant)</option>
                <option value="BILL_PAYMENT">Bill Payment</option>
                <option value="ONLINE_SHOPPING">Online Shopping</option>
                <option value="RECHARGE">Mobile Recharge</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Sender VPA / Phone
              </label>
              <input
                type="text"
                required
                value={sender}
                onChange={(e) => setSender(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Receiver VPA / Merchant
              </label>
              <input
                type="text"
                required
                value={receiver}
                onChange={(e) => setReceiver(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium focus:ring-2 focus:ring-indigo-500/20"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Location
              </label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Device Identifier
              </label>
              <input
                type="text"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium font-mono"
              />
            </div>

          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 bg-indigo-600 text-white font-semibold text-sm rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              Simulate Risk Score
            </button>

            <button
              type="button"
              onClick={handleSubmitToDb}
              disabled={loading}
              className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 bg-slate-900 text-white font-semibold text-sm rounded-xl hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
              Score & Store to Database
            </button>
          </div>
        </form>
      </div>

      {/* Output Results Card */}
      {result && (
        <div className={`p-6 rounded-2xl border shadow-md space-y-4 animate-in fade-in ${
          result.is_fraud
            ? 'bg-rose-50 border-rose-200 text-rose-900'
            : 'bg-emerald-50 border-emerald-200 text-emerald-900'
        }`}>
          <div className="flex justify-between items-start">
            <div>
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                result.is_fraud ? 'bg-rose-600 text-white' : 'bg-emerald-600 text-white'
              }`}>
                {result.is_fraud ? <AlertCircle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
                {result.risk_level} RISK DETECTED
              </span>
              {dbInserted && (
                <span className="ml-2 text-xs font-semibold text-slate-600 bg-white/80 border border-slate-200 px-2.5 py-1 rounded-full">
                  Saved to PostgreSQL DB
                </span>
              )}
              <h2 className="text-2xl font-black mt-2">
                Fraud Probability: {result.fraud_percentage.toFixed(1)}%
              </h2>
            </div>
          </div>

          {/* Risk Factors */}
          {result.risk_reasons && result.risk_reasons.length > 0 && (
            <div className="bg-white/80 p-4 rounded-xl border border-rose-200/50 space-y-1.5">
              <p className="text-xs font-bold uppercase text-slate-700">Risk Explanation Factors:</p>
              <ul className="list-disc list-inside text-xs text-slate-700 space-y-1">
                {result.risk_reasons.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
