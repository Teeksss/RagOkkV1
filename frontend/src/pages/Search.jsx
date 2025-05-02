import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { search } from '../api/search';
import { getDocuments } from '../api/documents';
import LoadingSpinner from '../components/common/LoadingSpinner';
import MarkdownRenderer from '../components/common/MarkdownRenderer';

const Search = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    documentIds: [],
    dateRange: {
      from: '',
      to: ''
    }
  });
  const [availableDocuments, setAvailableDocuments] = useState([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    totalResults: 0,
    limit: 10
  });

  // Extract query parameters on mount and when location changes
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const urlQuery = searchParams.get('q') || '';
    const page = parseInt(searchParams.get('page')) || 1;
    const docIds = searchParams.getAll('doc') || [];
    const fromDate = searchParams.get('from') || '';
    const toDate = searchParams.get('to') || '';
    
    setQuery(urlQuery);
    setPagination(prev => ({ ...prev, page }));
    setFilters({
      documentIds: docIds,
      dateRange: {
        from: fromDate,
        to: toDate
      }
    });
    
    // Execute search if query exists
    if (urlQuery) {
      executeSearch(urlQuery, docIds, fromDate, toDate, page);
    }
  }, [location.search]);

  // Load available documents for filtering
  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setDocumentsLoading(true);
        
        const result = await getDocuments({
          limit: 100, // Get a larger set of documents for filtering
          sort: 'filename',
          order: 'asc'
        });
        
        setAvailableDocuments(result.items || []);
      } catch (err) {
        console.error('Error loading documents for filtering:', err);
      } finally {
        setDocumentsLoading(false);
      }
    };
    
    fetchDocuments();
  }, []);

  // Execute search function
  const executeSearch = async (searchQuery, docIds = [], fromDate = '', toDate = '', page = 1) => {
    if (!searchQuery) return;
    
    try {
      setLoading(true);
      setError(null);
      
      // Prepare search parameters
      const searchParams = {
        query: searchQuery,
        page,
        limit: pagination.limit
      };
      
      // Add document filter if selected
      if (docIds && docIds.length > 0) {
        searchParams.document_ids = docIds;
      }
      
      // Add date filters if selected
      if (fromDate) {
        searchParams.from_date = fromDate;
      }
      
      if (toDate) {
        searchParams.to_date = toDate;
      }
      
      const result = await search(searchParams);
      
      setResults(result.items || []);
      setPagination({
        page: result.page,
        totalPages: result.total_pages,
        totalResults: result.total_items,
        limit: result.limit
      });
    } catch (err) {
      console.error('Search error:', err);
      setError(err.message || 'Failed to execute search. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle search form submission
  const handleSearch = (e) => {
    e.preventDefault();
    
    if (!query.trim()) return;
    
    // Update URL with search params
    const searchParams = new URLSearchParams();
    searchParams.set('q', query);
    searchParams.set('page', '1'); // Reset to first page on new search
    
    // Add document filters
    filters.documentIds.forEach(docId => {
      searchParams.append('doc', docId);
    });
    
    // Add date filters
    if (filters.dateRange.from) {
      searchParams.set('from', filters.dateRange.from);
    }
    
    if (filters.dateRange.to) {
      searchParams.set('to', filters.dateRange.to);
    }
    
    navigate(`${location.pathname}?${searchParams.toString()}`);
  };

  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage < 1 || newPage > pagination.totalPages) return;
    
    const searchParams = new URLSearchParams(location.search);
    searchParams.set('page', newPage.toString());
    
    navigate(`${location.pathname}?${searchParams.toString()}`);
  };

  // Handle document filter change
  const handleDocumentFilterChange = (docId) => {
    setFilters(prev => {
      const newDocIds = prev.documentIds.includes(docId)
        ? prev.documentIds.filter(id => id !== docId)
        : [...prev.documentIds, docId];
      
      return {
        ...prev,
        documentIds: newDocIds
      };
    });
  };

  // Handle date filter change
  const handleDateFilterChange = (e) => {
    const { name, value } = e.target;
    
    setFilters(prev => ({
      ...prev,
      dateRange: {
        ...prev.dateRange,
        [name]: value
      }
    }));
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({
      documentIds: [],
      dateRange: {
        from: '',
        to: ''
      }
    });
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date);
  };

  // Highlight search terms in text
  const highlightText = (text, searchTerm) => {
    if (!text || !searchTerm) return text;
    
    const parts = text.split(new RegExp(`(${searchTerm})`, 'gi'));
    
    return parts.map((part, index) => 
      part.toLowerCase() === searchTerm.toLowerCase() 
        ? <mark key={index} className="bg-yellow-200 not-italic">{part}</mark> 
        : part
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Advanced Search</h1>
          <p className="mt-1 text-sm text-gray-500">
            Search across all your documents
          </p>
        </div>
      </div>

      {/* Search form */}
      <div className="bg-white shadow sm:rounded-md mb-8">
        <div className="px-4 py-5 sm:p-6">
          <form onSubmit={handleSearch}>
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <label htmlFor="search-input" className="sr-only">Search</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <input
                    id="search-input"
                    type="text"
                    className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 pr-3 py-2 border-gray-300 rounded-md"
                    placeholder="Search documents, content, etc."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
              </div>
              <div className="flex-shrink-0">
                <button
                  type="submit"
                  disabled={!query.trim() || loading}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <LoadingSpinner size="small" color="white" className="mr-2" />
                      Searching...
                    </>
                  ) : 'Search'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowFilters(!showFilters)}
                  className="ml-2 inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clipRule="evenodd" />
                  </svg>
                  Filters
                </button>
              </div>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="mt-4 bg-gray-50 p-4 rounded-md">
                <div className="mb-2 flex justify-between items-center">
                  <h3 className="text-sm font-medium text-gray-900">Search Filters</h3>
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="text-xs text-blue-600 hover:text-blue-500"
                  >
                    Clear all filters
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Document filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Filter by Documents
                    </label>
                    <div className="max-h-40 overflow-y-auto border border-gray-200 rounded-md p-2">
                      {documentsLoading ? (
                        <div className="flex justify-center items-center py-4">
                          <LoadingSpinner size="small" />
                        </div>
                      ) : availableDocuments.length === 0 ? (
                        <p className="text-sm text-gray-500">No documents available</p>
                      ) : (
                        availableDocuments.map((doc) => (
                          <div key={doc.id} className="flex items-center mb-1">
                            <input
                              id={`doc-${doc.id}`}
                              name={`doc-${doc.id}`}
                              type="checkbox"
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                              checked={filters.documentIds.includes(doc.id)}
                              onChange={() => handleDocumentFilterChange(doc.id)}
                            />
                            <label htmlFor={`doc-${doc.id}`} className="ml-2 block text-sm text-gray-700 truncate">
                              {doc.filename}
                            </label>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Date range filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Filter by Date
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label htmlFor="from" className="block text-xs text-gray-500">
                          From
                        </label>
                        <input
                          type="date"
                          id="from"
                          name="from"
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          value={filters.dateRange.from}
                          onChange={handleDateFilterChange}
                        />
                      </div>
                      <div>
                        <label htmlFor="to" className="block text-xs text-gray-500">
                          To
                        </label>
                        <input
                          type="date"
                          id="to"
                          name="to"
                          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                          value={filters.dateRange.to}
                          onChange={handleDateFilterChange}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </form>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Search results */}
      {query && !loading && (
        <div className="mb-4">
          <h2 className="text-lg font-medium text-gray-900">
            {pagination.totalResults} {pagination.totalResults === 1 ? 'result' : 'results'} for "{query}"
          </h2>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <LoadingSpinner size="large" />
        </div>
      ) : results.length === 0 && query ? (
        <div className="bg-white shadow sm:rounded-md">
          <div className="px-4 py-5 sm:p-6 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h14a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">No results found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search query or filters.
            </p>
          </div>
        </div>
      ) : results.length > 0 ? (
        <>
          <div className="bg-white shadow overflow-hidden sm:rounded-md mb-6">
            <ul className="divide-y divide-gray-200">
              {results.map((result) => (
                <li key={result.id}>
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-medium text-blue-600 truncate">
                        <a 
                          href={`/app/documents/${result.document_id}`} 
                          className="hover:underline"
                        >
                          {result.document_name}
                        </a>
                      </h3>
                      <div className="ml-2 flex-shrink-0 flex">
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          {formatDate(result.created_at)}
                        </span>
                      </div>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between">
                      <div className="sm:flex">
                        <div className="flex items-center text-sm text-gray-500 mt-2 sm:mt-0">
                          <div className="bg-gray-50 p-3 rounded border border-gray-200 w-full">
                            <p className="text-gray-800">
                              {result.highlight ? (
                                <span dangerouslySetInnerHTML={{ __html: result.highlight }} />
                              ) : (
                                highlightText(result.content.substring(0, 200) + '...', query)
                              )}
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {/* Pagination */}
          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6 rounded-md shadow">
              <div className="flex flex-1 justify-between sm:hidden">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page === pagination.totalPages}
                  className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing <span className="font-medium">{((pagination.page - 1) * pagination.limit) + 1}</span> to{" "}
                    <span className="font-medium">
                      {Math.min(pagination.page * pagination.limit, pagination.totalResults)}
                    </span>{" "}
                    of <span className="font-medium">{pagination.totalResults}</span> results
                  </p>
                </div>
                <div>
                  <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                    <button
                      onClick={() => handlePageChange(pagination.page - 1)}
                      disabled={pagination.page === 1}
                      className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Previous</span>
                      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
                      </svg>
                    </button>
                    
                    {[...Array(Math.min(5, pagination.totalPages))].map((_, i) => {
                      // Calculate which page numbers to show
                      let pageNum;
                      if (pagination.totalPages <= 5) {
                        // If 5 or fewer pages, show all pages
                        pageNum = i + 1;
                      } else if (pagination.page <= 3) {
                        // If current page is 1, 2, or 3, show pages 1-5
                        pageNum = i + 1;
                      } else if (pagination.page >= pagination.totalPages - 2) {
                        // If current page is among the last 3 pages, show the last 5 pages
                        pageNum = pagination.totalPages - 4 + i;
                      } else {
                        // Otherwise, show 2 pages before and 2 pages after the current page
                        pageNum = pagination.page - 2 + i;
                      }
                      
                      return (
                        <button
                          key={pageNum}
                          onClick={() => handlePageChange(pageNum)}
                          className={`relative inline-flex items-center px-4 py-2 text-sm font-semibold ${
                            pagination.page === pageNum
                              ? 'z-10 bg-blue-600 text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                              : 'text-gray-900 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:outline-offset-0'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                    
                    <button
                      onClick={() => handlePageChange(pagination.page + 1)}
                      disabled={pagination.page === pagination.totalPages}
                      className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <span className="sr-only">Next</span>
                      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                        <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
};

export default Search;