import React from 'react';
import { PriorityBadge, CategoryBadge, SentimentBadge, ResponseBadge } from './StatusBadge';
import { ChevronLeft, ChevronRight, Inbox, Calendar, User } from 'lucide-react';

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleString('en-US', {
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

export const EmailTable = ({
  emails = [],
  onSelectEmail,
  selectedEmailId,
  page = 1,
  totalPages = 1,
  onPageChange,
  totalCount = 0,
}) => {
  if (emails.length === 0) {
    return (
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-12 text-center shadow-lg">
        <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto mb-4">
          <Inbox className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-slate-200">No emails found</h3>
        <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
          No classified emails match your current search query or filter selection.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-xl backdrop-blur-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-950/60 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <th className="py-3.5 px-4">Sender</th>
              <th className="py-3.5 px-4">Subject</th>
              <th className="py-3.5 px-4">Category</th>
              <th className="py-3.5 px-4">Priority</th>
              <th className="py-3.5 px-4">Sentiment</th>
              <th className="py-3.5 px-4">Response</th>
              <th className="py-3.5 px-4 text-right">Received At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-sm">
            {emails.map((email) => {
              const isSelected = selectedEmailId === email.id;
              return (
                <tr
                  key={email.id}
                  onClick={() => onSelectEmail(email)}
                  className={`group cursor-pointer transition-all duration-150 ${
                    isSelected
                      ? 'bg-indigo-950/40 hover:bg-indigo-950/60'
                      : 'hover:bg-slate-800/50'
                  }`}
                >
                  {/* Sender */}
                  <td className="py-3.5 px-4 font-medium text-slate-200 max-w-[200px] truncate">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center text-xs font-bold shrink-0">
                        {(email.sender || 'U')[0].toUpperCase()}
                      </div>
                      <span className="truncate" title={email.sender}>
                        {email.sender}
                      </span>
                    </div>
                  </td>

                  {/* Subject */}
                  <td className="py-3.5 px-4 text-slate-300 max-w-[300px] truncate">
                    <div className="font-semibold text-slate-100 group-hover:text-indigo-400 transition-colors truncate">
                      {email.subject || '(No Subject)'}
                    </div>
                    {email.summary && (
                      <div className="text-xs text-slate-400 truncate max-w-[280px]">
                        {email.summary}
                      </div>
                    )}
                  </td>

                  {/* Category */}
                  <td className="py-3.5 px-4">
                    <CategoryBadge category={email.category} />
                  </td>

                  {/* Priority */}
                  <td className="py-3.5 px-4">
                    <PriorityBadge priority={email.priority} />
                  </td>

                  {/* Sentiment */}
                  <td className="py-3.5 px-4">
                    <SentimentBadge sentiment={email.sentiment} />
                  </td>

                  {/* Response */}
                  <td className="py-3.5 px-4">
                    <ResponseBadge requiresResponse={email.requires_response} />
                  </td>

                  {/* Received At */}
                  <td className="py-3.5 px-4 text-right text-xs text-slate-400 font-mono whitespace-nowrap">
                    {formatDate(email.received_at || email.classified_at)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <span className="font-semibold text-slate-200">{emails.length}</span> of{' '}
            <span className="font-semibold text-slate-200">{totalCount}</span> emails
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 font-medium">
              Page {page} of {totalPages}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="p-1.5 rounded-lg border border-slate-800 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
