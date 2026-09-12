import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

const PRIORITY_COLORS = {
  High: '#ef4444',
  Urgent: '#dc2626',
  Medium: '#f59e0b',
  Low: '#10b981',
};

const DEFAULT_COLORS = ['#ef4444', '#f59e0b', '#10b981', '#6366f1'];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900 border border-slate-700 px-3 py-2 rounded-lg shadow-xl text-xs">
        <p className="font-semibold text-slate-200">{payload[0].name}</p>
        <p className="text-slate-300 mt-0.5 font-bold">
          {payload[0].value} {payload[0].value === 1 ? 'Email' : 'Emails'}
        </p>
      </div>
    );
  }
  return null;
};

export const PriorityChart = ({ data = {} }) => {
  const chartData = Object.entries(data).map(([name, count]) => ({
    name: name || 'Unassigned',
    value: Number(count) || 0,
  })).filter(item => item.value > 0);

  if (chartData.length === 0) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-500 text-sm">
        No priority data available
      </div>
    );
  }

  return (
    <div className="h-64 w-full pt-2">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="45%"
            innerRadius={50}
            outerRadius={80}
            paddingAngle={4}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={PRIORITY_COLORS[entry.name] || DEFAULT_COLORS[index % DEFAULT_COLORS.length]}
                stroke="#0f172a"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => <span className="text-xs text-slate-300 font-medium">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
