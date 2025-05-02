import React from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';

const AuthLayout = () => {
  const { isAuthenticated, loading } = useContext(AuthContext);
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="fixed top-0 left-0 w-full h-full flex items-center justify-center bg-gray-100">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  // Redirect to app if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/app" state={{ from: location }} replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold text-blue-600">RAG System</h2>
          <p className="mt-2 text-sm text-gray-600">
            Document Search & Chat with AI
          </p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;