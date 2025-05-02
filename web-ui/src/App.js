import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import Dashboard from './components/dashboard/Dashboard';
import DocumentUpload from './components/documents/DocumentUpload';
import DocumentList from './components/documents/DocumentList';
import Chat from './components/chat/Chat';
import QueryInterface from './components/query/QueryInterface';  // Added import
import Settings from './components/settings/Settings';
import Navigation from './components/layout/Navigation';
import PrivateRoute from './components/auth/PrivateRoute';
import { AuthProvider } from './contexts/AuthContext';
import { ApiProvider } from './contexts/ApiContext';
import './App.css';

const theme = extendTheme({
  colors: {
    brand: {
      50: '#e6f7ff',
      100: '#b3e0ff',
      500: '#0086ff',
      600: '#0066cc',
      700: '#004d99',
    },
  },
  fonts: {
    heading: '"Inter", sans-serif',
    body: '"Inter", sans-serif',
  },
});

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Router>
        <AuthProvider>
          <ApiProvider>
            <div className="app-container">
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/" element={
                  <PrivateRoute>
                    <Navigation>
                      <Dashboard />
                    </Navigation>
                  </PrivateRoute>
                } />
                <Route path="/documents" element={
                  <PrivateRoute>
                    <Navigation>
                      <DocumentList />
                    </Navigation>
                  </PrivateRoute>
                } />
                <Route path="/upload" element={
                  <PrivateRoute>
                    <Navigation>
                      <DocumentUpload />
                    </Navigation>
                  </PrivateRoute>
                } />
                <Route path="/chat" element={
                  <PrivateRoute>
                    <Navigation>
                      <Chat />
                    </Navigation>
                  </PrivateRoute>
                } />
                <Route path="/query" element={  // Add this route
                  <PrivateRoute>
                    <Navigation>
                      <QueryInterface />
                    </Navigation>
                  </PrivateRoute>
                } />
                <Route path="/settings" element={
                  <PrivateRoute>
                    <Navigation>
                      <Settings />
                    </Navigation>
                  </PrivateRoute>
                } />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </div>
          </ApiProvider>
        </AuthProvider>
      </Router>
    </ChakraProvider>
  );
}

export default App;