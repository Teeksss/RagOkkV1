/**
 * Format a date to a human-readable string
 * 
 * @param {string|Date} dateInput Date to format
 * @param {Object} options Formatting options
 * @param {boolean} options.includeTime Whether to include time
 * @param {string} options.locale Locale to use for formatting
 * @returns {string} Formatted date string
 */
export const formatDate = (dateInput, options = {}) => {
  if (!dateInput) return 'N/A';
  
  const { includeTime = true, locale = 'en-US' } = options;
  
  try {
    const date = dateInput instanceof Date ? dateInput : new Date(dateInput);
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    
    const formatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      ...(includeTime && {
        hour: '2-digit',
        minute: '2-digit'
      })
    };
    
    return new Intl.DateTimeFormat(locale, formatOptions).format(date);
  } catch (error) {
    console.error('Error formatting date:', error);
    return 'Format error';
  }
};

/**
 * Format file size to human-readable string
 * 
 * @param {number} sizeInBytes File size in bytes
 * @param {number} decimals Number of decimal places to include
 * @returns {string} Formatted file size
 */
export const formatFileSize = (sizeInBytes, decimals = 2) => {
  if (!sizeInBytes || isNaN(sizeInBytes)) return 'Unknown size';
  
  if (sizeInBytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(sizeInBytes) / Math.log(k));
  
  return parseFloat((sizeInBytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
};

/**
 * Truncate text to a specified length
 * 
 * @param {string} text Text to truncate
 * @param {number} maxLength Maximum length
 * @param {string} suffix Suffix to add to truncated text
 * @returns {string} Truncated text
 */
export const truncateText = (text, maxLength = 100, suffix = '...') => {
  if (!text) return '';
  
  if (text.length <= maxLength) return text;
  
  return text.substring(0, maxLength).trim() + suffix;
};

/**
 * Format a number with thousand separators
 * 
 * @param {number} num Number to format
 * @param {Object} options Formatting options
 * @param {string} options.locale Locale to use for formatting
 * @param {number} options.minimumFractionDigits Minimum fraction digits
 * @param {number} options.maximumFractionDigits Maximum fraction digits
 * @returns {string} Formatted number
 */
export const formatNumber = (num, options = {}) => {
  if (num === null || num === undefined || isNaN(num)) {
    return 'N/A';
  }
  
  const {
    locale = 'en-US',
    minimumFractionDigits = 0,
    maximumFractionDigits = 2
  } = options;
  
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits,
    maximumFractionDigits
  }).format(num);
};

/**
 * Format a duration in seconds to a human-readable string
 * 
 * @param {number} seconds Duration in seconds
 * @returns {string} Formatted duration
 */
export const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return 'N/A';
  
  // For very short durations
  if (seconds < 60) {
    return `${Math.round(seconds)} seconds`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  
  // For durations less than an hour
  if (minutes < 60) {
    return `${minutes} min${minutes !== 1 ? 's' : ''} ${remainingSeconds} sec${remainingSeconds !== 1 ? 's' : ''}`;
  }
  
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  
  // For durations with hours
  return `${hours} hr${hours !== 1 ? 's' : ''} ${remainingMinutes} min${remainingMinutes !== 1 ? 's' : ''}`;
};