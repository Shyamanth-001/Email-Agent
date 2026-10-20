import React, { useState, useEffect } from 'react';
import { Mail, AlertCircle, Loader2 } from 'lucide-react';
import { loginGoogleCode } from '../services/api';

export function AuthPage({ onAuthSuccess }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  // Load Google Identity Services script dynamically
  useEffect(() => {
    if (!googleClientId) return;
    if (!window.google?.accounts?.oauth2) {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);
    }
  }, [googleClientId]);

  // Handle Google OAuth authorization code (returns code + refresh token)
  const handleGoogleCodeResponse = async (response) => {
    if (!response || !response.code) return;
    setLoading(true);
    setError(null);
    try {
      const data = await loginGoogleCode(response.code);
      localStorage.setItem('hasSession', 'true');
      onAuthSuccess(data.user);
    } catch (err) {
      console.error('Google code auth error:', err);
      setError(
        err.response?.data?.detail || err.message || 'Google authentication failed'
      );
    } finally {
      setLoading(false);
    }
  };

  // Launch Google OAuth Code Popup for Identity + Gmail scope
  const handleConnectGoogleOAuth = () => {
    if (!googleClientId) {
      setError('Google Client ID is missing in VITE_GOOGLE_CLIENT_ID');
      return;
    }
    if (window.google?.accounts?.oauth2) {
      const client = window.google.accounts.oauth2.initCodeClient({
        client_id: googleClientId,
        scope: 'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
        ux_mode: 'popup',
        callback: handleGoogleCodeResponse,
      });
      client.requestCode();
    } else {
      setError('Google Identity Services script is loading. Please try again in a moment.');
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-950 px-4 py-12 text-slate-100 font-sans">
      <div className="w-full max-w-md space-y-8 bg-slate-900/90 border border-slate-800 p-8 rounded-2xl shadow-2xl backdrop-blur-xl text-center">
        {/* Header */}
        <div className="space-y-3">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
            <Mail className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            AI Email Classifier
          </h1>
          <p className="text-sm text-slate-400 leading-relaxed max-w-sm mx-auto">
            Sign in with your Google account to access your AI email dashboard and automate real-time inbox classification.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-start gap-3 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm text-left">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Google Authentication Action */}
        <div className="pt-2">
          <button
            type="button"
            disabled={loading}
            onClick={handleConnectGoogleOAuth}
            className="w-full py-3.5 px-5 bg-slate-800 hover:bg-slate-700 active:bg-slate-750 disabled:opacity-50 text-slate-100 font-semibold rounded-xl border border-slate-700 flex items-center justify-center gap-3 transition-all text-sm shadow-lg hover:shadow-indigo-500/10 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>Sign in with Google</span>
              </>
            )}
          </button>
        </div>

        {/* Footer info */}
        <p className="text-xs text-slate-500 pt-2">
          Secure OAuth 2.0 authentication powered by Google Identity.
        </p>
      </div>
    </div>
  );
}

export default AuthPage;
