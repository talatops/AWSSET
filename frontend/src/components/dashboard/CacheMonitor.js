import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';

const CacheMonitor = () => {
  const [cacheStats, setCacheStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [message, setMessage] = useState(null);
  const { token } = useAuth();

  const fetchCacheStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/aws/ec2/cache/statistics`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
              if (response.ok) {
          const data = await response.json();
          setCacheStats(data);
          setMessage({ type: 'success', text: 'Cache statistics updated successfully' });
        } else {
          const errorText = await response.text();
          console.error('Cache stats response:', response.status, errorText);
          throw new Error(`Failed to fetch cache statistics: ${response.status}`);
        }
    } catch (error) {
      console.error('Error fetching cache stats:', error);
      setMessage({ type: 'error', text: 'Failed to fetch cache statistics' });
    } finally {
      setLoading(false);
    }
  };

  const optimizeCache = async () => {
    try {
      setOptimizing(true);
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/aws/ec2/cache/optimize`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMessage({ 
            type: 'success', 
            text: `Cache optimized successfully! Removed ${data.expired_items_removed} expired items.` 
          });
          // Refresh stats after optimization
          setTimeout(fetchCacheStats, 1000);
        } else {
          throw new Error(data.error || 'Cache optimization failed');
        }
      } else {
        const errorText = await response.text();
        console.error('Cache optimization response:', response.status, errorText);
        throw new Error(`Failed to optimize cache: ${response.status}`);
      }
    } catch (error) {
      console.error('Error optimizing cache:', error);
      setMessage({ type: 'error', text: `Cache optimization failed: ${error.message}` });
    } finally {
      setOptimizing(false);
    }
  };

  const refreshCache = async (method = null) => {
    try {
      setRefreshing(true);
      const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const url = method ? `${baseUrl}/api/aws/ec2/cache/refresh?method=${method}` : `${baseUrl}/api/aws/ec2/cache/refresh`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMessage({ 
            type: 'success', 
            text: data.message 
          });
          // Refresh stats after refresh
          setTimeout(fetchCacheStats, 1000);
        } else {
          throw new Error(data.error || 'Cache refresh failed');
        }
      } else {
        const errorText = await response.text();
        console.error('Cache refresh response:', response.status, errorText);
        throw new Error(`Failed to refresh cache: ${response.status}`);
      }
    } catch (error) {
      console.error('Error refreshing cache:', error);
      setMessage({ type: 'error', text: `Cache refresh failed: ${error.message}` });
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchCacheStats();
  }, []);

  const getCacheHealthColor = (health) => {
    switch (health) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'critical': return 'error';
      default: return 'default';
    }
  };

  const getCacheStatusIcon = (status) => {
    switch (status) {
      case 'cached': return <CheckCircleIcon color="success" />;
      case 'expired': return <WarningIcon color="warning" />;
      case 'not_cached': return <MemoryIcon color="disabled" />;
      default: return <MemoryIcon color="disabled" />;
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return 'Invalid';
    }
  };

  const formatAge = (seconds) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  if (loading && !cacheStats) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading Cache Statistics...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" fontWeight="bold">
          Cache Monitor
        </Typography>
      </Box>

      {/* Action Buttons - Moved down with better spacing */}
      <Box display="flex" gap={2} mb={4} justifyContent="center">
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchCacheStats}
          disabled={loading}
          size="large"
        >
          Refresh Stats
        </Button>
        <Button
          variant="contained"
          startIcon={<SpeedIcon />}
          onClick={optimizeCache}
          disabled={optimizing}
          size="large"
          color="primary"
        >
          {optimizing ? 'Optimizing...' : 'Optimize Cache'}
        </Button>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<RefreshIcon />}
          onClick={() => refreshCache()}
          disabled={refreshing}
          size="large"
        >
          {refreshing ? 'Refreshing...' : 'Refresh All Cache'}
        </Button>
      </Box>

      {/* Message */}
      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 4 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      {cacheStats && (
        <Grid container spacing={3}>
          {/* Cache Overview */}
          <Grid item xs={12} md={4}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Cache Overview
                  </Typography>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Total Items
                    </Typography>
                    <Typography variant="h4" fontWeight="bold">
                      {cacheStats.total_cached_items}
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      Health Status
                    </Typography>
                    <Chip
                      label={cacheStats.cache_health}
                      color={getCacheHealthColor(cacheStats.cache_health)}
                      size="small"
                    />
                  </Box>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" color="text.secondary">
                      Hit Rate
                    </Typography>
                    <Typography variant="h6" color="primary">
                      {(cacheStats.performance_metrics?.cache_hit_rate * 100).toFixed(1)}%
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          {/* Performance Metrics */}
          <Grid item xs={12} md={8}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Metrics
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="primary" fontWeight="bold">
                          {cacheStats.performance_metrics?.cache_hits || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Cache Hits
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="error" fontWeight="bold">
                          {cacheStats.performance_metrics?.cache_misses || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Cache Misses
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="success" fontWeight="bold">
                          {cacheStats.performance_metrics?.total_requests || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Total Requests
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Box textAlign="center">
                        <Typography variant="h4" color="info" fontWeight="bold">
                          {cacheStats.cache_size_mb || 0}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Size (MB)
                        </Typography>
                      </Box>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>

          {/* Method Details */}
          <Grid item xs={12}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Method Cache Status
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>Method</TableCell>
                          <TableCell>Status</TableCell>
                          <TableCell>Resource Count</TableCell>
                          <TableCell>Last Check</TableCell>
                          <TableCell>Cache Age</TableCell>
                          <TableCell>Actions</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {Object.entries(cacheStats.methods || {}).map(([method, stats]) => (
                          <TableRow key={method}>
                            <TableCell>
                              <Typography variant="body2" fontWeight="medium">
                                {method.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box display="flex" alignItems="center">
                                {getCacheStatusIcon(stats.cache_status)}
                                <Chip
                                  label={stats.cache_status}
                                  size="small"
                                  color={stats.cache_status === 'cached' ? 'success' : 
                                         stats.cache_status === 'expired' ? 'warning' : 'default'}
                                  sx={{ ml: 1 }}
                                />
                              </Box>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {stats.resource_count || 0}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary">
                                {formatTimestamp(stats.last_check)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" color="text.secondary">
                                {formatAge(stats.cache_age_seconds)}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Tooltip title="Refresh this method's cache">
                                <IconButton
                                  size="small"
                                  onClick={() => refreshCache(method)}
                                  disabled={refreshing}
                                >
                                  <RefreshIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </motion.div>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default CacheMonitor;
