import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'react-toastify';
import credentialCacheService from '../services/credentialCacheService';

export const useAWS = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [credentials, setCredentials] = useState(null);
  const [isMounted, setIsMounted] = useState(true);

  // Check AWS credentials status
  const checkCredentials = async () => {
    try {
      // Use cache service to prevent repeated API calls
      const credentialsData = await credentialCacheService.getCredentials(api);
      
      if (isMounted) {
        setCredentials(credentialsData);
      }
      
      return credentialsData;
    } catch (error) {
      console.error('Failed to check AWS credentials:', error);
      
      if (isMounted) {
        setCredentials(null);
      }
      
      return null;
    }
  };

  // Store AWS credentials
  const storeCredentials = async (credentialsData) => {
    try {
      if (isMounted) setLoading(true);
      if (isMounted) setError(null);
      
      const response = await api.post('/api/aws/credentials', credentialsData);
      
      if (response.data.success) {
        if (isMounted) setCredentials(response.data);
        // Update the global cache
        credentialCacheService.updateCredentials(response.data);
        toast.success('AWS credentials stored successfully!');
        return response.data;
      } else {
        throw new Error(response.data.message || 'Failed to store credentials');
      }
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      if (isMounted) setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      if (isMounted) setLoading(false);
    }
  };

  // Validate AWS credentials
  const validateCredentials = async (credentialsData) => {
    try {
      if (isMounted) setLoading(true);
      if (isMounted) setError(null);
      
      const response = await api.post('/api/aws/validate', credentialsData);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      if (isMounted) setError(errorMessage);
      throw error;
    } finally {
      if (isMounted) setLoading(false);
    }
  };

  // Test AWS permissions
  const testPermissions = async (service = 'ec2', credentialsData = null) => {
    try {
      if (isMounted) setLoading(true);
      
      // If credentials are provided, send them in the request body
      // Otherwise, the backend will use stored credentials
      const requestBody = credentialsData || {};
      
      const response = await api.post(`/api/aws/test-permissions?service=${service}`, requestBody);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      if (isMounted) setError(errorMessage);
      throw error;
    } finally {
      if (isMounted) setLoading(false);
    }
  };

  // Remove AWS credentials
  const removeCredentials = async () => {
    try {
      if (isMounted) setLoading(true);
      await api.delete('/api/aws/credentials');
      if (isMounted) setCredentials(null);
      // Clear the global cache
      credentialCacheService.clearCredentials();
      toast.success('AWS credentials removed successfully!');
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      if (isMounted) setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      if (isMounted) setLoading(false);
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
      if (isMounted) setLoading(true);
      if (isMounted) setError(null);
      const response = await api.get('/api/aws/stats');
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      if (isMounted) setError(errorMessage);
      throw error;
    } finally {
      if (isMounted) setError(null);
      if (isMounted) setLoading(false);
    }
  };

  useEffect(() => {
    setIsMounted(true);
    
    const initCredentials = async () => {
      try {
        // Use cache service for initial loading
        const credentialsData = await credentialCacheService.getCredentials(api);
        if (isMounted) {
          setCredentials(credentialsData);
        }
      } catch (error) {
        console.error('Failed to check AWS credentials:', error);
        if (isMounted) {
          setCredentials(null);
        }
      }
    };
    
    initCredentials();
    
    return () => {
      setIsMounted(false);
    };
  }, [api]);

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
    // Add cache management functions
    refreshCredentials: () => credentialCacheService.refreshCredentials(api),
    hasCachedCredentials: () => credentialCacheService.hasValidCache(),
  };
};

export const useEC2 = () => {
  const { api } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isMounted, setIsMounted] = useState(true);

  const handleRequest = async (requestFn) => {
    try {
      if (isMounted) setLoading(true);
      if (isMounted) setError(null);
      return await requestFn();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message;
      if (isMounted) setError(errorMessage);
      toast.error(errorMessage);
      throw error;
    } finally {
      if (isMounted) setLoading(false);
    }
  };

  useEffect(() => {
    setIsMounted(true);
    return () => {
      setIsMounted(false);
    };
  }, []);

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

  const createKeyPair = async (keyPairConfig) => {
    return handleRequest(async () => {
      const response = await api.post('/api/aws/ec2/key-pairs', keyPairConfig);
      toast.success('Key pair created successfully!');
      return response.data;
    });
  };

  const deleteKeyPair = async (keyPairName) => {
    return handleRequest(async () => {
      const response = await api.delete(`/api/aws/ec2/key-pairs/${keyPairName}`);
      toast.success('Key pair deleted successfully!');
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
    createKeyPair,
    deleteKeyPair,
    listAMIs,
  };
};
