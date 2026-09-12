import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { EmailDetails } from './components/EmailDetails';
import { Dashboard } from './pages/Dashboard';
import { Emails } from './pages/Emails';
import { Settings } from './pages/Settings';
import { fetchStats, fetchEmails } from './services/api';

export function App() {
  const [stats, setStats] = useState(null);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    setError(null);
    try {
      const [statsRes, emailsRes] = await Promise.all([
        fetchStats(),
        fetchEmails(100, 0),
      ]);
      setStats(statsRes);
      setEmails(emailsRes || []);
    } catch (err) {
      console.error('Failed to load email classifier data:', err);
      if (!isSilent) {
        setError(
          err.response?.data?.detail ||
            err.message ||
            'Failed to connect to FastAPI server. Please check backend status.'
        );
      }
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(false);
    // Background polling every 30 seconds to fetch new emails automatically
    const interval = setInterval(() => {
      loadData(true);
    }, 30000);
    return () => clearInterval(interval);
  }, [loadData]);


  return (
    <Router>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
        {/* Sidebar */}
        <Sidebar emailCount={emails.length} />

        {/* Main Content Area */}
        <main className="flex-1 h-screen overflow-y-auto bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 p-6 md:p-8">
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route
                path="/"
                element={
                  <Dashboard
                    stats={stats}
                    emails={emails}
                    loading={loading}
                    error={error}
                    onRetry={loadData}
                    onSelectEmail={(email) => setSelectedEmail(email)}
                    selectedEmailId={selectedEmail?.id}
                  />
                }
              />
              <Route
                path="/emails"
                element={
                  <Emails
                    emails={emails}
                    loading={loading}
                    error={error}
                    onRetry={loadData}
                    onSelectEmail={(email) => setSelectedEmail(email)}
                    selectedEmailId={selectedEmail?.id}
                  />
                }
              />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </div>
        </main>

        {/* Slide-Over Email Details Drawer */}
        {selectedEmail && (
          <EmailDetails
            email={selectedEmail}
            onClose={() => setSelectedEmail(null)}
          />
        )}
      </div>
    </Router>
  );
}

export default App;
