import React from 'react';

const StatCard = ({ title, value, total, icon, color }) => {
  // Calculate percentage if total is provided
  const percentage = total ? Math.round((value / total) * 100) : null;
  
  // Define color classes
  const colorClasses = {
    blue: {
      bg: 'bg-blue-500',
      text: 'text-blue-500',
      light: 'bg-blue-100'
    },
    green: {
      bg: 'bg-green-500',
      text: 'text-green-500',
      light: 'bg-green-100'
    },
    red: {
      bg: 'bg-red-500',
      text: 'text-red-500',
      light: 'bg-red-100'
    },
    yellow: {
      bg: 'bg-yellow-500',
      text: 'text-yellow-500',
      light: 'bg-yellow-100'
    },
    purple: {
      bg: 'bg-purple-500',
      text: 'text-purple-500',
      light: 'bg-purple-100'
    },
    indigo: {
      bg: 'bg-indigo-500',
      text: 'text-indigo-500',
      light: 'bg-indigo-100'
    }
  };
  
  // Default to blue if invalid color is provided
  const colorClass = colorClasses[color] || colorClasses.blue;
  
  // Icon components
  const icons = {
    users: (
      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
      </svg>
    ),
    document: (
      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
      </svg>
    ),
    chat: (
      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
      </svg>
    ),
    exclamation: (
      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    ),
    star: (
      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
      </svg>
    ),
    chart: (
      <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
      </svg>
    )
  };
  
  return (
    <div className="bg-white rounded-lg shadow p-6 flex items-start">
      <div className={`${colorClass.light} p-3 rounded-md mr-4`}>
        <span className={colorClass.text}>
          {icons[icon] || icons.chart}
        </span>
      </div>
      <div>
        <h3 className="text-lg font-medium text-gray-900">{title}</h3>
        <div className="mt-1 flex items-baseline">
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
          {total && (
            <p className="ml-2 text-sm text-gray-500">
              of {total} ({percentage}%)
            </p>
          )}
        </div>
        {percentage !== null && (
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`${colorClass.bg} h-2 rounded-full`} 
              style={{ width: `${percentage}%` }}
            ></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;