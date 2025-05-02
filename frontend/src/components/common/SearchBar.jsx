import React, { useState, useEffect, useRef } from 'react';

const SearchBar = ({ onSearch, placeholder, initialValue = '', showButton = true }) => {
  const [searchTerm, setSearchTerm] = useState(initialValue);
  const inputRef = useRef(null);

  useEffect(() => {
    // Update search term when initialValue changes
    if (initialValue !== searchTerm) {
      setSearchTerm(initialValue);
    }
  }, [initialValue]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(searchTerm);
  };

  const handleKeyDown = (e) => {
    // Submit on Enter
    if (e.key === 'Enter') {
      handleSubmit(e);
    }
  };

  const handleClear = () => {
    setSearchTerm('');
    onSearch('');
    inputRef.current?.focus();
  };

  return (
    <div className="w-full max-w-3xl">
      <form onSubmit={handleSubmit} className="relative flex">
        <div className="relative flex-grow">
          <input
            type="text"
            ref={inputRef}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder || "Search..."}
            className="w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          {searchTerm && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute inset-y-0 right-0 pr-3 flex items-center"
            >
              <svg className="h-5 w-5 text-gray-400 hover:text-gray-500" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </button>
          )}
        </div>
        {showButton && (
          <button
            type="submit"
            className="ml-3 inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Search
          </button>
        )}
      </form>
    </div>
  );
};

export default SearchBar;