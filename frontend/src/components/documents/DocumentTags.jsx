import React, { useState, useEffect, useRef } from 'react';
import { updateDocumentTags, getAllTags } from '../../api/documents';
import TagSelector from './TagSelector';

const DocumentTags = ({ documentId, initialTags = [], onTagsUpdated }) => {
  const [tags, setTags] = useState(initialTags);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [availableTags, setAvailableTags] = useState([]);
  const [selectedTag, setSelectedTag] = useState('');
  const dropdownRef = useRef(null);
  
  useEffect(() => {
    fetchAvailableTags();
  }, []);
  
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsEditing(false);
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [dropdownRef]);
  
  const fetchAvailableTags = async () => {
    try {
      const allTags = await getAllTags();
      setAvailableTags(allTags);
    } catch (err) {
      console.error('Error fetching tags:', err);
    }
  };
  
  const handleAddTag = async (tagName) => {
    if (!tagName.trim()) return;
    
    // Check if tag already exists
    if (tags.find(tag => tag.toLowerCase() === tagName.toLowerCase())) return;
    
    try {
      setIsLoading(true);
      const newTags = [...tags, tagName];
      
      // Update on server
      await updateDocumentTags(documentId, newTags);
      
      // Update local state
      setTags(newTags);
      
      // Add to available tags if it's a new tag
      if (!availableTags.find(tag => tag.toLowerCase() === tagName.toLowerCase())) {
        setAvailableTags([...availableTags, tagName]);
      }
      
      // Reset selection
      setSelectedTag('');
      
      // Notify parent component
      if (onTagsUpdated) {
        onTagsUpdated(newTags);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error adding tag:', err);
      setError('Failed to add tag. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleRemoveTag = async (tagToRemove) => {
    try {
      setIsLoading(true);
      const newTags = tags.filter(tag => tag !== tagToRemove);
      
      // Update on server
      await updateDocumentTags(documentId, newTags);
      
      // Update local state
      setTags(newTags);
      
      // Notify parent component
      if (onTagsUpdated) {
        onTagsUpdated(newTags);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error removing tag:', err);
      setError('Failed to remove tag. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div>
      <div className="flex items-center mb-2">
        <h3 className="text-sm font-medium text-gray-700">Tags</h3>
        {error && <p className="ml-3 text-xs text-red-600">{error}</p>}
      </div>
      
      <div className="flex flex-wrap items-center gap-2" ref={dropdownRef}>
        {tags.length > 0 ? (
          tags.map((tag) => (
            <span 
              key={tag} 
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
            >
              {tag}
              <button
                type="button"
                onClick={() => handleRemoveTag(tag)}
                disabled={isLoading}
                className="flex-shrink-0 ml-1 h-4 w-4 rounded-full inline-flex items-center justify-center text-blue-400 hover:bg-blue-200 hover:text-blue-500 focus:outline-none focus:bg-blue-500 focus:text-white"
              >
                <span className="sr-only">Remove {tag} tag</span>
                <svg className="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8">
                  <path strokeLinecap="round" strokeWidth="1.5" d="M1 1l6 6m0-6L1 7" />
                </svg>
              </button>
            </span>
          ))
        ) : (
          <span className="text-sm text-gray-500">No tags</span>
        )}
        
        {isEditing ? (
          <TagSelector 
            availableTags={availableTags.filter(tag => !tags.includes(tag))} 
            onTagSelected={handleAddTag} 
            onClose={() => setIsEditing(false)} 
          />
        ) : (
          <button
            type="button"
            onClick={() => setIsEditing(true)}
            className="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg className="h-3 w-3 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
            </svg>
            Add Tag
          </button>
        )}
      </div>
    </div>
  );
};

export default DocumentTags;