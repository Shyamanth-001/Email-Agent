import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export const ErrorState = ({ message, onRetry }) => {
  return (
    <div className="bg-slate-900/90 border border-red-500/30 rounded-2xl p-8 text-center max-w-lg mx-auto my-12 shadow-2xl backdrop-blur-sm">
      <div className="w-14 h-14 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center mx-auto mb-4">
        <AlertTriangle className="w-7 h-7 animate-bounce" />
      </div>
      <h3 className="text-lg font-bold text-slate-100">Unable to Connect to API</h3>
      <p className="text-xs text-slate-400 mt-2 leading-relaxed">
        {message || 'Could not communicate with FastAPI server. Ensure FastAPI is running on http://localhost:8000.'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-6 inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-xl transition-all shadow-lg shadow-indigo-600/30 active:scale-95 cursor-pointer"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Retry Connection</span>
        </button>
      )}
    </div>
  );
};
