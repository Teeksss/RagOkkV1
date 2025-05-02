import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';

// Layouts
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';
import AdminLayout from './layouts/AdminLayout';

// Public Pages
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Home from './pages/Home';

// Protected Pages
import Dashboard from './pages/Dashboard';
import DocumentsList from './pages/DocumentsList';
import DocumentView from './pages/DocumentView';
import DocumentUpload from './pages/DocumentUpload';
import ConversationsList from './pages/ConversationsList';
import Conversation from './pages/Conversation';
import Profile from './pages/Profile';
import Search from './pages/Search';

// Admin Pages
import AdminDashboard from './components/admin/AdminDashboard';
import UserManagement from './pages/admin/UserManagement';
import APIKeyManager from './components/admin/APIKeyManager';
import SystemSettings from './pages/admin/SystemSettings';
import ABTestManager from './pages/admin/ABTestManager';

// Error Pages
import NotFound from './pages/NotFound';

// Private Route Component
import PrivateRoute from './components/common/PrivateRoute';
import RoleGuard from './components/common/RoleGuard';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Auth Routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
          </Route>

          {/* Public Routes */}
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Home />} />
          </Route>

          {/* Protected Routes */}
          <Route path="/app" element={
            <PrivateRoute>
              <MainLayout />
            </PrivateRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="documents" element={<DocumentsList />} />
            <Route path="documents/upload" element={<DocumentUpload />} />
            <Route path="documents/:documentId" element={<DocumentView />} />
            <Route path="conversations" element={<ConversationsList />} />
            <Route path="conversations/:conversationId" element={<Conversation />} />
            <Route path="profile" element={<Profile />} />
            <Route path="search" element={<Search />} />
          </Route>

          {/* Admin Routes */}
          <Route path="/admin" element={
            <RoleGuard requiredRoles={['admin']}>
              <AdminLayout />
            </RoleGuard>
          }>
            <Route index element={<AdminDashboard />} />
            <Route path="users" element={<UserManagement />} />
            <Route path="api-keys" element={<APIKeyManager />} />
            <Route path="settings" element={<SystemSettings />} />
            <Route path="ab-tests" element={<ABTestManager />} />
          </Route>

          {/* Redirects */}
          <Route path="/logout" element={<Navigate to="/login" />} />

          {/* 404 Page */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;