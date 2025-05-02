import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getUsers } from '../../api/users';
import { getDocuments } from '../../api/documents';
import { getSystemStats } from '../../api/admin';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import { formatNumber, formatDate } from '../../utils/formatting';

const AdminDashboard = () => {
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    totalDocuments: 0,
    totalConversations: 0,
    apiRequests: {
      total: 0,
      today: 0
    },
    systemLoad: {
      cpu: 0,
      memory: 0,
      disk: 0
    }
  });
  
  const [recentUsers, setRecentUsers] = useState([]);
  const [recentDocuments, setRecentDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch system stats and recent data in parallel
        const [systemStats, usersResult, documentsResult] = await Promise.all([
          getSystemStats(),
          getUsers({ limit: 5, sort: 'created_at', order: 'desc' }),
          getDocuments({ limit: 5, sort: 'created_at', order: 'desc' })
        ]);
        
        setStats(systemStats);
        setRecentUsers(usersResult.items || []);
        setRecentDocuments(documentsResult.items || []);
      } catch (err) {
        console.error('Error fetching admin dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Admin Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">
            System overview and statistics
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-8 bg-red-50 border-l-4 border-red-400 p-4">
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
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-blue-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Users</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">{formatNumber(stats.totalUsers)}</div>
                    <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                      <span>Active: {formatNumber(stats.activeUsers)}</span>
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-green-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Documents</dt>
                  <dd className="text-2xl font-semibold text-gray-900">{formatNumber(stats.totalDocuments)}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-purple-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Conversations</dt>
                  <dd className="text-2xl font-semibold text-gray-900">{formatNumber(stats.totalConversations)}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-yellow-500 rounded-md p-3">
                <svg className="h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">API Requests</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">{formatNumber(stats.apiRequests.total)}</div>
                    <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                      <span>Today: {formatNumber(stats.apiRequests.today)}</span>
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Monitor */}
      <div className="bg-white shadow sm:rounded-lg mb-8">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg leading-6 font-medium text-gray-900">System Load</h2>
          <div className="mt-5 grid grid-cols-1 gap-5 sm:grid-cols-3">
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-700">CPU Usage</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  stats.systemLoad.cpu > 80 ? 'bg-red-100 text-red-800' : 
                  stats.systemLoad.cpu > 50 ? 'bg-yellow-100 text-yellow-800' : 
                  'bg-green-100 text-green-800'
                }`}>
                  {stats.systemLoad.cpu}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    stats.systemLoad.cpu > 80 ? 'bg-red-500' : 
                    stats.systemLoad.cpu > 50 ? 'bg-yellow-500' : 
                    'bg-green-500'
                  }`} 
                  style={{ width: `${stats.systemLoad.cpu}%` }}
                ></div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-700">Memory Usage</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  stats.systemLoad.memory > 80 ? 'bg-red-100 text-red-800' : 
                  stats.systemLoad.memory > 50 ? 'bg-yellow-100 text-yellow-800' : 
                  'bg-green-100 text-green-800'
                }`}>
                  {stats.systemLoad.memory}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    stats.systemLoad.memory > 80 ? 'bg-red-500' : 
                    stats.systemLoad.memory > 50 ? 'bg-yellow-500' : 
                    'bg-green-500'
                  }`} 
                  style={{ width: `${stats.systemLoad.memory}%` }}
                ></div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-700">Disk Usage</h3>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  stats.systemLoad.disk > 80 ? 'bg-red-100 text-red-800' : 
                  stats.systemLoad.disk > 50 ? 'bg-yellow-100 text-yellow-800' : 
                  'bg-green-100 text-green-800'
                }`}>
                  {stats.systemLoad.disk}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    stats.systemLoad.disk > 80 ? 'bg-red-500' : 
                    stats.systemLoad.disk > 50 ? 'bg-yellow-500' : 
                    'bg-green-500'
                  }`} 
                  style={{ width: `${stats.systemLoad.disk}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Users */}
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
            <h2 className="text-lg leading-6 font-medium text-gray-900">Recent Users</h2>
            <Link to="/admin/users" className="text-sm font-medium text-blue-600 hover:text-blue-500">
              View all
            </Link>
          </div>
          <div className="border-t border-gray-200">
            {recentUsers.length === 0 ? (
              <div className="px-4 py-5 text-center text-sm text-gray-500">
                No users found
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {recentUsers.map((user) => (
                  <li key={user.id}>
                    <div className="px-4 py-4 flex items-center">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {user.full_name || user.username}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          {user.email}
                        </p>
                      </div>
                      <div className="ml-4 flex-shrink-0 flex">
                        <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          Joined {formatDate(user.created_at, { includeTime: false })}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Recent Documents */}
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
            <h2 className="text-lg leading-6 font-medium text-gray-900">Recent Documents</h2>
            <Link to="/app/documents" className="text-sm font-medium text-blue-600 hover:text-blue-500">
              View all
            </Link>
          </div>
          <div className="border-t border-gray-200">
            {recentDocuments.length === 0 ? (
              <div className="px-4 py-5 text-center text-sm text-gray-500">
                No documents found
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {recentDocuments.map((document) => (
                  <li key={document.id}>
                    <div className="px-4 py-4 flex items-center">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {document.filename}
                        </p>
                        <p className="text-sm text-gray-500 truncate">
                          Uploaded by: {document.user_name || 'Unknown user'}
                        </p>
                      </div>
                      <div className="ml-4 flex-shrink-0 flex">
                        <p className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                          {document.processing_status}
                        </p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;