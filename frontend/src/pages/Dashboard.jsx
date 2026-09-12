import React from 'react';
import { StatCard } from '../components/StatCard';
import { CategoryChart } from '../components/CategoryChart';
import { PriorityChart } from '../components/PriorityChart';
import { EmailTable } from '../components/EmailTable';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { Mail, AlertCircle, MessageSquare, Frown, ArrowRight, BarChart3, PieChart } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard = ({
  stats,
  emails,
  loading,
  error,
  onRetry,
  onSelectEmail,
  selectedEmailId,
}) => {
  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;

  // Calculate Negative / Frustrated Emails from loaded email list if available
  const negativeCount = emails.filter((e) => {
    const s = (e.sentiment || '').toLowerCase();
    return s.includes('negative') || s.includes('frustrated') || s.includes('angry');
  }).length;

  const highPriorityCount = stats?.by_priority?.High || stats?.by_priority?.high || 0;
  const recentEmails = emails.slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white m-0">Dashboard Overview</h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time automated email classification and sentiment insights.
          </p>
        </div>
        <Link
          to="/emails"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 rounded-xl text-xs font-semibold transition-all"
        >
          <span>View All Emails</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* SUMMARY CARDS (Top) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Emails"
          value={stats?.total_emails ?? emails.length}
          icon={Mail}
          accentColor="indigo"
          description="Processed by LLM"
        />
        <StatCard
          title="High Priority"
          value={highPriorityCount}
          icon={AlertCircle}
          accentColor="red"
          description="Requires immediate focus"
        />
        <StatCard
          title="Requires Response"
          value={stats?.requires_response ?? 0}
          icon={MessageSquare}
          accentColor="amber"
          description="Action pending from team"
        />
        <StatCard
          title="Negative / Frustrated"
          value={negativeCount}
          icon={Frown}
          accentColor="rose"
          description="Customer friction detected"
        />
      </div>

      {/* CHARTS (Middle) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-indigo-400" />
              <h2 className="text-sm font-bold text-slate-200 m-0">Emails by Category</h2>
            </div>
            <span className="text-[11px] text-slate-500 font-medium">Distribution</span>
          </div>
          <CategoryChart data={stats?.by_category || {}} />
        </div>

        {/* Priority Breakdown */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <PieChart className="w-4 h-4 text-purple-400" />
              <h2 className="text-sm font-bold text-slate-200 m-0">Emails by Priority</h2>
            </div>
            <span className="text-[11px] text-slate-500 font-medium">Urgency breakdown</span>
          </div>
          <PriorityChart data={stats?.by_priority || {}} />
        </div>
      </div>

      {/* RECENT EMAILS (Bottom) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <h2 className="text-sm font-bold text-slate-200 m-0">Recent Emails</h2>
          <Link to="/emails" className="text-xs text-indigo-400 hover:underline font-medium">
            See all ({emails.length}) →
          </Link>
        </div>
        <EmailTable
          emails={recentEmails}
          onSelectEmail={onSelectEmail}
          selectedEmailId={selectedEmailId}
          totalPages={1}
          totalCount={recentEmails.length}
        />
      </div>
    </div>
  );
};
