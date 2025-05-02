import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts/AuthContext';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { uploadDocument } from '../api/documents';

const UploadDocument = () => {
  const { user } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [options, setOptions] = useState({
    chunkSize: 1000,
    chunkOverlap: 100,
    extractImages: true,
    ocrEnabled: true,
    tags: []
  });
  const [tagInput, setTagInput] = useState('');

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setError(null);
  };

  const handleOptionChange = (e) => {
    const { name, value, type, checked } = e.target;
    setOptions({
      ...options,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !options.tags.includes(tagInput.trim())) {
      setOptions({
        ...options,
        tags: [...options.tags, tagInput.trim()]
      });
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setOptions({
      ...options,
      tags: options.tags.filter(tag => tag !== tagToRemove)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!file) {
      setError('Please select a file to upload');
      return;
    }
    
    setUploading(true);
    setError(null);
    
    try {
      // Create form data
      const formData = new FormData();
      formData.append('file', file);
      
      // Add options as JSON string
      formData.append('options', JSON.stringify({
        chunk_size: parseInt(options.chunkSize),
        chunk_overlap: parseInt(options.chunkOverlap),
        extract_images: options.extractImages,
        ocr_enabled: options.ocrEnabled,
        tags: options.tags
      }));
      
      // Upload with progress tracking
      const onProgress = (percent) => {
        setProgress(percent);
      };
      
      const result = await uploadDocument(formData, onProgress);
      
      // Redirect to document details page
      navigate(`/app/documents/${result.id}`);
    } catch (err) {
      console.error('Error uploading document:', err);
      setError(err.message || 'Failed to upload document. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const fileSize = file ? (file.size / 1024 / 1024).toFixed(2) : 0;
  const fileTooLarge = fileSize > 10; // 10MB limit

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="md:flex md:items-center md:justify-between mb-6">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">Upload Document</h1>
          <p className="mt-1 text-sm text-gray-500">
            Add documents to your knowledge base for search and retrieval.
          </p>
        </div>
      </div>

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

      <div className="bg-white shadow sm:rounded-md">
        <div className="px-4 py-5 sm:p-6">
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
              {/* File upload area */}
              <div className="sm:col-span-6">
                <label className="block text-sm font-medium text-gray-700">
                  Document File
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <svg 
                      className="mx-auto h-12 w-12 text-gray-400" 
                      stroke="currentColor" 
                      fill="none" 
                      viewBox="0 0 48 48" 
                      aria-hidden="true"
                    >
                      <path 
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" 
                        strokeWidth={2} 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                      />
                    </svg>
                    
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                      >
                        <span>Upload a file</span>
                        <input 
                          id="file-upload" 
                          name="file-upload" 
                          type="file" 
                          className="sr-only"
                          onChange={handleFileChange}
                          disabled={uploading}
                          accept=".pdf,.docx,.txt,.md,.json,.csv,.xlsx,.pptx,.html,.png,.jpg,.jpeg"
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    
                    <p className="text-xs text-gray-500">
                      PDF, Word, Excel, Text, Markdown, Images up to 10MB
                    </p>
                    
                    {file && (
                      <div className="mt-2 text-sm text-gray-900 bg-gray-50 p-2 rounded">
                        <p className="font-medium">{file.name}</p>
                        <p className={`text-xs ${fileTooLarge ? 'text-red-500 font-medium' : 'text-gray-500'}`}>
                          {fileSize} MB {fileTooLarge && '(File too large)'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Processing options */}
              <div className="sm:col-span-3">
                <label htmlFor="chunkSize" className="block text-sm font-medium text-gray-700">
                  Chunk Size (characters)
                </label>
                <div className="mt-1">
                  <input
                    type="number"
                    name="chunkSize"
                    id="chunkSize"
                    min="100"
                    max="5000"
                    value={options.chunkSize}
                    onChange={handleOptionChange}
                    className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Recommended: 1000 for general text
                </p>
              </div>

              <div className="sm:col-span-3">
                <label htmlFor="chunkOverlap" className="block text-sm font-medium text-gray-700">
                  Chunk Overlap (characters)
                </label>
                <div className="mt-1">
                  <input
                    type="number"
                    name="chunkOverlap"
                    id="chunkOverlap"
                    min="0"
                    max="1000"
                    value={options.chunkOverlap}
                    onChange={handleOptionChange}
                    className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md"
                  />
                </div>
                <p className="mt-1 text-xs text-gray-500">
                  Recommended: 100 for better context between chunks
                </p>
              </div>

              <div className="sm:col-span-3">
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="extractImages"
                      name="extractImages"
                      type="checkbox"
                      checked={options.extractImages}
                      onChange={handleOptionChange}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="extractImages" className="font-medium text-gray-700">
                      Extract Images
                    </label>
                    <p className="text-gray-500">Extract and process images from documents</p>
                  </div>
                </div>
              </div>

              <div className="sm:col-span-3">
                <div className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id="ocrEnabled"
                      name="ocrEnabled"
                      type="checkbox"
                      checked={options.ocrEnabled}
                      onChange={handleOptionChange}
                      className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor="ocrEnabled" className="font-medium text-gray-700">
                      Enable OCR
                    </label>
                    <p className="text-gray-500">Apply OCR to extract text from images</p>
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="sm:col-span-6">
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700">
                  Tags
                </label>
                <div className="mt-1 flex rounded-md shadow-sm">
                  <input
                    type="text"
                    name="tags"
                    id="tags"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    className="focus:ring-blue-500 focus:border-blue-500 flex-1 block w-full rounded-none rounded-l-md sm:text-sm border-gray-300"
                    placeholder="Add tags to organize your documents"
                  />
                  <button
                    type="button"
                    onClick={handleAddTag}
                    className="inline-flex items-center px-3 py-2 border border-l-0 border-gray-300 rounded-r-md bg-gray-50 text-gray-500 sm:text-sm hover:bg-gray-100"
                  >
                    Add
                  </button>
                </div>
                
                {options.tags.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {options.tags.map((tag, index) => (
                      <span 
                        key={index} 
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-1.5 inline-flex items-center justify-center h-4 w-4 rounded-full bg-blue-200 text-blue-600 hover:bg-blue-300"
                        >
                          <svg className="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8">
                            <path strokeLinecap="round" strokeWidth="1.5" d="M1 1l6 6m0-6L1 7" />
                          </svg>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Upload progress */}
            {uploading && (
              <div className="mt-6">
                <div className="relative pt-1">
                  <div className="flex mb-2 items-center justify-between">
                    <div>
                      <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-blue-600 bg-blue-200">
                        Uploading
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-xs font-semibold inline-block text-blue-600">
                        {progress}%
                      </span>
                    </div>
                  </div>
                  <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-blue-200">
                    <div 
                      style={{ width: `${progress}%` }} 
                      className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500"
                    ></div>
                  </div>
                </div>
              </div>
            )}

            {/* Form actions */}
            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => navigate('/app/documents')}
                disabled={uploading}
                className="mr-3 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={uploading || !file || fileTooLarge}
                className="py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? (
                  <span className="flex items-center">
                    <LoadingSpinner size="small" color="white" />
                    <span className="ml-2">Uploading...</span>
                  </span>
                ) : 'Upload Document'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default UploadDocument;