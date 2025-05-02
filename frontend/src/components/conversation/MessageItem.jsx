import React from 'react';
import ReactMarkdown from 'react-markdown';
import { formatDistanceToNow } from 'date-fns';

const MessageItem = ({ message, onThumbsUp, onThumbsDown, isLast }) => {
  const { id, role, content, timestamp, isLoading, isError, feedback } = message;
  
  // Determine message style based on role
  const getMessageStyle = () => {
    switch (role) {
      case 'user':
        return 'bg-blue-50 text-blue-800';
      case 'assistant':
        return isLoading ? 'bg-gray-100 text-gray-500' : 'bg-white text-gray-800 shadow-sm';
      case 'system':
        return isError ? 'bg-red-50 text-red-800' : 'bg-yellow-50 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  // Get avatar component based on role
  const getAvatar = () => {
    switch (role) {
      case 'user':
        return (
          <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          </div>
        );
      case 'assistant':
        return (
          <div className="h-8 w-8 rounded-full bg-purple-500 flex items-center justify-center text-white">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </div>
        );
      case 'system':
        return (
          <div className="h-8 w-8 rounded-full bg-yellow-500 flex items-center justify-center text-white">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1
1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="h-8 w-8 rounded-full bg-gray-400 flex items-center justify-center text-white">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          </div>
        );
    }
  };
  
  const renderLoading = () => (
    <div className="flex space-x-1 items-center">
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse"></div>
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
      <div className="w-2 h-2 bg-gray-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
    </div>
  );
  
  return (
    <div className={`flex items-start ${role === 'user' ? 'justify-end' : ''}`}>
      {role !== 'user' && <div className="mr-3 flex-shrink-0">{getAvatar()}</div>}
      
      <div className={`max-w-3xl rounded-lg px-4 py-2 ${getMessageStyle()}`}>
        {isLoading ? (
          renderLoading()
        ) : (
          <div className="prose prose-sm max-w-none">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
        
        {timestamp && role === 'assistant' && !isLoading && (
          <div className="mt-1 flex items-center justify-between">
            <div className="text-xs text-gray-500">
              {formatDistanceToNow(new Date(timestamp), { addSuffix: true })}
            </div>
            
            {id && isLast && (
              <div className="flex space-x-2">
                <button 
                  onClick={() => onThumbsUp(id)}
                  className={`p-1 rounded-full ${feedback?.thumbs_up ? 'bg-green-100 text-green-600' : 'text-gray-400 hover:text-gray-600'}`}
                  title="Helpful"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                  </svg>
                </button>
                <button 
                  onClick={() => onThumbsDown(id)}
                  className={`p-1 rounded-full ${feedback?.thumbs_down ? 'bg-red-100 text-red-600' : 'text-gray-400 hover:text-gray-600'}`}
                  title="Not helpful"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                    <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                  </svg>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      
      {role === 'user' && <div className="ml-3 flex-shrink-0">{getAvatar()}</div>}
    </div>
  );
};

export default MessageItem;