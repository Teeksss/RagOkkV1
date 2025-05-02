import React, { useState, useEffect, useContext } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import { getDocuments } from '../api/documents';
import { getConversations } from '../api/conversations';
import LoadingSpinner from '../components/common/LoadingSpinner';

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const [recentDocuments, setRecentDocuments] = useState([]);
  const [recentConversations, setRecentConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch recent documents and conversations in parallel
        const [documentsResult, conversationsResult] = await Promise.all([
          getDocuments({ limit: 5, sort: 'created_at', order: 'desc' }),
          getConversations({ limit: 5 })
        ]);
        
        setRecentDocuments(documentsResult.items || []);
        setRecentConversations(conversationsResult.items || []);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Welcome message */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
          Welcome, {user?.full_name || user?.username || 'User'}!
        </h1>
        <p className="mt-2 text-sm text-gray-600">
          Access your documents, have conversations with AI, and search for information.
        </p>
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Quick actions */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h2 className="text-lg leading-6 font-medium text-gray-900">Quick Actions</h2>
            <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-5">
              <Link
                to="/app/documents/upload"
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
                Upload Document
              </Link>
              <Link
                to="/app/conversations"
                className="inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <svg className="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 5v8a2 2 0 01-2 2h-5l-5 4v-4H4a2 2 0 01-2-2V5a2 2 0 012-2h12a2 2 0 012 2zM7 8H5v2h2V8zm2 0h2v2H9V8zm6 0h-2v2h2V8z" clipRule="evenodd" />
                </svg>
                New Conversation
              </Link>
              <Link
                to="/app/documents"
                className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                </svg>
                View Documents
              </Link>
              <Link
                to="/app/search"
                className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
                </svg>
                Advanced Search
              </Link>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <h2 className="text-lg leading-6 font-medium text-gray-900">Your Activity</h2>
            <div className="mt-5 grid grid-cols-2 gap-5 sm:grid-cols-2">
              <div className="bg-blue-50 overflow-hidden shadow-sm rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-blue-500 truncate">Documents</dt>
                  <dd className="mt-1 text-3xl font-semibold text-blue-800">{recentDocuments.length}</dd>
                </div>
              </div>
              <div className="bg-green-50 overflow-hidden shadow-sm rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-green-500 truncate">Conversations</dt>
                  <dd className="mt-1 text-3xl font-semibold text-green-800">{recentConversations.length}</dd>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Documents */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-5 py-5">
            <div className="flex justify-between items-center">
              <h2 className="text-lg leading-6 font-medium text-gray-900">Recent Documents</h2>
              <Link to="/app/documents" className="text-sm font-medium text-blue-600 hover:text-blue-500">
                View all
              </Link>
            </div>
          </div>
          <div className="border-t border-gray-200">
            {recentDocuments.length === 0 ? (
              <div className="px-5 py-5 text-center text-sm text-gray-500">
                <p>No documents uploaded yet.</p>
                <Link to="/app/documents/upload" className="mt-2 inline-flex items-center text-blue-600 hover:text-blue-500">
                  Upload your first document
                  <svg className="ml-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </Link>
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {recentDocuments.map((document) => (
                  <li key={document.id}>
                    <Link to={`/app/documents/${document.id}`} className="block hover:bg-gray-50">
                      <div className="px-5 py-4">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 text-blue-500">
                            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3 flex-1">
                            <p className="text-sm font-medium text-gray-900 truncate">{document.filename}</p>
                            <p className="text-xs text-gray-500">
                              {formatDate(document.created_at)}
                            </p>
                          </div>
                        </div>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Recent Conversations */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-5 py-5">
            <div className="flex justify-between items-center">
              <h2 className="text-lg leading-6 font-medium text-gray-900">Recent Conversations</h2>
              <Link to="/app/conversations" className="text-sm font-medium text-blue-600 hover:text-blue-500">
                View all
              </Link>
            </div>
          </div>
          <div className="border-t border-gray-200">
            {recentConversations.length === 0 ? (
              <div className="px-5 py-5 text-center text-sm text-gray-500">
                <p>No conversations started yet.</p>
                <Link to="/app/conversations" className="mt-2 inline-flex items-center text-blue-600 hover:text-blue-500">
                  Start a new conversation
                  <svg className="ml-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10.293 5.293a1 1 0 011.414 0l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414-1.414L12.586 11H5a1 1 0 110-2h7.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </Link>
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {recentConversations.map((conversation) => (
                  <li key={conversation.id}>
                    <Link to={`/app/conversations/${conversation.id}`} className="block hover:bg-gray-50">
                      <div className="px-5 py-4">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 text-green-500">
                            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
                            </svg>
                          </div>
                          <div className="ml-3 flex-1">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {conversation.title || 'Untitled Conversation'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {formatDate(conversation.last_message_at || conversation.created_at)}
                            </p>
                          </div>
                          <div className="ml-2 flex-shrink-0">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              {conversation.message_count || 0} messages
                            </span>
                          </div>
                        </div>
                      </div>
                    </Link>
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

export default Dashboard;