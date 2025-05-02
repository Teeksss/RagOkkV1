import React, { useState, useEffect } from 'react';
import { getAllTags } from '../../api/documents';

const DocumentFilters = ({ onFiltersChanged, initialFilters = {} }) => {
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState(initialFilters.tags || []);
  const [fileTypes, setFileTypes] = useState([
    { id: 'pdf', name: 'PDF', selected: initialFilters.types?.includes('pdf') || false },
    { id: 'doc', name: 'Word', selected: initialFilters.types?.includes('doc') || false },
    { id: 'image', name: 'Images', selected: initialFilters.types?.includes('image') || false },
    { id: 'text', name: 'Text', selected: initialFilters.types?.includes('text') || false },
  ]);
  const [dateRange, setDateRange] = useState({
    from: initialFilters.from || '',
    to: initialFilters.to || ''
  });
  const [searchText, setSearchText] = useState(initialFilters.text || '');
  
  useEffect(() => {
    fetchTags();
  }, []);
  
  useEffect(() => {
    applyFilters();
  }, [selectedTags, fileTypes, dateRange]);
  
  const fetchTags = async () => {
    try {
      const allTags = await getAllTags();
      setTags(allTags);
    } catch (err) {
      console.error('Error fetching tags:', err);
    }
  };
  
  const handleTagToggle = (tagName) => {
    setSelectedTags(prev => {
      if (prev.includes(tagName)) {
        return prev.filter(tag => tag !== tagName);
      } else {
        return [...prev, tagName];
      }
    });
  };
  
  const handleFileTypeToggle = (fileTypeId) => {
    setFileTypes(prev => 
      prev.map(type => 
        type.id === fileTypeId 
          ? { ...type, selected: !type.selected } 
          : type
      )
    );
  };
  
  const handleDateChange = (field, value) => {
    setDateRange(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  const handleSearch = (e) => {
    e.preventDefault();
    applyFilters();
  };
  
  const clearFilters = () => {
    setSelectedTags([]);
    setFileTypes(fileTypes.map(type => ({ ...type, selected: false })));
    setDateRange({ from: '', to: '' });
    setSearchText('');
    
    // Update parent component
    onFiltersChanged({});
  };
  
  const applyFilters = () => {
    const selectedTypes = fileTypes
      .filter(type => type.selected)
      .map(type => type.id);
    
    const filters = {
      tags: selectedTags.length > 0 ? selectedTags : undefined,
      types: selectedTypes.length > 0 ? selectedTypes : undefined,
      from: dateRange.from || undefined,
      to: dateRange.to || undefined,
      text: searchText.trim() || undefined
    };
    
    // Remove undefined properties
    Object.keys(filters).forEach(key => 
      filters[key] === undefined && delete filters[key]
    );
    
    // Update parent component
    onFiltersChanged(filters);
  };
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Filter Documents</h3>
      
      <form onSubmit={handleSearch} className="mb-4">
        <div className="relative">
          <input
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search documents..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg className="h-5 w-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
            </svg>
          </div>
          <button
            type="submit"
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-blue-600 hover:text-blue-800"
          >
            Search
          </button>
        </div>
      </form>
      
      <div className="space-y-4">
        {/* Tags */}
        {tags.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Tags</h4>
            <div className="flex flex-wrap gap-2">
              {tags.map(tag => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => handleTagToggle(tag)}
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    selectedTags.includes(tag)
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                  }`}
                >
                  {tag}
                  {selectedTags.includes(tag) && (
                    <svg className="ml-1.5 h-2 w-2 text-blue-400" fill="currentColor" viewBox="0 0 8 8">
                      <circle cx="4" cy="4" r="3" />
                    </svg>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* File Types */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">File Types</h4>
          <div className="flex flex-wrap gap-2">
            {fileTypes.map(type => (
              <button
                key={type.id}
                type="button"
                onClick={() => handleFileTypeToggle(type.id)}
                className={`inline-flex items-center px-3 py-1 rounded-md text-xs font-medium ${
                  type.selected
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
                }`}
              >
                {type.name}
                {type.selected && (
                  <svg className="ml-1.5 h-3 w-3 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
        
        {/* Date Range */}
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Date Range</h4>
          <div className="flex gap-4">
            <div className="flex-1">
              <label htmlFor="date-from" className="block text-xs text-gray-500 mb-1">From</label>
              <input
                type="date"
                id="date-from"
                value={dateRange.from}
                onChange={(e) => handleDateChange('from', e.target.value)}
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="flex-1">
              <label htmlFor="date-to" className="block text-xs text-gray-500 mb-1">To</label>
              <input
                type="date"
                id="date-to"
                value={dateRange.to}
                onChange={(e) => handleDateChange('to', e.target.value)}
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-1.5 text-sm focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={clearFilters}
            className="mr-3 px-3 py-1.5 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Clear Filters
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentFilters;