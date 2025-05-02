import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import LoadingSpinner from '../common/LoadingSpinner';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [activeUsers, setActiveUsers] = useState([]);
  const [popularDocs, setPopularDocs] = useState([]);
  const [queryStats, setQueryStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timePeriod, setTimePeriod] = useState('7d');

  useEffect(() => {
    fetchDashboardData();
  }, [timePeriod]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // In a real application, these would be API calls to backend endpoints
      // For this example, we'll simulate the responses
      
      // Simulate API calls with some delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock data
      const statsData = {
        time_period: timePeriod,
        users: {
          active: 42,
          total: 87,
          active_percentage: 48.3
        },
        documents: {
          new: 156,
          total: 2378
        },
        messages: {
          new: 874,
          total: 12456
        },
        feedback: {
          new: 134,
          positive: 112,
          positive_percentage: 83.6
        },
        errors: 8
      };
      
      const activeUsersData = [
        { id: '1', username: 'johndoe', email: 'john@example.com', message_count: 156, last_login: '2025-04-30T15:32:00Z', is_admin: false },
        { id: '2', username: 'janedoe', email: 'jane@example.com', message_count: 124, last_login: '2025-05-01T12:15:00Z', is_admin: true },
        { id: '3', username: 'bobsmith', email: 'bob@example.com', message_count: 98, last_login: '2025-05-02T08:45:00Z', is_admin: false },
        { id: '4', username: 'alicejones', email: 'alice@example.com', message_count: 76, last_login: '2025-05-01T18:22:00Z', is_admin: false },
        { id: '5', username: 'mikebrown', email: 'mike@example.com', message_count: 65, last_login: '2025-04-29T10:05:00Z', is_admin: false }
      ];
      
      const popularDocsData = [
        { document_id: '1', filename: 'annual_report_2024.pdf', title: 'Annual Report 2024', content_type: 'application/pdf', created_at: '2025-01-15T09:30:00Z', usage_count: 87 },
        { document_id: '2', filename: 'product_specs.docx', title: 'Product Specifications', content_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', created_at: '2025-02-22T14:15:00Z', usage_count: 63 },
        { document_id: '3', filename: 'user_manual.pdf', title: 'User Manual v2.1', content_type: 'application/pdf', created_at: '2025-03-10T11:45:00Z', usage_count: 58 },
        { document_id: '4', filename: 'financial_forecast.xlsx', title: 'Financial Forecast Q2 2025', content_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', created_at: '2025-04-05T16:20:00Z', usage_count: 42 },
        { document_id: '5', filename: 'technical_overview.md', title: 'Technical Overview', content_type: 'text/markdown', created_at: '2025-04-18T13:10:00Z', usage_count: 36 }
      ];
      
      const queryStatsData = {
        time_period: timePeriod,
        total_queries: 1458,
        avg_response_time: 1.2,
        common_terms: [
          { term: 'how', count: 120 },
          { term: 'what', count: 95 },
          { term: 'document', count: 78 },
          { term: 'search', count: 65 },
          { term: 'help', count: 50 }
        ]
      };
      
      setStats(statsData);
      setActiveUsers(activeUsersData);
      setPopularDocs(popularDocsData);
      setQueryStats(queryStatsData);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const getFileIcon = (contentType) => {
    if (contentType?.includes('pdf')) {
      return (
        <svg className="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
        </svg>
      );
    } else if (contentType?.includes('word') || contentType?.includes('document')) {
      return (
        <svg className="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
        </svg>
      );
    } else if (contentType?.includes('sheet') || contentType?.includes('excel')) {
      return (
        <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M5 4a1 1 0 00-1 1v10a1 1 0 001 1h10a1 1 0 001-1V5a1 1 0 00-1-1H5zm6 9a1 1 0 11-2 0 1 1 0 012 0zm4-3a1 1 0 00-1-1h-4a1 1 0 000 2h4a1 1 0 001-1zm-5-3a1 1 0 11-2 0 1 1 0 012 0z" clipRule="evenodd" />
        </svg>
      );
    } else if (contentType?.includes('markdown') || contentType?.includes('md')) {
      return (
        <svg className="w-6 h-6 text-purple-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
        </svg>
      );
    } else {
      return (
        <svg className="w-6 h-6 text-gray-500" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
        </svg>
      );
    }
  };

  if (loading && !stats) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Time Period Selector */}
      <div className="bg-white shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Dashboard Overview
            </h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Time period:</span>
              <select
                value={timePeriod}
                onChange={(e) => setTimePeriod(e.target.value)}
                className="block pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="24h">Last 24 hours</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="all">All time</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {/* Users Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-blue-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Active Users
                    </dt>
                    <dd>
                      <div className="text-lg font-medium text-gray-900">
                        {stats.users.active}
                      </div>
                      <div className="text-sm text-gray-500">
                        of {stats.users.total} total ({stats.users.active_percentage}%)
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-5 py-3">
              <div className="text-sm">
                <Link to="/admin/users" className="font-medium text-blue-600 hover:text-blue-500">
                  View all users
                </Link>
              </div>
            </div>
          </div>

          {/* Documents Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-green-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-green-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      New Documents
                    </dt>
                    <dd>
                      <div className="text-lg font-medium text-gray-900">
                        {stats.documents.new}
                      </div>
                      <div className="text-sm text-gray-500">
                        of {stats.documents.total} total
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-5 py-3">
              <div className="text-sm">
                <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                  View documents
                </a>
              </div>
            </div>
          </div>

          {/* Messages Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-purple-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-purple-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      New Messages
                    </dt>
                    <dd>
                      <div className="text-lg font-medium text-gray-900">
                        {stats.messages.new}
                      </div>
                      <div className="text-sm text-gray-500">
                        of {stats.messages.total} total
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-5 py-3">
              <div className="text-sm">
                <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                  View conversations
                </a>
              </div>
            </div>
          </div>

          {/* Feedback Card */}
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-yellow-100 rounded-md p-3">
                  <svg className="h-6 w-6 text-yellow-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905A3.61 3.61 0 018.5 7.5" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Positive Feedback
                    </dt>
                    <dd>
                      <div className="text-lg font-medium text-gray-900">
                        {stats.feedback.positive_percentage}%
                      </div>
                      <div className="text-sm text-gray-500">
                        {stats.feedback.positive} of {stats.feedback.new}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-5 py-3">
              <div className="text-sm">
                <a href="#" className="font-medium text-blue-600 hover:text-blue-500">
                  View all feedback
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Active Users */}
        <div className="bg-white shadow sm:rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Most Active Users
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Based on message count in the selected time period.
            </p>
          </div>
          
          <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
            <div className="sm:divide-y sm:divide-gray-200">
              {activeUsers.map(user => (
                <div key={user.id} className="py-4 sm:py-5 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-blue-600 font-medium text-lg">
                          {user.username.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{user.username}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <div className="text-sm text-gray-500 mr-4">
                        <div>{user.message_count} messages</div>
                        <div>Last seen: {formatDate(user.last_login)}</div>
                      </div>
                      {user.is_admin && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Admin
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-gray-50 px-4 py-4 sm:px-6">
            <Link to="/admin/users" className="text-sm font-medium text-blue-600 hover:text-blue-500">
              View all users
            </Link>
          </div>
        </div>

        {/* Popular Documents */}
        <div className="bg-white shadow sm:rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Popular Documents
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Most accessed documents in the selected time period.
            </p>
          </div>
          
          <div className="border-t border-gray-200 px-4 py-5 sm:p-0">
            <div className="sm:divide-y sm:divide-gray-200">
              {popularDocs.map(doc => (
                <div key={doc.document_id} className="py-4 sm:py-5 sm:px-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10 flex items-center justify-center">
                        {getFileIcon(doc.content_type)}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{doc.title}</div>
                        <div className="text-sm text-gray-500">{doc.filename}</div>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <div className="text-sm text-gray-500 mr-4">
                        <div>{doc.usage_count} uses</div>
                        <div>Added: {formatDate(doc.created_at)}</div>
                      </div>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {doc.content_type.split('/')[1]}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-gray-50 px-4 py-4 sm:px-6">
            <a href="#" className="text-sm font-medium text-blue-600 hover:text-blue-500">
              View all documents
            </a>
          </div>
        </div>
      </div>

      {/* Query Stats */}
      {queryStats && (
        <div className="bg-white shadow sm:rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Query Statistics
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500">
              Overview of user queries and performance.
            </p>
          </div>
          
          <div className="border-t border-gray-200">
            <div className="px-4 py-5 sm:p-6">
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-gray-500">Total Queries</div>
                  <div className="mt-1 text-3xl font-semibold text-gray-900">{queryStats.total_queries}</div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-gray-500">Avg Response Time</div>
                  <div className="mt-1 text-3xl font-semibold text-gray-900">{queryStats.avg_response_time}s</div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="text-sm font-medium text-gray-500">System Errors</div>
                  <div className="mt-1 text-3xl font-semibold text-gray-900">{stats.errors}</div>
                </div>
              </div>
              
              <div className="mt-6">
                <h4 className="text-base font-medium text-gray-900">Common Search Terms</h4>
                <div className="mt-2 flex flex-wrap gap-2">
                  {queryStats.common_terms.map((term, index) => (
                    <div key={index} className="bg-gray-100 px-3 py-1 rounded-full">
                      <span className="text-sm font-medium text-gray-800">{term.term}</span>
                      <span className="ml-1 text-xs text-gray-500">({term.count})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;