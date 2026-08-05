import React, { useState, useEffect } from 'react';
import { Transaction, PaginatedTransactionsResponse } from '../types';
import { Search, Filter, RefreshCw, CheckCircle2, AlertTriangle, Clock, ArrowUpDown, ChevronLeft, ChevronRight, Eye, ShieldCheck } from 'lucide-react';

export const TransactionAdmin: React.FC = () => {
  const [data, setData] = useState<PaginatedTransactionsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination
  const [page, setPage] = useState<number>(1);
  const [limit] = useState<number>(15);
  const [search, setSearch] = useState<string>('');
  const [isFraudFilter, setIsFraudFilter] = useState<string>('all');
  const [reviewFilter, setReviewFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('timestamp');
  const [sortDir, setSortDir] = useState<string>('desc');

  // Review Modal State
  const [selectedTxn, setSelectedTxn] = useState<Transaction | null>(null);
  const [reviewStatus, setReviewStatus] = useState<string>('verified_legit');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [submittingReview, setSubmittingReview] = useState<boolean>(false);

  const fetchTransactions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        sort_by: sortBy,
        sort_dir: sortDir
      });

      if (search.trim()) params.append('search', search.trim());
      if (isFraudFilter !== 'all') params.append('is_fraud', isFraudFilter);
      if (reviewFilter !== 'all') params.append('review_status', reviewFilter);

      const res = await fetch(`/api/transactions?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch transactions`);
      const result: PaginatedTransactionsResponse = await res.json();
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [page, isFraudFilter, reviewFilter, sortBy, sortDir]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTransactions();
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTxn) return;

    setSubmittingReview(true);
    try {
      const res = await fetch(`/api/transactions/${selectedTxn.transaction_id}/review`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          review_status: reviewStatus,
          review_notes: reviewNotes
        })
      });

      if (!res.ok) throw new Error('Failed to update review status');
      
      // Close modal and refresh list
      setSelectedTxn(null);
      fetchTransactions();
    } catch (err: any) {
      alert(err.message || 'Review update failed');
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-indigo-600" />
            UPI Transaction Management Panel
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Browse, search, filter, and manually review scored UPI transactions stored in PostgreSQL database.
          </p>
        </div>

        <button
          onClick={() => fetchTransactions()}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-xl hover:bg-slate-800 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Live DB
        </button>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row gap-3">
          
          {/* Search Input */}
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Txn ID, Sender VPA, Receiver, Location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500"
            />
          </div>

          {/* Risk Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400 hidden sm:block" />
            <select
              value={isFraudFilter}
              onChange={(e) => { setIsFraudFilter(e.target.value); setPage(1); }}
              className="bg-slate-50 border border-slate-200 rounded-xl text-sm px-3 py-2 text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
            >
              <option value="all">All Risk Levels</option>
              <option value="1">🚨 Flagged Fraud (Prob ≥ 50%)</option>
              <option value="0">✅ Legit Transactions</option>
            </select>
          </div>

          {/* Review Filter */}
          <select
            value={reviewFilter}
            onChange={(e) => { setReviewFilter(e.target.value); setPage(1); }}
            className="bg-slate-50 border border-slate-200 rounded-xl text-sm px-3 py-2 text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="all">All Review Statuses</option>
            <option value="pending">⏳ Pending Review</option>
            <option value="verified_legit">✅ Verified Legit</option>
            <option value="confirmed_fraud">❌ Confirmed Fraud</option>
          </select>

          {/* Sort By */}
          <select
            value={`${sortBy}_${sortDir}`}
            onChange={(e) => {
              const [sb, sd] = e.target.value.split('_');
              setSortBy(sb);
              setSortDir(sd);
            }}
            className="bg-slate-50 border border-slate-200 rounded-xl text-sm px-3 py-2 text-slate-700 font-medium focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          >
            <option value="timestamp_desc">Newest First</option>
            <option value="timestamp_asc">Oldest First</option>
            <option value="fraud_probability_desc">Highest Fraud Prob</option>
            <option value="amount_desc">Highest Amount</option>
          </select>

          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
          >
            Search
          </button>
        </form>
      </div>

      {/* Transactions Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-20 text-center">
            <RefreshCw className="h-8 w-8 text-indigo-600 animate-spin mx-auto mb-2" />
            <p className="text-sm text-slate-500 font-medium">Fetching transactions from PostgreSQL database...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center bg-rose-50 border border-rose-200 rounded-2xl m-4 text-rose-700">
            <AlertTriangle className="h-8 w-8 mx-auto mb-2 text-rose-600" />
            <p className="font-semibold">Error Loading Data</p>
            <p className="text-xs mt-1 text-rose-600">{error}</p>
          </div>
        ) : data && data.data.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <th className="px-4 py-3.5">Transaction ID</th>
                  <th className="px-4 py-3.5">Timestamp</th>
                  <th className="px-4 py-3.5">Amount (INR)</th>
                  <th className="px-4 py-3.5">Sender / Receiver VPA</th>
                  <th className="px-4 py-3.5">Type & Location</th>
                  <th className="px-4 py-3.5">Fraud Score</th>
                  <th className="px-4 py-3.5">Review Status</th>
                  <th className="px-4 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.data.map((txn) => {
                  const isHighRisk = txn.fraud_probability >= 0.50;
                  const probPct = (txn.fraud_probability * 100).toFixed(1);

                  return (
                    <tr key={txn.transaction_id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-800">
                        {txn.transaction_id}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
                        {new Date(txn.timestamp).toLocaleString('en-IN', {
                          day: '2-digit', month: 'short', year: 'numeric',
                          hour: '2-digit', minute: '2-digit'
                        })}
                      </td>
                      <td className="px-4 py-3 font-bold text-slate-900">
                        ₹{txn.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        <div className="font-medium text-slate-800">{txn.sender}</div>
                        <div className="text-slate-400 text-[11px]">→ {txn.receiver}</div>
                      </td>
                      <td className="px-4 py-3 text-xs">
                        <span className="inline-block px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[11px] mr-1.5">
                          {txn.transaction_type}
                        </span>
                        <span className="text-slate-500">{txn.location}</span>
                      </td>
                      <td className="px-4 py-3 text-xs">
                        <div className="flex items-center gap-2">
                          <span className={`px-2.5 py-1 rounded-full font-bold text-xs ${
                            isHighRisk
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}>
                            {probPct}% {isHighRisk ? 'HIGH RISK' : 'LOW'}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {txn.review_status === 'pending' && (
                          <span className="inline-flex items-center gap-1 text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full font-medium text-[11px]">
                            <Clock className="h-3 w-3" /> Pending
                          </span>
                        )}
                        {txn.review_status === 'verified_legit' && (
                          <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full font-medium text-[11px]">
                            <CheckCircle2 className="h-3 w-3" /> Verified Legit
                          </span>
                        )}
                        {txn.review_status === 'confirmed_fraud' && (
                          <span className="inline-flex items-center gap-1 text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-0.5 rounded-full font-medium text-[11px]">
                            <AlertTriangle className="h-3 w-3" /> Confirmed Fraud
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => {
                            setSelectedTxn(txn);
                            setReviewStatus(txn.review_status);
                            setReviewNotes(txn.review_notes || '');
                          }}
                          className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs rounded-lg transition-colors"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Review
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center text-slate-500 text-sm">
            No transactions found matching criteria.
          </div>
        )}

        {/* Pagination Footer */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between px-5 py-3.5 bg-slate-50 border-t border-slate-200 text-xs text-slate-600">
            <div>
              Showing Page <strong>{data.page}</strong> of <strong>{data.total_pages}</strong> ({data.total_records} total transactions)
            </div>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="font-semibold px-2">{page}</span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage(page + 1)}
                className="p-1.5 rounded-lg border border-slate-300 bg-white hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Manual Review Modal Drawer */}
      {selectedTxn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 animate-in fade-in zoom-in-95">
            <div className="flex justify-between items-start border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Manual Transaction Review</h3>
                <p className="text-xs text-slate-500 font-mono mt-0.5">{selectedTxn.transaction_id}</p>
              </div>
              <button
                onClick={() => setSelectedTxn(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-50 p-3.5 rounded-xl text-xs space-y-1.5 border border-slate-200">
              <div className="flex justify-between">
                <span className="text-slate-500">Amount:</span>
                <span className="font-bold text-slate-900">₹{selectedTxn.amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Sender VPA:</span>
                <span className="font-medium text-slate-800">{selectedTxn.sender}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Receiver VPA:</span>
                <span className="font-medium text-slate-800">{selectedTxn.receiver}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">ML Fraud Probability:</span>
                <span className={`font-bold ${selectedTxn.fraud_probability >= 0.5 ? 'text-rose-600' : 'text-emerald-600'}`}>
                  {(selectedTxn.fraud_probability * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            <form onSubmit={handleReviewSubmit} className="space-y-4 pt-1">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Update Review Action
                </label>
                <select
                  value={reviewStatus}
                  onChange={(e) => setReviewStatus(e.target.value)}
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm font-medium focus:ring-2 focus:ring-indigo-500/20"
                >
                  <option value="pending">⏳ Leave as Pending</option>
                  <option value="verified_legit">✅ Mark as Verified Legit</option>
                  <option value="confirmed_fraud">❌ Confirm as Fraudulent</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Analyst Review Notes
                </label>
                <textarea
                  rows={3}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="e.g. Verified customer via bank call; device ID confirmed."
                  className="w-full p-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-indigo-500/20"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedTxn(null)}
                  className="px-4 py-2 border border-slate-300 rounded-xl text-xs font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className="px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-semibold hover:bg-indigo-700 disabled:opacity-50"
                >
                  {submittingReview ? 'Saving...' : 'Save Review Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
