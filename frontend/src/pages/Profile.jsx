import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts/AuthContext';
import { updateProfile, changePassword } from '../api/users';
import { validatePassword } from '../utils/auth';
import LoadingSpinner from '../components/common/LoadingSpinner';

const Profile = () => {
  const { user, refreshUser } = useContext(AuthContext);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');
  
  // Profile form state
  const [profile, setProfile] = useState({
    username: '',
    email: '',
    full_name: ''
  });
  
  // Password form state
  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  
  // Validation errors
  const [validationErrors, setValidationErrors] = useState({});

  // Initialize profile form with user data
  useEffect(() => {
    if (user) {
      setProfile({
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || ''
      });
    }
  }, [user]);

  // Handle profile form changes
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfile({
      ...profile,
      [name]: value
    });
    
    // Clear errors
    setError(null);
    setSuccess(null);
  };

  // Handle password form changes
  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswords({
      ...passwords,
      [name]: value
    });
    
    // Validate new password
    if (name === 'new_password' && value) {
      const validation = validatePassword(value);
      if (!validation.valid) {
        setValidationErrors({
          ...validationErrors,
          new_password: validation.message
        });
      } else {
        const updatedErrors = { ...validationErrors };
        delete updatedErrors.new_password;
        setValidationErrors(updatedErrors);
      }
    }
    
    // Validate password confirmation
    if (name === 'confirm_password' && value && passwords.new_password && value !== passwords.new_password) {
      setValidationErrors({
        ...validationErrors,
        confirm_password: 'Passwords do not match'
      });
    } else if (name === 'confirm_password') {
      const updatedErrors = { ...validationErrors };
      delete updatedErrors.confirm_password;
      setValidationErrors(updatedErrors);
    }
    
    // Clear general errors
    setError(null);
    setSuccess(null);
  };

  // Submit profile update
  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await updateProfile(profile);
      
      // Refresh user data
      await refreshUser();
      
      setSuccess('Profile updated successfully');
    } catch (err) {
      console.error('Error updating profile:', err);
      setError(err.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  // Submit password change
  const handlePasswordUpdate = async (e) => {
    e.preventDefault();
    
    // Validation
    if (!passwords.current_password) {
      setError('Current password is required');
      return;
    }
    
    if (!passwords.new_password) {
      setError('New password is required');
      return;
    }
    
    const validation = validatePassword(passwords.new_password);
    if (!validation.valid) {
      setError(validation.message);
      return;
    }
    
    if (passwords.new_password !== passwords.confirm_password) {
      setError('Passwords do not match');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await changePassword({
        current_password: passwords.current_password,
        new_password: passwords.new_password
      });
      
      // Clear form
      setPasswords({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      
      setSuccess('Password changed successfully');
    } catch (err) {
      console.error('Error changing password:', err);
      setError(err.message || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Profile</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your account settings
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-8">
        <div className="sm:hidden">
          <label htmlFor="tabs" className="sr-only">Select a tab</label>
          <select
            id="tabs"
            name="tabs"
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={activeTab}
            onChange={(e) => setActiveTab(e.target.value)}
          >
            <option value="profile">Profile</option>
            <option value="password">Password</option>
          </select>
        </div>
        <div className="hidden sm:block">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('profile')}
                className={`${
                  activeTab === 'profile'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Profile
              </button>
              <button
                onClick={() => setActiveTab('password')}
                className={`${
                  activeTab === 'password'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
              >
                Password
              </button>
            </nav>
          </div>
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
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

      {success && (
        <div className="mb-4 bg-green-50 border-l-4 border-green-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-green-700">{success}</p>
            </div>
          </div>
        </div>
      )}

      {/* Profile Form */}
      {activeTab === 'profile' && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <form onSubmit={handleProfileUpdate}>
              <div className="grid grid-cols-6 gap-6">
                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                    Username
                  </label>
                  <input
                    type="text"
                    name="username"
                    id="username"
                    value={profile.username}
                    onChange={handleProfileChange}
                    className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    disabled
                  />
                  <p className="mt-1 text-xs text-gray-500">Username cannot be changed.</p>
                </div>

                <div className="col-span-6 sm:col-span-3">
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Email address
                  </label>
                  <input
                    type="email"
                    name="email"
                    id="email"
                    value={profile.email}
                    onChange={handleProfileChange}
                    className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  />
                </div>

                <div className="col-span-6">
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                    Full name
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    id="full_name"
                    value={profile.full_name}
                    onChange={handleProfileChange}
                    className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                  />
                </div>
              </div>
              
              <div className="mt-6">
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <LoadingSpinner size="small" color="white" className="mr-2" />
                      Saving...
                    </>
                  ) : 'Save changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Password Form */}
      {activeTab === 'password' && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <form onSubmit={handlePasswordUpdate}>
              <div className="space-y-6">
                <div>
                  <label htmlFor="current_password" className="block text-sm font-medium text-gray-700">
                    Current password
                  </label>
                  <input
                    type="password"
                    name="current_password"
                    id="current_password"
                    value={passwords.current_password}
                    onChange={handlePasswordChange}
                    className="mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md"
                    required
                  />
                </div>

                <div>
                  <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">
                    New password
                  </label>
                  <input
                    type="password"
                    name="new_password"
                    id="new_password"
                    value={passwords.new_password}
                    onChange={handlePasswordChange}
                    className={`mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md ${
                      validationErrors.new_password ? 'border-red-300' : ''
                    }`}
                    required
                  />
                  {validationErrors.new_password && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.new_password}</p>
                  )}
                  <div className="mt-2 text-sm text-gray-500">
                    <p>Password must contain at least:</p>
                    <ul className="list-disc pl-5 mt-1">
                      <li>8 characters</li>
                      <li>One uppercase letter</li>
                      <li>One lowercase letter</li>
                      <li>One number</li>
                      <li>One special character</li>
                    </ul>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700">
                    Confirm new password
                  </label>
                  <input
                    type="password"
                    name="confirm_password"
                    id="confirm_password"
                    value={passwords.confirm_password}
                    onChange={handlePasswordChange}
                    className={`mt-1 focus:ring-blue-500 focus:border-blue-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md ${
                      validationErrors.confirm_password ? 'border-red-300' : ''
                    }`}
                    required
                  />
                  {validationErrors.confirm_password && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.confirm_password}</p>
                  )}
                </div>
              </div>
              
              <div className="mt-6">
                <button
                  type="submit"
                  disabled={loading || Object.keys(validationErrors).length > 0}
                  className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <LoadingSpinner size="small" color="white" className="mr-2" />
                      Updating...
                    </>
                  ) : 'Change password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Profile;