import React, { useState, useMemo } from 'react';
import { EmailFilters } from '../components/EmailFilters';
import { EmailTable } from '../components/EmailTable';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { Mail, RefreshCw } from 'lucide-react';

export const Emails = ({
  emails = [],
  loading,
  error,
  onRetry,
  onSelectEmail,
  selectedEmailId,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedPriority, setSelectedPriority] = useState('ALL');
  const [selectedSentiment, setSelectedSentiment] = useState('ALL');
  const [sortByDate, setSortByDate] = useState('desc');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Extract unique categories, priorities, sentiments
  const categories = useMemo(() => {
    const set = new Set(emails.map((e) => e.category).filter(Boolean));
    return Array.from(set).sort();
  }, [emails]);

  const priorities = useMemo(() => {
    const set = new Set(emails.map((e) => e.priority).filter(Boolean));
    return Array.from(set).sort();
  }, [emails]);

  const sentiments = useMemo(() => {
    const set = new Set(emails.map((e) => e.sentiment).filter(Boolean));
    return Array.from(set).sort();
  }, [emails]);

  // Filter & sort emails
  const filteredEmails = useMemo(() => {
    return emails
      .filter((email) => {
        // Search term filter (sender or subject)
        if (searchTerm) {
          const query = searchTerm.toLowerCase();
          const senderMatch = (email.sender || '').toLowerCase().includes(query);
          const subjectMatch = (email.subject || '').toLowerCase().includes(query);
          const bodyMatch = (email.body || '').toLowerCase().includes(query);
          if (!senderMatch && !subjectMatch && !bodyMatch) return false;
        }

        // Category filter
        if (selectedCategory !== 'ALL' && email.category !== selectedCategory) {
          return false;
        }

        // Priority filter
        if (selectedPriority !== 'ALL' && email.priority !== selectedPriority) {
          return false;
        }

        // Sentiment filter
        if (selectedSentiment !== 'ALL' && email.sentiment !== selectedSentiment) {
          return false;
        }

        return true;
      })
      .sort((a, b) => {
        const dateA = new Date(a.received_at || a.classified_at || 0).getTime();
        const dateB = new Date(b.received_at || b.classified_at || 0).getTime();
        return sortByDate === 'desc' ? dateB - dateA : dateA - dateB;
      });
  }, [emails, searchTerm, selectedCategory, selectedPriority, selectedSentiment, sortByDate]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredEmails.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const paginatedEmails = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredEmails.slice(start, start + pageSize);
  }, [filteredEmails, currentPage, pageSize]);

  const handleReset = () => {
    setSearchTerm('');
    setSelectedCategory('ALL');
    setSelectedPriority('ALL');
    setSelectedSentiment('ALL');
    setSortByDate('desc');
    setPage(1);
  };

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} onRetry={onRetry} />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white m-0">All Classified Emails</h1>
          <p className="text-xs text-slate-400 mt-1">
            Search, filter, and inspect AI summaries for all incoming messages.
          </p>
        </div>
        <button
          onClick={onRetry}
          className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl text-xs font-semibold transition-all cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Component */}
      <EmailFilters
        searchTerm={searchTerm}
        setSearchTerm={(val) => {
          setSearchTerm(val);
          setPage(1);
        }}
        selectedCategory={selectedCategory}
        setSelectedCategory={(val) => {
          setSelectedCategory(val);
          setPage(1);
        }}
        selectedPriority={selectedPriority}
        setSelectedPriority={(val) => {
          setSelectedPriority(val);
          setPage(1);
        }}
        selectedSentiment={selectedSentiment}
        setSelectedSentiment={(val) => {
          setSelectedSentiment(val);
          setPage(1);
        }}
        sortByDate={sortByDate}
        setSortByDate={setSortByDate}
        categories={categories}
        priorities={priorities}
        sentiments={sentiments}
        onReset={handleReset}
      />

      {/* Email Table */}
      <EmailTable
        emails={paginatedEmails}
        onSelectEmail={onSelectEmail}
        selectedEmailId={selectedEmailId}
        page={currentPage}
        totalPages={totalPages}
        onPageChange={(p) => setPage(p)}
        totalCount={filteredEmails.length}
      />
    </div>
  );
};
