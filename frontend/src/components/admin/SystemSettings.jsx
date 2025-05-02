import React, { useState, useEffect } from 'react';
import LoadingSpinner from '../common/LoadingSpinner';

const SystemSettings = () => {
  const [settings, setSettings] = useState({
    general: {
      siteName: 'RAG System',
      siteDescription: 'Retrieval-Augmented Generation System',
      defaultLanguage: 'en',
      maintenanceMode: false
    },
    authentication: {
      allowRegistration: true,
      requireEmailVerification: true,
      passwordMinLength: 8,
      passwordRequireSpecialChar: true,
      passwordRequireNumber: true,
      passwordRequireUppercase: true,
      sessionTimeoutMinutes: 30,
      maxLoginAttempts: 5,
      lockoutDurationMinutes: 15
    },
    documents: {
      maxFileSizeMB: 10,
      allowedExtensions: 'pdf,docx,txt,md,json,csv,xlsx,pptx,html,png,jpg,jpeg',
      defaultChunkSize: 1000,
      defaultChunkOverlap: 100,
      extractImages: true,
      ocrEnabled: true
    },
    search: {
      defaultModel: 'text-embedding-ada-002',
      vectorDimension: 384,
      resultLimit: 5,
      reranking: true,
      inclusiveSearch: false
    },
    llm: {
      provider: 'openai',
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      contextWindow: 8192,
      streamResponse: true,
      useHistory: true,
      historyTruncation: 10
    },
    cache: {
      enabled: true,
      ttlSeconds: 3600,
      maxSize: 1000
    },
    logging: {
      level: 'INFO',
      detailedErrors: false,
      logUserQueries: true,
      logResponses: true,
      retentionDays: 30
    }
  });
  
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('general');

  // In a real application, you'd fetch settings from API
  useEffect(() => {
    // Simulating API call
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const handleChange = (category, setting, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: value
      }
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    setSuccess(false);
    setError(null);
    
    try {
      // In a real application, you'd make an API call here
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Simulate success
      setSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(false);
      }, 3000);
    } catch (err) {
      setError('Failed to save settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'general', label: 'General' },
    { id: 'authentication', label: 'Authentication' },
    { id: 'documents', label: 'Documents' },
    { id: 'search', label: 'Search' },
    { id: 'llm', label: 'LLM' },
    { id: 'cache', label: 'Cache' },
    { id: 'logging', label: 'Logging' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="siteName" className="block text-sm font-medium text-gray-700">
                Site Name
              </label>
              <input
                type="text"
                id="siteName"
                value={settings.general.siteName}
                onChange={(e) => handleChange('general', 'siteName', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="siteDescription" className="block text-sm font-medium text-gray-700">
                Site Description
              </label>
              <input
                type="text"
                id="siteDescription"
                value={settings.general.siteDescription}
                onChange={(e) => handleChange('general', 'siteDescription', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="defaultLanguage" className="block text-sm font-medium text-gray-700">
                Default Language
              </label>
              <select
                id="defaultLanguage"
                value={settings.general.defaultLanguage}
                onChange={(e) => handleChange('general', 'defaultLanguage', e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="ja">Japanese</option>
                <option value="zh">Chinese</option>
                <option value="tr">Turkish</option>
              </select>
            </div>
            
            <div className="flex items-center">
              <input
                id="maintenanceMode"
                type="checkbox"
                checked={settings.general.maintenanceMode}
                onChange={(e) => handleChange('general', 'maintenanceMode', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="maintenanceMode" className="ml-2 block text-sm text-gray-900">
                Maintenance Mode
              </label>
            </div>
          </div>
        );
      
      case 'authentication':
        return (
          <div className="space-y-6">
            <div className="flex items-center">
              <input
                id="allowRegistration"
                type="checkbox"
                checked={settings.authentication.allowRegistration}
                onChange={(e) => handleChange('authentication', 'allowRegistration', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="allowRegistration" className="ml-2 block text-sm text-gray-900">
                Allow Public Registration
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="requireEmailVerification"
                type="checkbox"
                checked={settings.authentication.requireEmailVerification}
                onChange={(e) => handleChange('authentication', 'requireEmailVerification', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="requireEmailVerification" className="ml-2 block text-sm text-gray-900">
                Require Email Verification
              </label>
            </div>
            
            <div>
              <label htmlFor="passwordMinLength" className="block text-sm font-medium text-gray-700">
                Minimum Password Length
              </label>
              <input
                type="number"
                id="passwordMinLength"
                min="6"
                max="64"
                value={settings.authentication.passwordMinLength}
                onChange={(e) => handleChange('authentication', 'passwordMinLength', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div className="flex items-center">
              <input
                id="passwordRequireSpecialChar"
                type="checkbox"
                checked={settings.authentication.passwordRequireSpecialChar}
                onChange={(e) => handleChange('authentication', 'passwordRequireSpecialChar', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="passwordRequireSpecialChar" className="ml-2 block text-sm text-gray-900">
                Require Special Character
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="passwordRequireNumber"
                type="checkbox"
                checked={settings.authentication.passwordRequireNumber}
                onChange={(e) => handleChange('authentication', 'passwordRequireNumber', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="passwordRequireNumber" className="ml-2 block text-sm text-gray-900">
                Require Number
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="passwordRequireUppercase"
                type="checkbox"
                checked={settings.authentication.passwordRequireUppercase}
                onChange={(e) => handleChange('authentication', 'passwordRequireUppercase', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="passwordRequireUppercase" className="ml-2 block text-sm text-gray-900">
                Require Uppercase Character
              </label>
            </div>
            
            <div>
              <label htmlFor="sessionTimeoutMinutes" className="block text-sm font-medium text-gray-700">
                Session Timeout (minutes)
              </label>
              <input
                type="number"
                id="sessionTimeoutMinutes"
                min="5"
                max="1440"
                value={settings.authentication.sessionTimeoutMinutes}
                onChange={(e) => handleChange('authentication', 'sessionTimeoutMinutes', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="maxLoginAttempts" className="block text-sm font-medium text-gray-700">
                Max Login Attempts
              </label>
              <input
                type="number"
                id="maxLoginAttempts"
                min="1"
                max="10"
                value={settings.authentication.maxLoginAttempts}
                onChange={(e) => handleChange('authentication', 'maxLoginAttempts', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="lockoutDurationMinutes" className="block text-sm font-medium text-gray-700">
                Account Lockout Duration (minutes)
              </label>
              <input
                type="number"
                id="lockoutDurationMinutes"
                min="1"
                max="1440"
                value={settings.authentication.lockoutDurationMinutes}
                onChange={(e) => handleChange('authentication', 'lockoutDurationMinutes', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
        );
      
      case 'documents':
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="maxFileSizeMB" className="block text-sm font-medium text-gray-700">
                Maximum File Size (MB)
              </label>
              <input
                type="number"
                id="maxFileSizeMB"
                min="1"
                max="100"
                value={settings.documents.maxFileSizeMB}
                onChange={(e) => handleChange('documents', 'maxFileSizeMB', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="allowedExtensions" className="block text-sm font-medium text-gray-700">
                Allowed File Extensions (comma-separated)
              </label>
              <input
                type="text"
                id="allowedExtensions"
                value={settings.documents.allowedExtensions}
                onChange={(e) => handleChange('documents', 'allowedExtensions', e.target.value)}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="defaultChunkSize" className="block text-sm font-medium text-gray-700">
                Default Chunk Size (characters)
              </label>
              <input
                type="number"
                id="defaultChunkSize"
                min="100"
                max="5000"
                value={settings.documents.defaultChunkSize}
                onChange={(e) => handleChange('documents', 'defaultChunkSize', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="defaultChunkOverlap" className="block text-sm font-medium text-gray-700">
                Default Chunk Overlap (characters)
              </label>
              <input
                type="number"
                id="defaultChunkOverlap"
                min="0"
                max="1000"
                value={settings.documents.defaultChunkOverlap}
                onChange={(e) => handleChange('documents', 'defaultChunkOverlap', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div className="flex items-center">
              <input
                id="extractImages"
                type="checkbox"
                checked={settings.documents.extractImages}
                onChange={(e) => handleChange('documents', 'extractImages', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="extractImages" className="ml-2 block text-sm text-gray-900">
                Extract Images from Documents
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="ocrEnabled"
                type="checkbox"
                checked={settings.documents.ocrEnabled}
                onChange={(e) => handleChange('documents', 'ocrEnabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="ocrEnabled" className="ml-2 block text-sm text-gray-900">
                Enable OCR for Images
              </label>
            </div>
          </div>
        );
      
      case 'search':
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="defaultModel" className="block text-sm font-medium text-gray-700">
                Default Embedding Model
              </label>
              <select
                id="defaultModel"
                value={settings.search.defaultModel}
                onChange={(e) => handleChange('search', 'defaultModel', e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="text-embedding-ada-002">OpenAI - text-embedding-ada-002</option>
                <option value="bge-large-en">BGE Large English</option>
                <option value="instructor-xl">Instructor XL</option>
                <option value="mpnet-base-v2">MPNET Base v2</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="vectorDimension" className="block text-sm font-medium text-gray-700">
                Vector Dimension
              </label>
              <input
                type="number"
                id="vectorDimension"
                min="128"
                max="1536"
                value={settings.search.vectorDimension}
                onChange={(e) => handleChange('search', 'vectorDimension', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="resultLimit" className="block text-sm font-medium text-gray-700">
                Default Result Limit
              </label>
              <input
                type="number"
                id="resultLimit"
                min="1"
                max="50"
                value={settings.search.resultLimit}
                onChange={(e) => handleChange('search', 'resultLimit', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div className="flex items-center">
              <input
                id="reranking"
                type="checkbox"
                checked={settings.search.reranking}
                onChange={(e) => handleChange('search', 'reranking', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="reranking" className="ml-2 block text-sm text-gray-900">
                Enable Result Reranking
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="inclusiveSearch"
                type="checkbox"
                checked={settings.search.inclusiveSearch}
                onChange={(e) => handleChange('search', 'inclusiveSearch', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="inclusiveSearch" className="ml-2 block text-sm text-gray-900">
                Inclusive Search (OR instead of AND)
              </label>
            </div>
          </div>
        );
      
      case 'llm':
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="provider" className="block text-sm font-medium text-gray-700">
                LLM Provider
              </label>
              <select
                id="provider"
                value={settings.llm.provider}
                onChange={(e) => handleChange('llm', 'provider', e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="openai">OpenAI</option>
                <option value="azure">Azure OpenAI</option>
                <option value="anthropic">Anthropic</option>
                <option value="huggingface">Hugging Face</option>
                <option value="local">Local Model</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                LLM Model
              </label>
              <select
                id="model"
                value={settings.llm.model}
                onChange={(e) => handleChange('llm', 'model', e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="claude-2">Claude 2</option>
                <option value="llama-2-70b">Llama 2 70B</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="temperature" className="block text-sm font-medium text-gray-700">
                Temperature ({settings.llm.temperature})
              </label>
              <input
                type="range"
                id="temperature"
                min="0"
                max="1"
                step="0.1"
                value={settings.llm.temperature}
                onChange={(e) => handleChange('llm', 'temperature', parseFloat(e.target.value))}
                className="mt-1 block w-full focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label htmlFor="contextWindow" className="block text-sm font-medium text-gray-700">
                Context Window Size (tokens)
              </label>
              <select
                id="contextWindow"
                value={settings.llm.contextWindow}
                onChange={(e) => handleChange('llm', 'contextWindow', parseInt(e.target.value))}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="4096">4,096</option>
                <option value="8192">8,192</option>
                <option value="16384">16,384</option>
                <option value="32768">32,768</option>
              </select>
            </div>
            
            <div className="flex items-center">
              <input
                id="streamResponse"
                type="checkbox"
                checked={settings.llm.streamResponse}
                onChange={(e) => handleChange('llm', 'streamResponse', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="streamResponse" className="ml-2 block text-sm text-gray-900">
                Stream Responses
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="useHistory"
                type="checkbox"
                checked={settings.llm.useHistory}
                onChange={(e) => handleChange('llm', 'useHistory', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="useHistory" className="ml-2 block text-sm text-gray-900">
                Use Conversation History
              </label>
            </div>
            
            <div>
              <label htmlFor="historyTruncation" className="block text-sm font-medium text-gray-700">
                History Truncation (messages)
              </label>
              <input
                type="number"
                id="historyTruncation"
                min="1"
                max="50"
                value={settings.llm.historyTruncation}
                onChange={(e) => handleChange('llm', 'historyTruncation', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
        );
      
      case 'cache':
        return (
          <div className="space-y-6">
            <div className="flex items-center">
              <input
                id="cacheEnabled"
                type="checkbox"
                checked={settings.cache.enabled}
                onChange={(e) => handleChange('cache', 'enabled', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="cacheEnabled" className="ml-2 block text-sm text-gray-900">
                Enable Response Caching
              </label>
            </div>
            
            <div>
              <label htmlFor="ttlSeconds" className="block text-sm font-medium text-gray-700">
                Cache TTL (seconds)
              </label>
              <input
                type="number"
                id="ttlSeconds"
                min="60"
                max="86400"
                value={settings.cache.ttlSeconds}
                onChange={(e) => handleChange('cache', 'ttlSeconds', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="maxSize" className="block text-sm font-medium text-gray-700">
                Max Cache Size (items)
              </label>
              <input
                type="number"
                id="maxSize"
                min="100"
                max="10000"
                value={settings.cache.maxSize}
                onChange={(e) => handleChange('cache', 'maxSize', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
        );
      
      case 'logging':
        return (
          <div className="space-y-6">
            <div>
              <label htmlFor="logLevel" className="block text-sm font-medium text-gray-700">
                Log Level
              </label>
              <select
                id="logLevel"
                value={settings.logging.level}
                onChange={(e) => handleChange('logging', 'level', e.target.value)}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              >
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
              </select>
            </div>
            
            <div className="flex items-center">
              <input
                id="detailedErrors"
                type="checkbox"
                checked={settings.logging.detailedErrors}
                onChange={(e) => handleChange('logging', 'detailedErrors', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="detailedErrors" className="ml-2 block text-sm text-gray-900">
                Show Detailed Errors
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="logUserQueries"
                type="checkbox"
                checked={settings.logging.logUserQueries}
                onChange={(e) => handleChange('logging', 'logUserQueries', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="logUserQueries" className="ml-2 block text-sm text-gray-900">
                Log User Queries
              </label>
            </div>
            
            <div className="flex items-center">
              <input
                id="logResponses"
                type="checkbox"
                checked={settings.logging.logResponses}
                onChange={(e) => handleChange('logging', 'logResponses', e.target.checked)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="logResponses" className="ml-2 block text-sm text-gray-900">
                Log System Responses
              </label>
            </div>
            
            <div>
              <label htmlFor="retentionDays" className="block text-sm font-medium text-gray-700">
                Log Retention (days)
              </label>
              <input
                type="number"
                id="retentionDays"
                min="1"
                max="365"
                value={settings.logging.retentionDays}
                onChange={(e) => handleChange('logging', 'retentionDays', parseInt(e.target.value))}
                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  if (loading && Object.keys(settings).length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        {success && (
          <div className="mb-4 bg-green-50 border-l-4 border-green-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-green-700">Settings saved successfully!</p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 bg-red-50 border-l-4 border-red-400 p-4">
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

        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-4">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                  whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm
                `}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-6">
          {renderTabContent()}
        </div>

        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={handleSave}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <LoadingSpinner size="small" color="white" className="mr-2" />
                Saving...
              </>
            ) : (
              'Save Settings'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;