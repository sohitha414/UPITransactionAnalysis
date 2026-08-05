import React from 'react';
import { ShieldAlert, BarChart3, Database, Cpu, Activity, Search } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  fraudRate?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, fraudRate }) => {
  const navItems = [
    { id: 'admin', label: 'React Admin Panel', icon: Search },
    { id: 'predictor', label: 'Fraud Score Simulator', icon: ShieldAlert },
    { id: 'dashboard', label: 'Streamlit Analytics', icon: BarChart3 },
    { id: 'model', label: 'ML Model Health', icon: Cpu },
    { id: 'eda', label: 'Data & Pipeline EDA', icon: Database },
  ];

  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Branding */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('admin')}>
            <div className="p-2 bg-gradient-to-tr from-indigo-600 to-emerald-500 rounded-xl shadow-md">
              <ShieldAlert className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
                UPI Transaction Analysis
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  ML Live Engine
                </span>
              </div>
              <p className="text-xs text-slate-400">End-to-End Fraud Detection & Risk Analytics</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/90 text-white shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Live Status Pill */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center space-x-2 bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700 text-xs text-slate-300">
              <Activity className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              <span>Pipeline: <strong className="text-emerald-400">Active</strong></span>
              {fraudRate !== undefined && (
                <span className="border-l border-slate-700 pl-2 text-slate-400">
                  Fraud: <strong className="text-rose-400">{fraudRate.toFixed(1)}%</strong>
                </span>
              )}
            </div>
          </div>

        </div>
      </div>

      {/* Mobile Sub-Nav */}
      <div className="md:hidden border-t border-slate-800 flex overflow-x-auto py-2 px-3 gap-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium whitespace-nowrap ${
                isActive ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-800'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
