import React, { useState, useEffect, useRef } from 'react';

const TagSelector = ({ availableTags, onTagSelected, onClose }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTags, setFilteredTags] = useState(availableTags);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef(null);
  
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);
  
  useEffect(() => {
    filterTags();
  }, [searchTerm, availableTags]);
  
  const filterTags = () => {
    if (!searchTerm.trim()) {
      setFilteredTags(availableTags);
      return;
    }
    
    const term = searchTerm.toLowerCase();
    const filtered = availableTags.filter(tag => 
      tag.toLowerCase().includes(term)
    );
    
    setFilteredTags(filtered);
    setSelectedIndex(0);
  };
  
  const handleKeyDown = (e) => {
    // Enter - select current tag or create new one
    if (e.key === 'Enter') {
      e.preventDefault();
      
      if (filteredTags.length > 0) {
        // Select existing tag
        onTagSelected(filteredTags[selectedIndex]);
      } else if (searchTerm.trim()) {
        // Create new tag
        onTagSelected(searchTerm.trim());
      }
      return;
    }
    
    // Escape - close dropdown
    if (e.key === 'Escape') {
      onClose();
      return;
    }
    
    // Arrow up - move selection up
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => 
        prev > 0 ? prev - 1 : filteredTags.length - 1
      );
      return;
    }
    
    // Arrow down - move selection down
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => 
        prev < filteredTags.length - 1 ? prev + 1 : 0
      );
      return;
    }
  };
  
  return (
    <div className="relative">
      <div className="absolute mt-1 w-60 bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm z-10">
        <div className="sticky top-0 z-10 bg-white">
          <div className="px-2 py-2">
            <input
              type="text"
              ref={inputRef}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full border-gray-300 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search or create tag..."
            />
          </div>
          <div className="border-t border-gray-200"></div>
        </div>
        
        {filteredTags.length > 0 ? (
          <ul className="max-h-40 overflow-y-auto py-1">
            {filteredTags.map((tag, index) => (
              <li
                key={tag}
                className={`cursor-pointer select-none relative py-2 px-3 text-sm ${
                  index === selectedIndex ? 'bg-blue-600 text-white' : 'text-gray-900 hover:bg-gray-100'
                }`}
                onClick={() => onTagSelected(tag)}
              >
                {tag}
              </li>
            ))}
          </ul>
        ) : (
          <div className="py-2 px-3 text-sm text-gray-700">
            {searchTerm.trim() ? (
              <>
                <p>No matching tags</p>
                <p className="mt-1 text-xs text-blue-600">
                  Press Enter to create "{searchTerm.trim()}"
                </p>
              </>
            ) : (
              <p>No tags available</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TagSelector;