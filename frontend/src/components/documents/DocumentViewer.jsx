import React, { useState, useEffect, useRef } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { useParams, useNavigate } from 'react-router-dom';
import { getDocument, deleteDocument, reprocessDocument } from '../../api/documents';
import DocumentTags from './DocumentTags';
import DocChunksViewer from './DocChunksViewer';
import LoadingSpinner from '../common/LoadingSpinner';

// PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const DocumentViewer = () => {
  const { documentId } = useParams();
  const navigate = useNavigate();
  const [document, setDocument] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [numPages, setNumPages] = useState(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [pdfScale, setPdfScale] = useState(1.0);
  const [viewMode, setViewMode] = useState('chunks'); // 'pdf' or 'chunks'
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isReprocessing, setIsReprocessing] = useState(false);
  const documentRef = useRef(null);

  useEffect(() => {
    loadDocument();
  }, [documentId]);

  const loadDocument = async () => {
    try {
      setLoading(true);
      const docData = await getDocument(documentId);
      setDocument(docData);
      
      // Load chunks too if they exist
      if (docData.chunks) {
        setChunks(docData.chunks);
      }
      
      setError(null);
    } catch (err) {
      console.error('Error loading document:', err);
      setError('Failed to load document. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const onDocumentLoadSuccess = ({ numPages }) => {
    setNumPages(numPages);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= numPages) {
      setPageNumber(newPage);
    }
  };

  const handleZoomIn = () => {
    setPdfScale((prevScale) => Math.min(prevScale + 0.2, 3.0));
  };

  const handleZoomOut = () => {
    setPdfScale((prevScale) => Math.max(prevScale - 0.2, 0.5));
  };

  const handleResetZoom = () => {
    setPdfScale(1.0);
  };

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      await deleteDocument(documentId);
      setShowDeleteModal(false);
      navigate('/app/documents');
    } catch (err) {
      console.error('Error deleting document:', err);
      setError('Failed to delete document. Please try again later.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleReprocess = async () => {
    try {
      setIsReprocessing(true);
      await reprocessDocument(documentId);
      // Reload document
      loadDocument();
    } catch (err) {
      console.error('Error reprocessing document:', err);
      setError('Failed to reprocess document. Please try again later.');
    } finally {
      setIsReprocessing(false);
    }
  };

  const renderContentByType = () => {
    if (!document) return null;

    if (viewMode === 'pdf' && document.content_type && document.content_type.includes('pdf')) {
      return (
        <div className="pdf-container bg-gray-100 p-4 rounded-lg">
          <div className="flex justify-center my-4">
            <div className="flex items-center space-x-2">
              <button 
                onClick={handleZoomOut} 
                className="p-2 bg-white rounded-full shadow hover:bg-gray-50"
                title="Zoom Out"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <span className="text-sm text-gray-700">{Math.round(pdfScale * 100)}%</span>
              <button 
                onClick={handleZoomIn} 
                className="p-2 bg-white rounded-full shadow hover:bg-gray-50"
                title="Zoom In"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </button>
              <button 
                onClick={handleResetZoom} 
                className="p-2 bg-white rounded-full shadow hover:bg-gray-50 ml-2"
                title="Reset Zoom"
              >
                <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
          </div>

          <div className="flex justify-center shadow-lg">
            <Document
              file={`/api/v1/documents/${documentId}/download`}
              onLoadSuccess={onDocumentLoadSuccess}
              loading={<div className="flex justify-center py-10"><LoadingSpinner size="large" /></div>}
              error={<div className="text-red-500 text-center py-10">Failed to load PDF. Please try again.</div>}
              className="document-container"
            >
              <Page 
                pageNumber={pageNumber} 
                scale={pdfScale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="pdf-page"
              />
            </Document>
          </div>

          {numPages && (
            <div className="flex justify-center items-center space-x-4 mt-4">
              <button
                onClick={() => handlePageChange(pageNumber - 1)}
                disabled={pageNumber <= 1}
                className={`p-2 rounded-lg ${pageNumber <= 1 ? 'text-gray-400 cursor-not-allowed' : 'text-gray-700 hover:bg-gray-200'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <span className="text-sm font-medium">
                Page {pageNumber} of {numPages}
              </span>
              <button
                onClick={() => handlePageChange(pageNumber + 1)}
                disabled={pageNumber >= numPages}
                className={`p-2 rounded-lg ${pageNumber >= numPages ? 'text-gray-400 cursor-not-allowed' : 'text-gray-700 hover:bg-gray-200'}`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          )}
        </div>
      );
    } else {
      return (
        <DocChunksViewer 
          chunks={chunks} 
          documentId={documentId} 
          onChunksLoaded={(newChunks) => setChunks(newChunks)} 
        />
      );
    }
  };

  const renderDeleteModal = () => (
    <div className={`fixed inset-0 z-10 ${showDeleteModal ? 'flex' : 'hidden'} items-center justify-center bg-black bg-opacity-50`}>
      <div className="bg-white rounded-lg p-6 max-w-md mx-auto">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Document</h3>
        <p className="text-sm text-gray-500 mb-4">
          Are you sure you want to delete "{document?.filename}"? This action cannot be undone.
        </p>
        <div className="flex justify-end space-x-3">
          <button
            onClick={() => setShowDeleteModal(false)}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
            disabled={isDeleting}
          >
            {isDeleting ? <LoadingSpinner size="small" /> : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 my-4">
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

  if (!document) {
    return <div className="text-center py-10">Document not found</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8" ref={documentRef}>
      {/* Document Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">
            {document.metadata?.title || document.filename}
          </h1>
          <p className="text-sm text-gray-500">
            {document.content_type} • {formatFileSize(document.file_size)}
          </p>
        </div>
        <div className="flex mt-4 sm:mt-0">
          <button
            onClick={() => setViewMode(viewMode === 'pdf' ? 'chunks' : 'pdf')}
            className="mr-3 px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
            disabled={!document.content_type?.includes('pdf')}
          >
            View as {viewMode === 'pdf' ? 'Chunks' : 'PDF'}
          </button>
          <button
            onClick={handleReprocess}
            className="mr-3 px-4 py-2 bg-white border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50"
            disabled={isReprocessing}
          >
            {isReprocessing ? <LoadingSpinner size="small" /> : 'Reprocess'}
          </button>
          <button
            onClick={() => setShowDeleteModal(true)}
            className="px-4 py-2 bg-red-600 border border-transparent rounded-md shadow-sm text-sm font-medium text-white hover:bg-red-700"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Status Badge */}
      <div className="mb-6">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
          document.processing_status === 'ready' ? 'bg-green-100 text-green-800' : 
          document.processing_status === 'processing' ? 'bg-blue-100 text-blue-800' :
          document.processing_status === 'error' ? 'bg-red-100 text-red-800' : 
          'bg-yellow-100 text-yellow-800'
        }`}>
          {document.processing_status === 'ready' ? 'Processed' : 
           document.processing_status === 'processing' ? 'Processing' :
           document.processing_status === 'error' ? 'Error' : 'Pending'}
        </span>
      </div>

      {/* Tags */}
      <div className="mb-6">
        <DocumentTags 
          documentId={documentId} 
          initialTags={document.metadata?.tags || []} 
          onTagsUpdated={(updatedTags) => {
            // Update local document state
            setDocument({
              ...document,
              metadata: {
                ...document.metadata,
                tags: updatedTags
              }
            });
          }}
        />
      </div>

      {/* Document Content */}
      <div className="mb-8">
        {renderContentByType()}
      </div>

      {/* Delete Modal */}
      {renderDeleteModal()}
    </div>
  );
};

// Helper function to format file size
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export default DocumentViewer;