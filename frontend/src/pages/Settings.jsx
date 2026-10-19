import React, { useState } from 'react';
import { Settings as SettingsIcon, Server, Cpu, Database, Save, CheckCircle, RefreshCw, Mail } from 'lucide-react';
import { connectGmailToken } from '../services/api';

export const Settings = () => {
  const [apiUrl, setApiUrl] = useState(
    import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  );
  const [saved, setSaved] = useState(false);
  const [manualToken, setManualToken] = useState('');
  const [gmailStatus, setGmailStatus] = useState(null);
  const [gmailLoading, setGmailLoading] = useState(false);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleConnectGmailOAuth = () => {
    if (!googleClientId) {
      setGmailStatus({ error: 'VITE_GOOGLE_CLIENT_ID is not configured in .env' });
      return;
    }

    if (window.google?.accounts?.oauth2) {
      setGmailLoading(true);
      setGmailStatus(null);
      const client = window.google.accounts.oauth2.initCodeClient({
        client_id: googleClientId,
        scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email',
        ux_mode: 'popup',
        callback: async (response) => {
          if (response.code) {
            try {
              const res = await connectGmailToken(null, response.code);
              setGmailStatus({ success: `Gmail connected for ${res.email}! Watch status: ${res.watch?.status || 'Active'}` });
            } catch (err) {
              setGmailStatus({ error: err.response?.data?.detail || 'Failed to connect Gmail' });
            } finally {
              setGmailLoading(false);
            }
          } else {
            setGmailLoading(false);
          }
        },
      });
      client.requestCode();
    } else {
      setGmailStatus({ error: 'Google Identity Services script is loading. Try again in a moment.' });
    }
  };

  const handleManualTokenSubmit = async (e) => {
    e.preventDefault();
    if (!manualToken.trim()) return;
    setGmailLoading(true);
    setGmailStatus(null);
    try {
      const res = await connectGmailToken(manualToken.trim(), null);
      setGmailStatus({ success: `Gmail refresh token stored for ${res.email}!` });
      setManualToken('');
    } catch (err) {
      setGmailStatus({ error: err.response?.data?.detail || 'Failed to connect token' });
    } finally {
      setGmailLoading(false);
    }
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

      {/* Gmail Account Connection Card */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <div className="w-10 h-10 rounded-xl bg-purple-600/10 border border-purple-500/20 text-purple-400 flex items-center justify-center">
            <Mail className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-100 m-0">Gmail Integration & Watch Sync</h2>
            <p className="text-xs text-slate-400">Connect your Gmail OAuth refresh token for background AI classification</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <button
              type="button"
              disabled={gmailLoading}
              onClick={handleConnectGmailOAuth}
              className="px-4 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-lg shadow-purple-600/20 transition-all cursor-pointer flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${gmailLoading ? 'animate-spin' : ''}`} />
              <span>Connect Gmail via Google OAuth</span>
            </button>
            <p className="text-[11px] text-slate-500 mt-1.5">
              Launches Google consent popup to obtain <code className="text-slate-400">gmail_refresh_token</code> for <code className="text-slate-400">python main.py --watch</code>.
            </p>
          </div>

          <div className="pt-2 border-t border-slate-800/80">
            <form onSubmit={handleManualTokenSubmit} className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300">
                Or Paste Gmail Refresh Token Manually
              </label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={manualToken}
                  onChange={(e) => setManualToken(e.target.value)}
                  placeholder="1//04..."
                  className="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-4 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-purple-500"
                />
                <button
                  type="submit"
                  disabled={gmailLoading || !manualToken.trim()}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 rounded-xl text-xs font-medium cursor-pointer"
                >
                  Save Token
                </button>
              </div>
            </form>
          </div>

          {gmailStatus?.success && (
            <div className="text-xs text-emerald-400 flex items-center gap-1.5 font-medium">
              <CheckCircle className="w-4 h-4" />
              <span>{gmailStatus.success}</span>
            </div>
          )}
          {gmailStatus?.error && (
            <div className="text-xs text-rose-400 font-medium">
              {gmailStatus.error}
            </div>
          )}
        </div>
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
