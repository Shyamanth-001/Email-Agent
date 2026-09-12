import React from 'react';

export const PriorityBadge = ({ priority }) => {
  const normalized = (priority || '').toLowerCase();
  
  const styles = {
    high: 'bg-red-500/10 text-red-400 border-red-500/20',
    urgent: 'bg-red-500/20 text-red-300 border-red-500/30 animate-pulse',
    medium: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  };

  const style = styles[normalized] || 'bg-slate-800 text-slate-300 border-slate-700';

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style}`}>
      {priority || 'Unknown'}
    </span>
  );
};

export const CategoryBadge = ({ category }) => {
  const colors = [
    'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    'bg-purple-500/10 text-purple-400 border-purple-500/20',
    'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    'bg-sky-500/10 text-sky-400 border-sky-500/20',
    'bg-pink-500/10 text-pink-400 border-pink-500/20',
  ];

  // Hash category name to consistently pick a color
  let hash = 0;
  const str = category || 'General';
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const colorIndex = Math.abs(hash) % colors.length;
  const style = colors[colorIndex];

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium border ${style}`}>
      {category || 'General'}
    </span>
  );
};

export const SentimentBadge = ({ sentiment }) => {
  const normalized = (sentiment || '').toLowerCase();

  let style = 'bg-slate-800 text-slate-300 border-slate-700';
  let emoji = '😐';

  if (normalized.includes('positive')) {
    style = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    emoji = '😊';
  } else if (normalized.includes('negative') || normalized.includes('frustrated') || normalized.includes('angry')) {
    style = 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    emoji = '😟';
  } else if (normalized.includes('neutral')) {
    style = 'bg-slate-500/10 text-slate-300 border-slate-600/30';
    emoji = '😐';
  }

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${style}`}>
      <span>{emoji}</span>
      <span className="capitalize">{sentiment || 'Neutral'}</span>
    </span>
  );
};

export const ResponseBadge = ({ requiresResponse }) => {
  if (requiresResponse) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span>
        Action Required
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-800/80 text-slate-400 border border-slate-700/50">
      No Action
    </span>
  );
};
