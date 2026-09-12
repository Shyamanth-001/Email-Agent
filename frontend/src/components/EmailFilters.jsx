import React from 'react';
import { Search, Filter, RotateCcw, SortAsc } from 'lucide-react';

export const EmailFilters = ({
  searchTerm,
  setSearchTerm,
  selectedCategory,
  setSelectedCategory,
  selectedPriority,
  setSelectedPriority,
  selectedSentiment,
  setSelectedSentiment,
  sortByDate,
  setSortByDate,
  categories = [],
  priorities = [],
  sentiments = [],
  onReset,
}) => {
  const hasActiveFilters =
    searchTerm ||
    selectedCategory !== 'ALL' ||
    selectedPriority !== 'ALL' ||
    selectedSentiment !== 'ALL' ||
    sortByDate !== 'desc';

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 mb-6 shadow-md backdrop-blur-sm">
      <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search by sender or subject..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
          />
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-xs font-semibold"
            >
              Clear
            </button>
          )}
        </div>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Category Filter */}
          <div className="relative min-w-[130px]">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full appearance-none bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-all pr-8 cursor-pointer"
            >
              <option value="ALL">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
            <Filter className="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          </div>

          {/* Priority Filter */}
          <div className="relative min-w-[120px]">
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="w-full appearance-none bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-all pr-8 cursor-pointer"
            >
              <option value="ALL">All Priorities</option>
              {priorities.map((pri) => (
                <option key={pri} value={pri}>
                  {pri}
                </option>
              ))}
            </select>
            <Filter className="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          </div>

          {/* Sentiment Filter */}
          <div className="relative min-w-[125px]">
            <select
              value={selectedSentiment}
              onChange={(e) => setSelectedSentiment(e.target.value)}
              className="w-full appearance-none bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 transition-all pr-8 cursor-pointer"
            >
              <option value="ALL">All Sentiments</option>
              {sentiments.map((sen) => (
                <option key={sen} value={sen}>
                  {sen}
                </option>
              ))}
            </select>
            <Filter className="w-3.5 h-3.5 absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          </div>

          {/* Date Sort Toggle */}
          <div className="relative">
            <button
              onClick={() => setSortByDate(sortByDate === 'desc' ? 'asc' : 'desc')}
              className="flex items-center gap-1.5 bg-slate-950/80 border border-slate-800 hover:border-slate-700 rounded-xl px-3 py-2.5 text-xs text-slate-300 font-medium transition-all"
              title="Toggle date sorting"
            >
              <SortAsc className={`w-3.5 h-3.5 ${sortByDate === 'asc' ? 'rotate-180' : ''} transition-transform`} />
              <span>{sortByDate === 'desc' ? 'Newest First' : 'Oldest First'}</span>
            </button>
          </div>

          {/* Reset Button */}
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl px-3 py-2.5 text-xs font-medium transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
