import React, { useState } from 'react';

const FeedbackList = ({ feedbacks }) => {
  const [expandedFeedbacks, setExpandedFeedbacks] = useState({});

  const toggleExpand = (feedbackId) => {
    setExpandedFeedbacks({
      ...expandedFeedbacks,
      [feedbackId]: !expandedFeedbacks[feedbackId]
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const renderRating = (rating) => {
    if (rating === null || rating === undefined) return null;
    
    return (
      <div className="flex">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg 
            key={star}
            className={`h-5 w-5 ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  if (!feedbacks || feedbacks.length === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Feedback</h3>
        <div className="text-center py-6 text-gray-500">No feedback found.</div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Feedback</h3>
      
      <div className="space-y-4">
        {feedbacks.map((feedback) => (
          <div key={feedback.id} className="border border-gray-200 rounded-md overflow-hidden">
            <div 
              className="bg-gray-50 px-4 py-3 flex justify-between items-center cursor-pointer"
              onClick={() => toggleExpand(feedback.id)}
            >
              <div className="flex-1">
                <div className="flex items-center space-x-4">
                  <div>
                    {feedback.thumbs_up && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Thumbs Up
                      </span>
                    )}
                    {feedback.thumbs_down && (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Thumbs Down
                      </span>
                    )}
                    {feedback.rating && (
                      <div className="mt-1">
                        {renderRating(feedback.rating)}
                      </div>
                    )}
                  </div>
                </div>
                <p className="text-sm text-gray-500 mt-1">{formatDate(feedback.created_at)}</p>
              </div>
              <div className="ml-4">
                <svg 
                  className={`h-5 w-5 text-gray-500 transform ${expandedFeedbacks[feedback.id] ? 'rotate-180' : ''}`} 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            </div>
            
            {expandedFeedbacks[feedback.id] && (
              <div className="px-4 py-3 bg-white border-t border-gray-200">
                {feedback.comment && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-500">Comment</h4>
                    <p className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">{feedback.comment}</p>
                  </div>
                )}
                
                {feedback.message && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-500">Message</h4>
                    <p className="mt-1 text-sm text-gray-900">{feedback.message.content}</p>
                  </div>
                )}
                
                {feedback.user && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium text-gray-500">User</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {feedback.user.username} ({feedback.user.email})
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default FeedbackList;