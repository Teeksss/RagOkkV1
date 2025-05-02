import { useQuery, useMutation, useQueryClient } from 'react-query';
import { getDocuments, uploadDocument, deleteDocument } from '../api/documents';

// Belge listesi için hook
export const useDocuments = (params = {}) => {
  return useQuery(
    ['documents', params],
    () => getDocuments(params),
    {
      keepPreviousData: true,
      staleTime: 30000, // 30 saniye
      refetchOnWindowFocus: false
    }
  );
};

// Belge yükleme mutasyonu
export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    ({ file, metadata, onProgress }) => uploadDocument(file, metadata, onProgress),
    {
      onSuccess: () => {
        // Başarılı yüklemeden sonra belge listesini yenile
        queryClient.invalidateQueries('documents');
      }
    }
  );
};

// Belge silme mutasyonu
export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation(
    (documentId) => deleteDocument(documentId),
    {
      onSuccess: () => {
        // Başarılı silmeden sonra belge listesini yenile
        queryClient.invalidateQueries('documents');
      }
    }
  );
};