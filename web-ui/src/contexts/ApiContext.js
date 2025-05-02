// ... [previous code remains the same] ...

// API methods
const api = {
    // ... [previous methods remain the same] ...
    
    // Query LLM
    getQueryResponse: async (query, model = null, filters = null) => {
      setIsLoading(true);
      
      try {
        const response = await axiosInstance.post('/query', {
          query,
          model,
          filters
        });
        
        return response.data;
      } finally {
        setIsLoading(false);
      }
    },
    
    // Get available LLM models
    getAvailableModels: async () => {
      setIsLoading(true);
      
      try {
        const response = await axiosInstance.get('/query/models');
        return response.data;
      } finally {
        setIsLoading(false);
      }
    }
};

// ... [rest of the code remains the same] ...