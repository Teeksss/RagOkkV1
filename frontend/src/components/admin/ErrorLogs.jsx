import React, { useState } from 'react';

const ErrorLogs = ({ errors }) => {
  const [expandedErrors, setExpandedErrors] = useState({});

  const toggleExpand = (errorId) => {
    setExpandedErrors({
      ...expandedErrors,
      [errorId]: !expandedErrors[errorId]
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  if (!errors || errors.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Error Logs</h3>
        <div className="text-center py-6 text-gray-500">No errors found.</div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Error Logs</h3>
      
      <div className="space-y-4">
        {errors.map((error) => (
          <div key={error.id} className="border border-red-200 rounded-md overflow-hidden">
            <div 
              className="bg-red-50 px-4 py-3 flex justify-between items-center cursor-pointer"
              onClick={() => toggleExpand(error.id)}
            >
              <div>
                <p className="font-medium text-red-800">{error.operation}</p>
                <p className="text-sm text-red-600">{formatDate(error.timestamp)}</p>
              </div>
              <div className="flex">
                {error.status_code && (
                  <span className="px-2 py-1 text-xs font-medium rounded-md bg-red-100 text-red-800 mr-2">
                    {error.status_code}
                  </span>
                )}
                <svg 
                  className={`h-5 w-5 text-red-500 transform ${expandedErrors[error.id] ? 'rotate-180' : ''}`} 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            
            {expandedErrors[error.id] && (
              <div className="px-4 py-3 bg-white border-t border-red-200">
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-gray-500">Error Message</h4>
                  <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{error.message}</p>
                </div>
                
                {error.request_path && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-500">Request</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {error.request_method} {error.request_path}
                    </p>
                  </div>
                )}
                
                {error.user_id && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-500">User ID</h4>
                    <p className="mt-1 text-sm text-gray-900">{error.user_id}</p>
                  </div>
                )}
                
                {error.data && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-500">Additional Data</h4>
                    <pre className="mt-1 text-sm text-gray-900 bg-gray-50 p-2 rounded overflow-auto">
                      {JSON.stringify(error.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ErrorLogs;