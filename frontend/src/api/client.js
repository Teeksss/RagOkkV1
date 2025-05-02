import axios from 'axios';
import { isTokenAboutToExpire } from '../utils/auth';

// API client sınıfı
class ApiClient {
  constructor(baseURL, options = {}) {
    this.client = axios.create({
      baseURL,
      timeout: options.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    this.refreshEndpoint = options.refreshEndpoint || '/auth/refresh';
    this.refreshTokenKey = options.refreshTokenKey || 'refresh_token';
    this.accessTokenKey = options.accessTokenKey || 'access_token';
    this.onUnauthorized = options.onUnauthorized;
    
    this._initializeInterceptors();
  }
  
  // Interceptor kurulumu
  _initializeInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // Access token ekleme
        const token = localStorage.getItem(this.accessTokenKey);
        
        if (token) {
          // Token süresi dolmak üzereyse yenile
          if (isTokenAboutToExpire(token, 300)) { // 5 dakika
            try {
              await this._refreshToken();
              const newToken = localStorage.getItem(this.accessTokenKey);
              config.headers.Authorization = `Bearer ${newToken}`;
            } catch (error) {
              console.warn('Token refresh failed:', error);
              // Token yenilemesi başarısız olsa bile mevcut token ile devam et
              config.headers.Authorization = `Bearer ${token}`;
            }
          } else {
            // Token hala geçerli
            config.headers.Authorization = `Bearer ${token}`;
          }
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // Yanıt 401 (Unauthorized) ise ve daha önce yeniden denenmemişse
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            // Token yenileme
            await this._refreshToken();
            
            // Yeni token ile isteği tekrarla
            const token = localStorage.getItem(this.accessTokenKey);
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return this.client(originalRequest);
          } catch (refreshError) {
            // Token yenileme başarısız
            if (this.onUnauthorized) {
              this.onUnauthorized();
            }
          }
        }
        
        // Hata mesajı standartlaştırma
        if (error.response?.data) {
          error.userMessage = error.response.data.detail || 
                              error.response.data.message || 
                              'An error occurred. Please try again.';
        } else if (error.request) {
          error.userMessage = 'No response from server. Please check your connection.';
        } else {
          error.userMessage = error.message || 'An unexpected error occurred.';
        }
        
        // Hata detayları için console.error
        console.error('API Error:', {
          url: originalRequest?.url,
          method: originalRequest?.method,
          status: error.response?.status,
          data: error.response?.data,
          message: error.message
        });
        
        return Promise.reject(error);
      }
    );
  }
  
  // Token yenileme
  async _refreshToken() {
    const refreshToken = localStorage.getItem(this.refreshTokenKey);
    
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    try {
      // Refresh token ile yeni access token al
      const response = await this.client.post(
        this.refreshEndpoint,
        { refresh_token: refreshToken },
        { skipAuthRefresh: true } // Sonsuz döngüyü engelle
      );
      
      // Yeni tokenları kaydet
      if (response.data.access_token) {
        localStorage.setItem(this.accessTokenKey, response.data.access_token);
      }
      
      if (response.data.refresh_token) {
        localStorage.setItem(this.refreshTokenKey, response.data.refresh_token);
      }
      
      return response.data;
    } catch (error) {
      // Hata durumunda tüm token verilerini temizle
      localStorage.removeItem(this.accessTokenKey);
      localStorage.removeItem(this.refreshTokenKey);
      throw error;
    }
  }
  
  // Temel HTTP metodları
  async get(url, config = {}) {
    try {
      const response = await this.client.get(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
  
  async post(url, data = {}, config = {}) {
    try {
      const response = await this.client.post(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
  
  async put(url, data = {}, config = {}) {
    try {
      const response = await this.client.put(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
  
  async patch(url, data = {}, config = {}) {
    try {
      const response = await this.client.patch(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
  
  async delete(url, config = {}) {
    try {
      const response = await this.client.delete(url, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
  
  // Streaming yanıt için özel metod
  async stream(url, data = {}, options = {}) {
    try {
      const { onChunk, ...config } = options;
      
      config.responseType = 'stream';
      config.onDownloadProgress = (progressEvent) => {
        const response = progressEvent.currentTarget.response || '';
        
        if (response && onChunk) {
          // SSE formatı varsayımı - farklı format için uyarlanmalı
          const chunks = response
            .split('\n\n')
            .filter(Boolean)
            .map(chunk => {
              const dataMatch = chunk.match(/data: (.+)/);
              return dataMatch ? dataMatch[1] : null;
            })
            .filter(Boolean);
          
          chunks.forEach(chunk => {
            try {
              const parsedChunk = JSON.parse(chunk);
              onChunk(parsedChunk);
            } catch (e) {
              console.warn('Error parsing chunk:', e);
              onChunk(chunk);
            }
          });
        }
      };
      
      const response = await this.client.post(url, data, config);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
}

// API client örneği oluştur
export const apiClient = new ApiClient(
  process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  {
    timeout: 60000,
    onUnauthorized: () => {
      // Oturum sonlandırma ve login sayfasına yönlendirme
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Yeniden yönlendirme
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?session=expired';
      }
    }
  }
);