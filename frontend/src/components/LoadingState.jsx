import React from 'react';

export const LoadingState = () => {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Stat Cards Skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 bg-slate-900/80 border border-slate-800 rounded-2xl p-5" />
        ))}
      </div>

      {/* Charts Skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="h-80 bg-slate-900/80 border border-slate-800 rounded-2xl p-6" />
        <div className="h-80 bg-slate-900/80 border border-slate-800 rounded-2xl p-6" />
      </div>

      {/* Table Skeleton */}
      <div className="h-96 bg-slate-900/80 border border-slate-800 rounded-2xl p-6" />
    </div>
  );
};
