import React, { createContext, useContext, useState, useCallback } from 'react';
import { getDocument, getDocumentChunks, updateDocumentMetadata, deleteDocument } from '../api/documents';

const DocumentContext = createContext();

export const DocumentProvider = ({ children, documentId }) => {
  const [document, setDocument] = useState(null);
  const [chunks, setChunks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    totalPages: 1,
    totalItems: 0,
    limit: 10
  });

  // Belge yükleme
  const loadDocument = useCallback(async () => {
    if (!documentId) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const result = await getDocument(documentId);
      setDocument(result);
      
      return result;
    } catch (err) {
      console.error('Error loading document:', err);
      setError(err.message || 'Failed to load document');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  // Belge parçalarını yükleme
  const loadChunks = useCallback(async (page = 1, limit = 10) => {
    if (!documentId) return;
    
    try {
      const result = await getDocumentChunks(documentId, page, limit);
      
      setChunks(result.items || []);
      setPagination({
        page: result.page,
        totalPages: result.total_pages,
        totalItems: result.total_items,
        limit: result.limit
      });
      
      return result;
    } catch (err) {
      console.error('Error loading document chunks:', err);
    }
  }, [documentId]);

  // Belge güncelleme
  const updateDocument = useCallback(async (metadata) => {
    if (!documentId) return;
    
    try {
      setLoading(true);
      
      const result = await updateDocumentMetadata(documentId, metadata);
      
      // Belgeyi güncelle
      setDocument(prevDoc => ({
        ...prevDoc,
        ...result
      }));
      
      return result;
    } catch (err) {
      console.error('Error updating document:', err);
      setError(err.message || 'Failed to update document');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  // Belge silme
  const removeDocument = useCallback(async () => {
    if (!documentId) return;
    
    try {
      setLoading(true);
      
      await deleteDocument(documentId);
      
      return true;
    } catch (err) {
      console.error('Error deleting document:', err);
      setError(err.message || 'Failed to delete document');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  return (
    <DocumentContext.Provider
      value={{
        document,
        chunks,
        loading,
        error,
        pagination,
        loadDocument,
        loadChunks,
        updateDocument,
        removeDocument,
        setError
      }}
    >
      {children}
    </DocumentContext.Provider>
  );
};

// Kullanım hook'u
export const useDocument = () => {
  const context = useContext(DocumentContext);
  
  if (!context) {
    throw new Error('useDocument must be used within a DocumentProvider');
  }
  
  return context;
};