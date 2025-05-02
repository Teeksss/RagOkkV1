import React from 'react';
import { Link } from 'react-router-dom';

const DocumentList = ({ documents, showUsage = true }) => {
  if (!documents || documents.length === 0) {
    return (
      <div className="bg-white shadow overflow-hidden sm:rounded-lg p-6">
        <div className="text-center text-gray-500">
          No documents found.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          {showUsage ? 'Popular Documents' : 'Documents'}
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Document
              </th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              {showUsage && (
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Usage
                </th>
              )}
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {documents.map((doc) => (
              <tr key={doc.document_id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center">
                      {getDocumentIcon(doc.content_type)}
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">{doc.title}</div>
                      <div className="text-sm text-gray-500">{doc.filename}</div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                    {formatContentType(doc.content_type)}
                  </span>
                </td>
                {showUsage && (
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {doc.usage_count} {doc.usage_count === 1 ? 'time' : 'times'}
                  </td>
                )}
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <Link
                    to={`/documents/${doc.document_id}`}
                    className="text-blue-600 hover:text-blue-900 mr-4"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Helper function to get document icon based on content type
const getDocumentIcon = (contentType) => {
  const iconClasses = "h-6 w-6 text-gray-500";
  
  if (contentType && contentType.includes('pdf')) {
    return (
      <svg className={iconClasses} fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
      </svg>
    );
  } else if (contentType && contentType.includes('image')) {
    return (
      <svg className={iconClasses} fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
      </svg>
    );
  } else if (contentType && contentType.includes('word')) {
    return (
      <svg className={iconClasses} fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
      </svg>
    );
  } else {
    return (
      <svg className={iconClasses} fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
      </svg>
    );
  }
};

// Helper function to format content type
const formatContentType = (contentType) => {
  if (!contentType) return 'Unknown';
  
  if (contentType.includes('pdf')) {
    return 'PDF';
  } else if (contentType.includes('word')) {
    return 'Word';
  } else if (contentType.includes('excel') || contentType.includes('spreadsheet')) {
    return 'Excel';
  } else if (contentType.includes('presentation') || contentType.includes('powerpoint')) {
    return 'PowerPoint';
  } else if (contentType.includes('image')) {
    return 'Image';
  } else if (contentType.includes('text/plain')) {
    return 'Text';
  } else if (contentType.includes('html')) {
    return 'HTML';
  } else if (contentType.includes('json')) {
    return 'JSON';
  } else if (contentType.includes('markdown')) {
    return 'Markdown';
  } else {
    return contentType.split('/').pop().toUpperCase();
  }
};

export default DocumentList;