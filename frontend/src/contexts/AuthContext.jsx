import React, { createContext, useState, useEffect } from 'react';
import { getCurrentUser, logout } from '../api/auth';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load user from localStorage on app start
    const loadUser = async () => {
      try {
        const userData = getCurrentUser();
        if (userData) {
          setUser(userData);
          setIsAuthenticated(true);
        }
      } catch (error) {
        console.error("Failed to load user:", error);
        // Clear invalid auth data
        logout();
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const logoutUser = () => {
    logout();
    setUser(null);
    setIsAuthenticated(false);
  };

  const updateUser = (userData) => {
    setUser(userData);
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      isAuthenticated, 
      loading,
      logout: logoutUser,
      updateUser
    }}>
      {children}
    </AuthContext.Provider>
  );
};