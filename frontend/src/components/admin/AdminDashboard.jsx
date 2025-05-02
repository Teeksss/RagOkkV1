import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { fetchDashboardStats, fetchActiveUsers, fetchPopularDocuments, fetchQueryStats, fetchErrorLogs, fetchRecentFeedbacks } from '../../api/admin';
import UserList from './UserList';
import DocumentList from './DocumentList';
import StatCard from './StatCard';
import ErrorLogs from './ErrorLogs';
import FeedbackList from './FeedbackList';
import RoleGuard from '../common/RoleGuard';

const AdminDashboard = () => {
  const [timePeriod, setTimePeriod] = useState('7d');
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [activeUsers, setActiveUsers] = useState([]);
  const [popularDocuments, setPopularDocuments] = useState([]);
  const [queryStats, setQueryStats] = useState(null);
  const [errorLogs, setErrorLogs] = useState([]);
  const [recentFeedbacks, setRecentFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const dashboardStats = await fetchDashboardStats(timePeriod);
        setStats(dashboardStats);

        if (activeTab === 'overview' || activeTab === 'users') {
          const users = await fetchActiveUsers(timePeriod);
          setActiveUsers(users);
        }

        if (activeTab === 'overview' || activeTab === 'documents') {
          const documents = await fetchPopularDocuments(timePeriod);
          setPopularDocuments(documents);
        }

        if (activeTab === 'overview' || activeTab === 'queries') {
          const queries = await fetchQueryStats(timePeriod);
          setQueryStats(queries);
        }

        if (activeTab === 'errors') {
          const logs = await fetchErrorLogs(timePeriod);
          setErrorLogs(logs);
        }

        if (activeTab === 'feedback') {
          const feedbacks = await fetchRecentFeedbacks();
          setRecentFeedbacks(feedbacks);
        }
      } catch (error) {
        console.error("Error loading dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [timePeriod, activeTab]);

  const renderTimePeriodSelector = () => (
    <div className="flex justify-end mb-4">
      <div className="inline-flex rounded-md shadow-sm" role="group">
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium ${timePeriod === '24h' 
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-50'}`}
          onClick={() => setTimePeriod('24h')}
        >
          24 Hours
        </button>
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium ${timePeriod === '7d' 
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-50'}`}
          onClick={() => setTimePeriod('7d')}
        >
          7 Days
        </button>
        <button
          type="button"
          className={`px-4 py-2 text-sm font-medium ${timePeriod === '30d' 
            ? 'bg-blue-600 text-white'
            : 'bg-white text-gray-700 hover:bg-gray-50'}`}
          onClick={() => setTimePeriod('30d')}
        >
          30 Days
        </button>
      </div>
    </div>
  );

  const renderTabs = () => (
    <div className="border-b border-gray-200 mb-6">
      <nav className="-mb-px flex space-x-8">
        <button
          className={`${activeTab === 'overview'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          className={`${activeTab === 'users'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
        <button
          className={`${activeTab === 'documents'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          onClick={() => setActiveTab('documents')}
        >
          Documents
        </button>
        <button
          className={`${activeTab === 'queries'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          onClick={() => setActiveTab('queries')}
        >
          Queries
        </button>
        <button
          className={`${activeTab === 'errors'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          onClick={() => setActiveTab('errors')}
        >
          Errors
        </button>
        <button
          className={`${activeTab === 'feedback'
            ? 'border-blue-500 text-blue-600'
            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          onClick={() => setActiveTab('feedback')}
        >
          Feedback
        </button>
      </nav>
    </div>
  );

  const renderOverview = () => {
    if (!stats) return null;

    return (
      <div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Active Users"
            value={stats.users.active}
            total={stats.users.total}
            icon="users"
            color="blue"
          />
          <StatCard
            title="Documents"
            value={stats.documents.new}
            total={stats.documents.total}
            icon="document"
            color="green"
          />
          <StatCard
            title="Conversations"
            value={stats.conversations.new}
            total={stats.conversations.total}
            icon="chat"
            color="purple"
          />
          <StatCard
            title="Errors"
            value={stats.errors.count}
            total={null}
            icon="exclamation"
            color="red"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Query Activity</h3>
            {queryStats && (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={queryStats.time_series}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="query_count"
                    stroke="#3B82F6"
                    name="Queries"
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Feedback Summary</h3>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center">
                <p className="text-sm text-gray-500">Thumbs Up</p>
                <p className="text-2xl font-bold text-green-600">{stats.feedback.thumbs_up}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">Thumbs Down</p>
                <p className="text-2xl font-bold text-red-600">{stats.feedback.thumbs_down}</p>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Thumbs Up', value: stats.feedback.thumbs_up || 0, fill: '#10B981' },
                    { name: 'Thumbs Down', value: stats.feedback.thumbs_down || 0, fill: '#EF4444' },
                  ]}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  dataKey="value"
                />
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Most Active Users</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      User
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Messages
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {activeUsers.slice(0, 5).map((user) => (
                    <tr key={user.user_id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{user.username}</div>
                        <div className="text-sm text-gray-500">{user.email}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {user.message_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Popular Documents</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Document
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Usage
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {popularDocuments.slice(0, 5).map((doc) => (
                    <tr key={doc.document_id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{doc.title}</div>
                        <div className="text-sm text-gray-500">{doc.filename}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {doc.usage_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'users':
        return <UserList users={activeUsers} />;
      case 'documents':
        return <DocumentList documents={popularDocuments} />;
      case 'queries':
        return (
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Query Statistics</h3>
            {queryStats && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Total Queries</p>
                    <p className="text-2xl font-bold">{queryStats.total_queries}</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Avg Response Time</p>
                    <p className="text-2xl font-bold">{queryStats.avg_response_time}s</p>
                  </div>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-500">Time Period</p>
                    <p className="text-2xl font-bold">{timePeriod}</p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={queryStats.time_series}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="query_count" fill="#3B82F6" name="Query Count" />
                  </BarChart>
                </ResponsiveContainer>
              </>
            )}
          </div>
        );
      case 'errors':
        return <ErrorLogs errors={errorLogs} />;
      case 'feedback':
        return <FeedbackList feedbacks={recentFeedbacks} />;
      default:
        return renderOverview();
    }
  };

  return (
    <RoleGuard requiredRoles={['admin']}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          {renderTimePeriodSelector()}
        </div>

        {renderTabs()}
        {renderContent()}
      </div>
    </RoleGuard>
  );
};

export default AdminDashboard;