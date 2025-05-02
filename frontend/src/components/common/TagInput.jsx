import React, { useState, useEffect, useRef } from 'react';

const TagInput = ({ 
  tags, 
  onTagsChange, 
  placeholder = 'Add a tag...',
  suggestions = [],
  maxTags = 10
}) => {
  const [input, setInput] = useState('');
  const [isValid, setIsValid] = useState(true);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState([]);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(0);
  const inputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Filter suggestions based on input
  useEffect(() => {
    if (input.trim()) {
      const filtered = suggestions.filter(
        suggestion => 
          suggestion.toLowerCase().includes(input.toLowerCase()) && 
          !tags.includes(suggestion)
      );
      setFilteredSuggestions(filtered);
      setSelectedSuggestionIndex(0);
    } else {
      setFilteredSuggestions([]);
    }
  }, [input, suggestions, tags]);

  // Handle clicks outside the component to close suggestion box
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        suggestionsRef.current && 
        !suggestionsRef.current.contains(event.target) &&
        inputRef.current &&
        !inputRef.current.contains(event.target)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const addTag = (tag) => {
    // Normalize the tag
    const trimmedTag = tag.trim();
    
    // Validate tag
    if (!trimmedTag) {
      return;
    }
    
    // Check for maximum tags
    if (tags.length >= maxTags) {
      setIsValid(false);
      setTimeout(() => setIsValid(true), 2000);
      return;
    }
    
    // Check for duplicates
    if (tags.includes(trimmedTag)) {
      setIsValid(false);
      setTimeout(() => setIsValid(true), 2000);
      return;
    }
    
    // Add tag
    onTagsChange([...tags, trimmedTag]);
    setInput('');
    setShowSuggestions(false);
  };

  const removeTag = (indexToRemove) => {
    onTagsChange(tags.filter((_, index) => index !== indexToRemove));
  };

  const handleInputChange = (e) => {
    setInput(e.target.value);
    setShowSuggestions(true);
  };

  const handleKeyDown = (e) => {
    // Check if suggestions are available
    const hasSuggestions = filteredSuggestions.length > 0;
    
    if (e.key === 'Enter') {
      e.preventDefault();
      
      if (hasSuggestions && showSuggestions) {
        // Add selected suggestion
        addTag(filteredSuggestions[selectedSuggestionIndex]);
      } else if (input) {
        // Add current input
        addTag(input);
      }
    } else if (e.key === 'ArrowDown' && hasSuggestions && showSuggestions) {
      e.preventDefault();
      setSelectedSuggestionIndex(prevIndex => 
        prevIndex < filteredSuggestions.length - 1 ? prevIndex + 1 : 0
      );
    } else if (e.key === 'ArrowUp' && hasSuggestions && showSuggestions) {
      e.preventDefault();
      setSelectedSuggestionIndex(prevIndex => 
        prevIndex > 0 ? prevIndex - 1 : filteredSuggestions.length - 1
      );
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    } else if (e.key === 'Backspace' && !input) {
      // Remove last tag when backspace is pressed on empty input
      if (tags.length > 0) {
        removeTag(tags.length - 1);
      }
    } else if (e.key === ',') {
      // Add tag on comma
      if (input) {
        e.preventDefault();
        addTag(input);
      }
    }
  };

  return (
    <div className="w-full">
      <div className={`flex flex-wrap p-2 border rounded-md ${isValid ? 'border-gray-300' : 'border-red-500'}`}>
        {/* Display existing tags */}
        {tags.map((tag, index) => (
          <div
            key={index}
            className="flex items-center bg-blue-100 text-blue-800 text-sm rounded-full px-3 py-1 m-1"
          >
            <span>{tag}</span>
            <button
              type="button"
              onClick={() => removeTag(index)}
              className="ml-2 text-blue-600 hover:text-blue-800 focus:outline-none"
            >
              <span className="sr-only">Remove {tag}</span>
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}
        
        {/* Input for new tags */}
        <div className="flex-grow">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={() => setShowSuggestions(true)}
            placeholder={tags.length ? '' : placeholder}
            className="border-0 outline-none p-2 w-full text-sm bg-transparent"
          />
        </div>
      </div>
      
      {/* Max tags warning */}
      {!isValid && (
        <p className="mt-1 text-xs text-red-500">
          {tags.length >= maxTags 
            ? `Maximum ${maxTags} tags allowed.` 
            : 'This tag already exists.'}
        </p>
      )}
      
      {/* Tag suggestions */}
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div 
          ref={suggestionsRef}
          className="mt-1 absolute z-10 w-full bg-white shadow-lg rounded-md border border-gray-200 max-h-60 overflow-auto"
        >
          <ul className="py-1">
            {filteredSuggestions.map((suggestion, index) => (
              <li
                key={index}
                onClick={() => addTag(suggestion)}
                className={`px-3 py-2 cursor-pointer text-sm ${
                  index === selectedSuggestionIndex 
                    ? 'bg-blue-100 text-blue-900'
                    : 'hover:bg-gray-100'
                }`}
              >
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default TagInput;