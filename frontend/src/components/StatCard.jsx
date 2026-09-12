import React from 'react';

export const StatCard = ({ title, value, icon: Icon, description, accentColor = 'indigo' }) => {
  const colorMap = {
    indigo: 'from-indigo-500/20 to-indigo-600/5 text-indigo-400 border-indigo-500/30 icon-bg:bg-indigo-500/20',
    red: 'from-red-500/20 to-red-600/5 text-red-400 border-red-500/30 icon-bg:bg-red-500/20',
    amber: 'from-amber-500/20 to-amber-600/5 text-amber-400 border-amber-500/30 icon-bg:bg-amber-500/20',
    rose: 'from-rose-500/20 to-rose-600/5 text-rose-400 border-rose-500/30 icon-bg:bg-rose-500/20',
    emerald: 'from-emerald-500/20 to-emerald-600/5 text-emerald-400 border-emerald-500/30 icon-bg:bg-emerald-500/20',
  };

  const selectedColor = colorMap[accentColor] || colorMap.indigo;

  return (
    <div className="relative overflow-hidden rounded-2xl bg-slate-900/90 border border-slate-800 p-5 shadow-lg backdrop-blur-sm transition-all duration-200 hover:border-slate-700 hover:shadow-indigo-500/5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-400">{title}</span>
        {Icon && (
          <div className={`p-2.5 rounded-xl border ${selectedColor}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold tracking-tight text-white">
          {value !== undefined && value !== null ? value.toLocaleString() : '-'}
        </span>
      </div>
      {description && (
        <p className="mt-2 text-xs text-slate-400 flex items-center gap-1">
          {description}
        </p>
      )}
    </div>
  );
};
