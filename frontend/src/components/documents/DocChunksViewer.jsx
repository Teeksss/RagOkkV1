import React, { useState, useEffect } from 'react';
import { getDocumentChunks } from '../../api/documents';
import LoadingSpinner from '../common/LoadingSpinner';

const DocChunksViewer = ({ documentId, chunks: initialChunks, onChunksLoaded }) => {
  const [chunks, setChunks] = useState(initialChunks || []);
  const [loading, setLoading] = useState(!initialChunks || initialChunks.length === 0);
  const [error, setError] = useState(null);
  const [expandedChunks, setExpandedChunks] = useState({});

  useEffect(() => {
    if (!initialChunks || initialChunks.length === 0) {
      loadChunks();
    }
  }, [documentId, initialChunks]);

  const loadChunks = async () => {
    try {
      setLoading(true);
      const fetchedChunks = await getDocumentChunks(documentId);
      setChunks(fetchedChunks);
      if (onChunksLoaded) {
        onChunksLoaded(fetchedChunks);
      }
      setError(null);
    } catch (err) {
      console.error('Error loading document chunks:', err);
      setError('Failed to load document chunks. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleChunk = (chunkId) => {
    setExpandedChunks(prev => ({
      ...prev,
      [chunkId]: !prev[chunkId]
    }));
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-10">
        <LoadingSpinner size="medium" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4">
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
    );
  }

  if (!chunks || chunks.length === 0) {
    return (
      <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
        <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No chunks found</h3>
        <p className="mt-1 text-sm text-gray-500">This document has not been processed yet or doesn't contain any text.</p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow-sm border border-gray-200 rounded-lg overflow-hidden">
      <div className="px-4 py-5 sm:px-6 bg-gray-50">
        <h3 className="text-lg leading-6 font-medium text-gray-900">Document Chunks</h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          This document has been split into {chunks.length} chunks for processing.
        </p>
      </div>
      <ul className="divide-y divide-gray-200">
        {chunks.map((chunk) => (
          <li 
            key={chunk.id} 
            className={`hover:bg-gray-50 transition-colors ${expandedChunks[chunk.id] ? 'bg-blue-50' : ''}`}
          >
            <div 
              className="px-4 py-4 sm:px-6 cursor-pointer"
              onClick={() => toggleChunk(chunk.id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="flex-shrink-0 h-6 w-6 rounded-full bg-blue-100 flex items-center justify-center text-blue-800 text-xs font-medium">
                    {chunk.chunk_index + 1}
                  </span>
                  <div className="ml-3 overflow-hidden">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {expandedChunks[chunk.id] ? 'Collapse' : 'Expand'} Chunk {chunk.chunk_index + 1}
                    </p>
                    {!expandedChunks[chunk.id] && (
                      <p className="text-sm text-gray-500 truncate">
                        {chunk.content.substring(0, 100)}...
                      </p>
                    )}
                  </div>
                </div>
                <div>
                  <svg 
                    className={`h-5 w-5 text-gray-400 transform ${expandedChunks[chunk.id] ? 'rotate-180' : ''} transition-transform`} 
                    viewBox="0 0 20 20" 
                    fill="currentColor"
                  >
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </div>
              </div>
              {expandedChunks[chunk.id] && (
                <div className="mt-3">
                  <div className="text-sm text-gray-800 whitespace-pre-wrap bg-white p-3 rounded-md border border-gray-200">
                    {chunk.content}
                  </div>
                  {chunk.metadata && Object.keys(chunk.metadata).length > 0 && (
                    <div className="mt-2">
                      <details className="text-xs">
                        <summary className="text-blue-600 cursor-pointer">Chunk Metadata</summary>
                        <pre className="mt-1 text-gray-600 bg-gray-50 p-2 rounded text-xs overflow-auto">
                          {JSON.stringify(chunk.metadata, null, 2)}
                        </pre>
                      </details>
                    </div>
                  )}
                </div>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default DocChunksViewer;