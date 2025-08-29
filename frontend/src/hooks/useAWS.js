import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-toastify';

export const useAWS = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [credentials, setCredentials] = useState(null);

  // Check AWS credentials status
  const checkCredentials = async () => {
    try {
      const response = await api.get('/api/aws/credentials');
      setCredentials(response.data);
      return response.data;
    } catch (error) {
      console.error('Failed to check AWS credentials:', error);
      setCredentials(null);
      return null;
    }
  };

  // Store AWS credentials
  const storeCredentials = async (credentialsData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.post('/api/aws/credentials', credentialsData);
      
      if (response.data.success) {
        setCredentials(response.data);
        toast.success('AWS credentials stored successfully!');
        return response.data;
      } else {
        throw new Error(response.data.message || 'Failed to store credentials');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Validate AWS credentials
  const validateCredentials = async (credentialsData) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.post('/api/aws/validate', credentialsData);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Test AWS permissions
  const testPermissions = async (service = 'ec2', credentialsData = null) => {
    try {
      setLoading(true);
      
      // If credentials are provided, send them in the request body
      // Otherwise, the backend will use stored credentials
      const requestBody = credentialsData || {};
      
      const response = await api.post(`/api/aws/test-permissions?service=${service}`, requestBody);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Remove AWS credentials
  const removeCredentials = async () => {
    try {
      setLoading(true);
      await api.delete('/api/aws/credentials');
      setCredentials(null);
      toast.success('AWS credentials removed successfully!');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Get available AWS regions
  const getRegions = async () => {
    try {
      const response = await api.get('/api/aws/regions');
      return response.data.regions;
    } catch (error) {
      console.error('Failed to get regions:', error);
      return {};
    }
  };

  // Get AWS service statistics
  const getServiceStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get('/api/aws/stats');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkCredentials();
  }, []);

  return {
    loading,
    error,
    credentials,
    checkCredentials,
    storeCredentials,
    validateCredentials,
    testPermissions,
    removeCredentials,
    getRegions,
    getServiceStats,
  };
};

export const useEC2 = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRequest = async (requestFn) => {
    try {
      setLoading(true);
      setError(null);
      return await requestFn();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Instance operations
  const listInstances = async (filters = {}) => {
    return handleRequest(async () => {
      const params = new URLSearchParams();
      if (filters.state) params.append('state', filters.state);
      if (filters.tag) params.append('tag', filters.tag);
      
      const response = await api.get(`/api/aws/ec2/instances?${params}`);
      return response.data;
    });
  };

  const getInstance = async (instanceId) => {
    return handleRequest(async () => {
      const response = await api.get(`/api/aws/ec2/instances/${instanceId}`);
      return response.data;
    });
  };

  const createInstance = async (instanceConfig) => {
    return handleRequest(async () => {
      const response = await api.post('/api/aws/ec2/instances', instanceConfig);
      toast.success('Instance creation initiated!');
      return response.data;
    });
  };

  const startInstance = async (instanceId) => {
    return handleRequest(async () => {
      const response = await api.post(`/api/aws/ec2/instances/${instanceId}/start`);
      toast.success('Instance start initiated!');
      return response.data;
    });
  };

  const stopInstance = async (instanceId, force = false) => {
    return handleRequest(async () => {
      const response = await api.post(`/api/aws/ec2/instances/${instanceId}/stop`, { force });
      toast.success('Instance stop initiated!');
      return response.data;
    });
  };

  const rebootInstance = async (instanceId) => {
    return handleRequest(async () => {
      const response = await api.post(`/api/aws/ec2/instances/${instanceId}/reboot`);
      toast.success('Instance reboot initiated!');
      return response.data;
    });
  };

  const terminateInstance = async (instanceId) => {
    return handleRequest(async () => {
      const response = await api.delete(`/api/aws/ec2/instances/${instanceId}`);
      toast.success('Instance termination initiated!');
      return response.data;
    });
  };

  // Resource listing
  const listSecurityGroups = async () => {
    return handleRequest(async () => {
      const response = await api.get('/api/aws/ec2/security-groups');
      return response.data;
    });
  };

  const listKeyPairs = async () => {
    return handleRequest(async () => {
      const response = await api.get('/api/aws/ec2/key-pairs');
      return response.data;
    });
  };

  const listAMIs = async (filters = {}) => {
    return handleRequest(async () => {
      const params = new URLSearchParams();
      if (filters.name) params.append('name', filters.name);
      if (filters.architecture) params.append('architecture', filters.architecture);
      if (filters.ami_state) params.append('ami_state', filters.ami_state);
      
      const response = await api.get(`/api/aws/ec2/amis?${params}`);
      return response.data;
    });
  };

  return {
    loading,
    error,
    listInstances,
    getInstance,
    createInstance,
    startInstance,
    stopInstance,
    rebootInstance,
    terminateInstance,
    listSecurityGroups,
    listKeyPairs,
    listAMIs,
  };
};
