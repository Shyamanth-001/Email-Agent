import React, { useState } from 'react';
import { Settings as SettingsIcon, Server, Cpu, Database, Save, CheckCircle } from 'lucide-react';

export const Settings = () => {
  const [apiUrl, setApiUrl] = useState(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  );
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white m-0">Settings</h1>
        <p className="text-xs text-slate-400 mt-1">
          Manage API endpoint configuration and application parameters.
        </p>
      </div>

      {/* API Configuration Card */}
      <form onSubmit={handleSave} className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
            <Server className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 m-0">FastAPI Connection</h2>
            <p className="text-xs text-slate-400">Configure base URL for REST API communication</p>
          </div>
        </div>

        <div className="space-y-2">
          <label className="block text-xs font-semibold text-slate-300">
            API Base URL (<code className="text-indigo-300">VITE_API_BASE_URL</code>)
          </label>
          <input
            type="text"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2.5 text-xs font-mono text-slate-100 focus:outline-none focus:border-indigo-500 transition-all"
            placeholder="http://localhost:8000"
          />
          <p className="text-[11px] text-slate-500">
            Configured in <code className="text-slate-400">.env</code> or environment variables.
          </p>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
          >
            <Save className="w-4 h-4" />
            <span>Save Configuration</span>
          </button>

          {saved && (
            <span className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium animate-fade-in">
              <CheckCircle className="w-4 h-4" />
              Configuration saved
            </span>
          )}
        </div>
      </form>

      {/* System Architecture Metadata */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* LLM Engine Info */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-3">
          <div className="flex items-center gap-2.5 text-indigo-400 font-bold text-xs uppercase tracking-wider">
            <Cpu className="w-4 h-4" />
            <span>LLM Classifier</span>
          </div>
          <div className="space-y-1.5 text-xs text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-400">Provider:</span>
              <span className="font-semibold text-slate-200">Groq Cloud</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Model:</span>
              <span className="font-mono text-slate-200">llama3-8b-8192</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Structured Parser:</span>
              <span className="font-semibold text-slate-200">Pydantic v2</span>
            </div>
          </div>
        </div>

        {/* Database Info */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-3">
          <div className="flex items-center gap-2.5 text-purple-400 font-bold text-xs uppercase tracking-wider">
            <Database className="w-4 h-4" />
            <span>Persistence & Storage</span>
          </div>
          <div className="space-y-1.5 text-xs text-slate-300">
            <div className="flex justify-between">
              <span className="text-slate-400">Database:</span>
              <span className="font-semibold text-slate-200">PostgreSQL</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">ORM:</span>
              <span className="font-mono text-slate-200">SQLAlchemy 2.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Backend API:</span>
              <span className="font-semibold text-slate-200">FastAPI</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
