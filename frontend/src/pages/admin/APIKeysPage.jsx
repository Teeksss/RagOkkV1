import React from 'react';
import APIKeyManager from '../../components/admin/APIKeyManager';

const APIKeysPage = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">API Keys Management</h1>
      <APIKeyManager />
    </div>
  );
};

export default APIKeysPage;