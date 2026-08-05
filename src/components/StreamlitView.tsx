import React from 'react';
import { ExternalLink, BarChart2 } from 'lucide-react';

export const StreamlitView: React.FC = () => {
  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart2 className="h-6 w-6 text-indigo-600" />
            Interactive Streamlit Analytics Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Interactive Plotly charts, filters, and drill-downs running live on Streamlit service.
          </p>
        </div>

        <a
          href="/streamlit/"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-xl hover:bg-slate-800 transition-colors"
        >
          <span>Open Dashboard in New Tab</span>
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden h-[800px] relative">
        <iframe
          src="/streamlit/"
          title="Streamlit Analytics Dashboard"
          className="w-full h-full border-0"
        />
      </div>
    </div>
  );
};
