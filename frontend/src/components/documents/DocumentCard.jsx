import React, { memo, useCallback } from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';
import { formatFileSize, formatDate } from '../../utils/formatting';

/**
 * Belge kartı bileşeni
 * React.memo ile sarılmış, sadece prop değişikliklerinde yeniden render edilir
 */
const DocumentCard = memo(({ document, onDelete }) => {
  // Silme işleyicisini memoize et
  const handleDelete = useCallback(() => {
    if (onDelete) {
      onDelete(document.id);
    }
  }, [document.id, onDelete]);
  
  // Belge durumuna göre renk sınıfını belirle
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  return (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            {/* Belge tipi ikonu */}
            {document.content_type?.includes('pdf') ? (
              <svg className="h-10 w-10 text-red-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            ) : document.content_type?.includes('word') || document.content_type?.includes('document') ? (
              <svg className="h-10 w-10 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            ) : (
              <svg className="h-10 w-10 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            )}
          </div>
          <div className="ml-5 w-0 flex-1">
            <Link to={`/app/documents/${document.id}`} className="text-lg font-medium text-blue-600 truncate hover:underline">
              {document.filename}
            </Link>
            <div className="mt-1 flex items-center text-sm text-gray-500">
              <span className="truncate">Uploaded {formatDate(document.created_at)}</span>
            </div>
            <div className="mt-2 flex">
              <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(document.processing_status)}`}>
                {document.processing_status}
              </span>
              <span className="ml-2 text-sm text-gray-500">
                {formatFileSize(document.file_size)}
              </span>
            </div>
            {document.tags && document.tags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {document.tags.map((tag, idx) => (
                  <span 
                    key={idx} 
                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              type="button"
              onClick={handleDelete}
              className="text-gray-400 hover:text-red-500"
              aria-label="Delete document"
            >
              <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V