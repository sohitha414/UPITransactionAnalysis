import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { TransactionAdmin } from './components/TransactionAdmin';
import { FraudPredictor } from './components/FraudPredictor';
import { StreamlitView } from './components/StreamlitView';
import { ModelHealth } from './components/ModelHealth';
import { EdaInspector } from './components/EdaInspector';
import { AnalyticsSummary } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('admin');
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    fetch('/api/analytics/summary')
      .then(res => res.json())
      .then(data => setSummary(data))
      .catch(() => {});
  }, [activeTab]);

  return (
    <div className="min-h-screen bg-slate-100 font-sans text-slate-900 antialiased">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        fraudRate={summary?.fraud_rate_percentage}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'admin' && <TransactionAdmin />}
        {activeTab === 'predictor' && <FraudPredictor />}
        {activeTab === 'dashboard' && <StreamlitView />}
        {activeTab === 'model' && <ModelHealth />}
        {activeTab === 'eda' && <EdaInspector />}
      </main>
    </div>
  );
}
