import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Mail, Settings, Sparkles, Inbox } from 'lucide-react';

export const Sidebar = ({ emailCount }) => {
  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Emails', path: '/emails', icon: Mail, badge: emailCount },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col h-screen sticky top-0 z-30 shrink-0">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800/80 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
          <Sparkles className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <h1 className="font-bold text-slate-100 text-base leading-snug tracking-tight">
            AI Email Classifier
          </h1>
          <p className="text-xs text-slate-400 font-medium">Smart Inbox Insights</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        <div className="px-3 mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Main Menu
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.name}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/80 border border-transparent'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </div>
              {item.badge !== undefined && item.badge !== null && item.badge > 0 && (
                <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Info */}
      <div className="p-4 m-4 rounded-xl bg-slate-900/60 border border-slate-800/80 text-xs text-slate-400 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></div>
          <span>API Connected</span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">v3.0.0</span>
      </div>
    </aside>
  );
};
