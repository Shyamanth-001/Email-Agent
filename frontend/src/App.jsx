import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { EmailDetails } from './components/EmailDetails';
import { Dashboard } from './pages/Dashboard';
import { Emails } from './pages/Emails';
import { Settings } from './pages/Settings';
import { AuthPage } from './pages/AuthPage';
import {
  fetchStats,
  fetchEmails,
  refreshAuthToken,
  fetchMe,
  logoutUser,
  onAuthError,
} from './services/api';
import { Loader2 } from 'lucide-react';

export function App() {
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

  const [stats, setStats] = useState(null);
  const [emails, setEmails] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);

  // Restore Auth Session on Mount
  useEffect(() => {
    let isMounted = true;

    const checkSession = async () => {
      // Only attempt a refresh if we previously had a session.
      // This prevents a 10-second timeout on every page load for
      // unauthenticated users when the backend may be unreachable.
      const hadSession = localStorage.getItem('hasSession') === 'true';
      if (!hadSession) {
        if (isMounted) setAuthChecking(false);
        return;
      }

      try {
        // Attempt token refresh via HttpOnly cookie
        const refreshData = await refreshAuthToken();
        if (isMounted && refreshData?.user) {
          setUser(refreshData.user);
          return;
        }
      } catch (err) {
        // Refresh cookie absent or invalid — session is gone
        localStorage.removeItem('hasSession');
        if (isMounted) setUser(null);
      } finally {
        if (isMounted) setAuthChecking(false);
      }
    };

    checkSession();

    // Subscribe to auth errors (token rotation failure)
    const unsubscribe = onAuthError(() => {
      localStorage.removeItem('hasSession');
      if (isMounted) setUser(null);
    });

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, []);

  const loadData = useCallback(async (isSilent = false) => {
    if (!user) return;
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
  }, [user]);

  useEffect(() => {
    if (user) {
      loadData(false);
      const interval = setInterval(() => {
        loadData(true);
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [user, loadData]);

  const handleLogout = async () => {
    await logoutUser();
    localStorage.removeItem('hasSession');
    setUser(null);
    setStats(null);
    setEmails([]);
  };

  // Initial Auth Check Spinner
  if (authChecking) {
    return (
      <div className="min-h-screen w-screen bg-slate-950 flex flex-col items-center justify-center text-slate-100 font-sans gap-3">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
        <p className="text-sm font-medium text-slate-400">Restoring session...</p>
      </div>
    );
  }

  // Render Login / Registration Page when Unauthenticated
  if (!user) {
    return <AuthPage onAuthSuccess={(userData) => setUser(userData)} />;
  }

  // Render Main Dashboard App when Authenticated
  return (
    <Router>
      <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
        {/* Sidebar */}
        <Sidebar emailCount={emails.length} user={user} onLogout={handleLogout} />

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
