import React from 'react';
import MessageItem from './MessageItem';

const MessageList = ({ messages, onThumbsUp, onThumbsDown }) => {
  // Group consecutive messages by the same role
  const groupedMessages = messages.reduce((groups, message) => {
    const lastGroup = groups[groups.length - 1];
    
    // Start a new group if it's the first message or the role is different from the last group
    if (!lastGroup || lastGroup.role !== message.role) {
      groups.push({
        role: message.role,
        messages: [message]
      });
    } else {
      // Add to existing group
      lastGroup.messages.push(message);
    }
    
    return groups;
  }, []);

  return (
    <div className="space-y-6">
      {groupedMessages.map((group, groupIndex) => (
        <div key={`group-${groupIndex}`} className="space-y-2">
          {group.messages.map((message, messageIndex) => (
            <MessageItem 
              key={message.id || `${group.role}-${messageIndex}`}
              message={message}
              onThumbsUp={onThumbsUp}
              onThumbsDown={onThumbsDown}
              isLast={messageIndex === group.messages.length - 1}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

export default MessageList;