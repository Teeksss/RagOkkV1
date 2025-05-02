import React, { useState, useEffect } from 'react';
import { getApiKeys, createApiKey, revokeApiKey } from '../../api/api-keys';
import LoadingSpinner from '../common/LoadingSpinner';

const APIKeyManager = () => {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [newKeyData, setNewKeyData] = useState({
    name: '',
    expires_in_days: 30,
    scopes: ['read']
  });
  const [createdKey, setCreatedKey] = useState(null);
  const [revokeConfirmation, setRevokeConfirmation] = useState(null);

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      setLoading(true);
      setError(null);
      const keys = await getApiKeys();
      setApiKeys(keys);
    } catch (err) {
      console.error('Error loading API keys:', err);
      setError('Failed to load API keys. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleScopeChange = (scope) => {
    if (newKeyData.scopes.includes(scope)) {
      setNewKeyData({
        ...newKeyData,
        scopes: newKeyData.scopes.filter(s => s !== scope)
      });
    } else {
      setNewKeyData({
        ...newKeyData,
        scopes: [...newKeyData.scopes, scope]
      });
    }
  };

  const handleCreateKey = async (e) => {
    e.preventDefault();
    
    if (!newKeyData.name.trim()) {
      setError('API key name is required');
      return;
    }
    
    if (newKeyData.scopes.length === 0) {
      setError('At least one scope must be selected');
      return;
    }
    
    try {
      setCreating(true);
      setError(null);
      
      const result = await createApiKey(newKeyData);
      
      setSuccess('API key created successfully');
      setCreatedKey(result);
      loadApiKeys();
      
      // Reset form
      setNewKeyData({
        name: '',
        expires_in_days: 30,
        scopes: ['read']
      });
    } catch (err) {
      console.error('Error creating API key:', err);
      setError('Failed to create API key. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const handleRevokeConfirmation = (key) => {
    setRevokeConfirmation(key);
  };

  const handleRevokeCancel = () => {
    setRevokeConfirmation(null);
  };

  const handleRevokeKey = async () => {
    try {
      setLoading(true);
      await revokeApiKey(revokeConfirmation.id);
      
      setSuccess('API key revoked successfully');
      loadApiKeys();
      setRevokeConfirmation(null);
    } catch (err) {
      console.error('Error revoking API key:', err);
      setError('Failed to revoke API key. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never expires';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium leading-6 text-gray-900">API Keys</h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>Create and manage API keys for programmatic access to the system.</p>
          </div>
          
          {error && (
            <div className="mt-4 bg-red-50 border-l-4 border-red-400 p-4">
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
          
          {success && (
            <div className="mt-4 bg-green-50 border-l-4 border-green-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-green-700">{success}</p>
                </div>
              </div>
            </div>
          )}

          {/* Created Key Display */}
          {createdKey && (
            <div className="mt-4 p-4 border border-yellow-300 bg-yellow-50 rounded-md">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="text-sm font-medium text-yellow-800">Your new API key has been created</h4>
                  <p className="mt-1 text-xs text-yellow-700">
                    Make sure to copy your API key now. You won't be able to see it again!
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setCreatedKey(null)}
                  className="text-yellow-600 hover:text-yellow-800"
                >
                  <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              <div className="mt-3">
                <div className="bg-white p-2 rounded border border-yellow-300 flex items-center justify-between break-all">
                  <code className="text-xs text-gray-800 flex-1">{createdKey.token}</code>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(createdKey.token);
                      setSuccess('API key copied to clipboard');
                    }}
                    className="ml-2 p-1 text-yellow-600 hover:text-yellow-900"
                  >
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                      <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z" />
                      <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Create New Key Form */}
          <div className="mt-5 border-t border-gray-200 pt-5">
            <h4 className="text-sm font-medium text-gray-900">Create a new API key</h4>
            <form className="mt-3 space-y-4" onSubmit={handleCreateKey}>
              <div>
                <label htmlFor="key-name" className="block text-sm font-medium text-gray-700">
                  Key Name
                </label>
                <input
                  type="text"
                  name="key-name"
                  id="key-name"
                  value={newKeyData.name}
                  onChange={(e) => setNewKeyData({ ...newKeyData, name: e.target.value })}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="My API Key"
                />
              </div>
              
              <div>
                <label htmlFor="expiration" className="block text-sm font-medium text-gray-700">
                  Expiration
                </label>
                <select
                  id="expiration"
                  name="expiration"
                  value={newKeyData.expires_in_days}
                  onChange={(e) => setNewKeyData({ ...newKeyData, expires_in_days: parseInt(e.target.value) })}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                >
                  <option value={7}>7 days</option>
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={365}>1 year</option>
                  <option value={0}>Never expires</option>
                </select>
              </div>
              
              <div>
                <span className="block text-sm font-medium text-gray-700">
                  Permissions
                </span>
                <div className="mt-2 space-y-2">
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="scope-read"
                        name="scope-read"
                        type="checkbox"
                        checked={newKeyData.scopes.includes('read')}
                        onChange={() => handleScopeChange('read')}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="scope-read" className="font-medium text-gray-700">Read</label>
                      <p className="text-gray-500">View documents and conversations</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="scope-write"
                        name="scope-write"
                        type="checkbox"
                        checked={newKeyData.scopes.includes('write')}
                        onChange={() => handleScopeChange('write')}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="scope-write" className="font-medium text-gray-700">Write</label>
                      <p className="text-gray-500">Create documents and conversations</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        id="scope-admin"
                        name="scope-admin"
                        type="checkbox"
                        checked={newKeyData.scopes.includes('admin')}
                        onChange={() => handleScopeChange('admin')}
                        className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="scope-admin" className="font-medium text-gray-700">Admin</label>
                      <p className="text-gray-500">Full system access (use with caution)</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <button
                  type="submit"
                  disabled={creating}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {creating ? <LoadingSpinner size="small" color="white" className="mr-2" /> : null}
                  Create API Key
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>

      {/* API Keys List */}
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium leading-6 text-gray-900">Your API Keys</h3>
          
          {loading && apiKeys.length === 0 ? (
            <div className="flex justify-center items-center h-24">
              <LoadingSpinner size="large" />
            </div>
          ) : apiKeys.length === 0 ? (
            <div className="mt-4 text-center py-8 border-2 border-dashed border-gray-200 rounded-md">
              <svg className="mx-auto h-12 w-12 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              <p className="mt-2 text-sm text-gray-500">No API keys found</p>
              <p className="text-xs text-gray-400">Create your first API key to get started</p>
            </div>
          ) : (
            <div className="mt-4 overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">Name</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Prefix</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Permissions</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Expires</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Last Used</th>
                    <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {apiKeys.map((key) => (
                    <tr key={key.id}>
                      <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">{key.name}</td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{key.prefix}...</td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                        <div className="flex space-x-2">
                          {key.scopes.map((scope) => (
                            <span key={scope} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {scope}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{formatDate(key.expires_at)}</td>
                      <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">{key.last_used_at ? formatDate(key.last_used_at) : 'Never'}</td>
                      <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                        <button
                          onClick={() => handleRevokeConfirmation(key)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Revoke
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Revoke Confirmation Modal */}
      {revokeConfirmation && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
                  <svg className="h-6 w-6 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div className="mt-3 text-center sm:mt-5">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Revoke API Key
                  </h3>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">
                      Are you sure you want to revoke the API key <strong>"{revokeConfirmation.name}"</strong>? This action cannot be undone.
                    </p>
                  </div>
                </div>
              </div>
              <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                <button
                  type="button"
                  onClick={handleRevokeKey}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:col-start-2 sm:text-sm"
                >
                  Revoke
                </button>
                <button
                  type="button"
                  onClick={handleRevokeCancel}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default APIKeyManager;