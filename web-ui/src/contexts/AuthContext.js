import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Initialize authentication state from local storage
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('token') || sessionStorage.getItem('token');
      
      if (token) {
        try {
          // Set default authorization header
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // Fetch user info
          const response = await axios.get(`${API_URL}/me`);
          setUser(response.data);
        } catch (error) {
          console.error('Auth initialization error:', error);
          // Clear invalid token
          localStorage.removeItem('token');
          sessionStorage.removeItem('token');
          axios.defaults.headers.common['Authorization'] = '';
        }
      }
      
      setIsLoading(false);
    };
    
    initAuth();
  }, []);
  
  const login = async (email, password, rememberMe = false) => {
    try {
      const response = await axios.post(`${API_URL}/login`, {
        username: email,
        password: password
      });
      
      const { access_token, refresh_token } = response.data;
      
      // Store token based on "remember me" preference
      if (rememberMe) {
        localStorage.setItem('token', access_token);
        localStorage.setItem('refresh_token', refresh_token);
      } else {
        sessionStorage.setItem('token', access_token);
        sessionStorage.setItem('refresh_token', refresh_token);
      }
      
      // Set default authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Fetch user info
      const userResponse = await axios.get(`${API_URL}/me`);
      setUser(userResponse.data);
      
      return userResponse.data;
    } catch (error) {
      setError(error.response?.data?.detail || 'Giriş başarısız');
      throw error;
    }
  };
  
  const register = async (name, email, password, passwordConfirm) => {
    try {
      const response = await axios.post(`${API_URL}/register`, {
        name,
        email,
        password,
        password_confirm: passwordConfirm
      });
      
      return response.data;
    } catch (error) {
      setError(error.response?.data?.detail || 'Kayıt başarısız');
      throw error;
    }
  };
  
  const logout = () => {
    // Clear tokens
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('token');
    sessionStorage.removeItem('refresh_token');
    
    // Clear authorization header
    axios.defaults.headers.common['Authorization'] = '';
    
    // Clear user state
    setUser(null);
  };
  
  const refreshToken = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token');
      
      if (!refresh_token) {
        throw new Error('No refresh token available');
      }
      
      const response = await axios.post(`${API_URL}/token/refresh`, {
        refresh_token
      });
      
      const { access_token, refresh_token: new_refresh_token } = response.data;
      
      // Update stored tokens
      if (localStorage.getItem('token')) {
        localStorage.setItem('token', access_token);
        localStorage.setItem('refresh_token', new_refresh_token);
      } else {
        sessionStorage.setItem('token', access_token);
        sessionStorage.setItem('refresh_token', new_refresh_token);
      }
      
      // Update authorization header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return access_token;
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
      throw error;
    }
  };
  
  const value = {
    user,
    isLoading,
    error,
    login,
    register,
    logout,
    refreshToken,
    isAuthenticated: !!user
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};