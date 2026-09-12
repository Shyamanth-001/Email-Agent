import React from 'react';
import { PriorityBadge, CategoryBadge, SentimentBadge, ResponseBadge } from './StatusBadge';
import { X, Sparkles, User, Calendar, Mail, FileText, CheckCircle2 } from 'lucide-react';

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
};

export const EmailDetails = ({ email, onClose }) => {
  if (!email) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-xs flex justify-end">
      {/* Backdrop click to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Slide-over Panel */}
      <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full shadow-2xl flex flex-col overflow-hidden transform transition-all duration-300">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Mail className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-100 line-clamp-1">
                {email.subject || '(No Subject)'}
              </h2>
              <p className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
                <span>Message ID: #{email.id}</span>
                {email.gmail_message_id && (
                  <span className="text-[11px] text-slate-500 font-mono truncate max-w-[200px]">
                    ({email.gmail_message_id})
                  </span>
                )}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-all"
            title="Close details"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* AI CLASSIFICATION SECTION (Visually Distinct) */}
          <div className="relative overflow-hidden rounded-2xl bg-gradient-to-b from-indigo-950/50 via-slate-900 to-slate-900 border border-indigo-500/30 p-5 shadow-lg shadow-indigo-950/30">
            {/* Sparkle background glow */}
            <div className="absolute top-0 right-0 p-8 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-indigo-600 text-white flex items-center justify-center">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                  AI Classification Analysis
                </span>
              </div>
              <ResponseBadge requiresResponse={email.requires_response} />
            </div>

            {/* Badges Grid */}
            <div className="grid grid-cols-3 gap-3 mb-4 bg-slate-950/60 p-3 rounded-xl border border-slate-800">
              <div>
                <div className="text-[11px] font-semibold text-slate-400 mb-1">Category</div>
                <CategoryBadge category={email.category} />
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-400 mb-1">Priority</div>
                <PriorityBadge priority={email.priority} />
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-400 mb-1">Sentiment</div>
                <SentimentBadge sentiment={email.sentiment} />
              </div>
            </div>

            {/* AI Summary */}
            <div className="bg-slate-950/70 p-4 rounded-xl border border-indigo-500/20">
              <div className="text-xs font-bold text-indigo-400 mb-1.5 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5" />
                <span>Executive Summary</span>
              </div>
              <p className="text-xs leading-relaxed text-slate-200">
                {email.summary || 'No summary available for this email.'}
              </p>
            </div>
          </div>

          {/* ORIGINAL EMAIL METADATA & BODY */}
          <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
              Original Message Details
            </h3>

            {/* Sender & Received Info */}
            <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400">
                  <User className="w-4 h-4 text-slate-500" />
                  <span className="font-semibold text-slate-300">From:</span>
                </div>
                <span className="font-mono text-slate-200 font-medium">{email.sender}</span>
              </div>
              <div className="flex items-center justify-between border-t border-slate-800/60 pt-2">
                <div className="flex items-center gap-2 text-slate-400">
                  <Calendar className="w-4 h-4 text-slate-500" />
                  <span className="font-semibold text-slate-300">Received Date:</span>
                </div>
                <span className="text-slate-300">
                  {formatDate(email.received_at || email.classified_at)}
                </span>
              </div>
            </div>

            {/* Email Subject & Body */}
            <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800 space-y-3">
              <div className="font-semibold text-slate-200 text-sm border-b border-slate-800/80 pb-2">
                {email.subject || '(No Subject)'}
              </div>
              <div className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-wrap max-h-96 overflow-y-auto pr-2">
                {email.body || '(Empty email body)'}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2 text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
            <span>Classified on {formatDate(email.classified_at)}</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl font-medium transition-all"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
