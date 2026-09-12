import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';

const CATEGORY_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#3b82f6'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 px-3 py-2 rounded-lg shadow-xl text-xs">
        <p className="font-semibold text-slate-200">{label}</p>
        <p className="text-indigo-400 font-bold mt-1">
          {payload[0].value} {payload[0].value === 1 ? 'Email' : 'Emails'}
        </p>
      </div>
    );
  }
  return null;
};

export const CategoryChart = ({ data = {} }) => {
  const chartData = Object.entries(data).map(([name, count]) => ({
    name: name || 'Uncategorized',
    count: Number(count) || 0,
  })).sort((a, b) => b.count - a.count);

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-sm">
        No category data available
      </div>
    );
  }

  return (
    <div className="h-64 w-full pt-4">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
          <XAxis
            dataKey="name"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
            interval={0}
            angle={-15}
            textAnchor="end"
          />
          <YAxis
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            axisLine={{ stroke: '#334155' }}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.05)' }} />
          <Bar dataKey="count" radius={[6, 6, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
