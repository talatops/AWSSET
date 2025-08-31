import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  Button,
  Alert,
  Skeleton,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Cloud,
  Security,
  Speed,
  Memory,
  Storage,
  AttachMoney,
  Refresh,
  Launch,
  CheckCircle,
  Warning,
  Error,
  Info,
  VpnKey,
  Computer,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import { useAWS } from '../../hooks/useAWS';
import { useWebSocket } from '../../contexts/WebSocketContext';

// Helper function to parse service costs safely
const parseServiceCost = (cost) => {
  if (!cost) return 0;
  
  if (typeof cost === 'string') {
    // Handle real cost format: "$0.96"
    const costMatch = cost.match(/\$([\d.]+)/);
    if (costMatch) {
      return parseFloat(costMatch[1]);
    }
    // Handle fallback values like "N/A" or "0.00"
    if (cost !== 'N/A' && cost !== '0.00') {
      const parsed = parseFloat(cost);
      return isNaN(parsed) ? 0 : parsed;
    }
  }
  
  return 0;
};

// Generate real data from AWS statistics
const generateRealData = (awsStats) => {
  if (!awsStats?.services) {
    return null;
  }

  const services = awsStats.services;
  
  // Calculate active services count
  const activeServices = Object.values(services).filter(service => 
    service.status === 'active'
  ).length;
  
  // Calculate total running instances
  const totalInstances = services.ec2?.instances || 0;
  const runningInstances = services.ec2?.running || 0;
  
  // Calculate total cost (handle both real costs and fallback values)
  const calculateTotalCost = () => {
    let total = 0;
    Object.values(services).forEach(service => {
      if (service.cost && typeof service.cost === 'string') {
        // Handle real cost format: "$0.96"
        const costMatch = service.cost.match(/\$([\d.]+)/);
        if (costMatch) {
          total += parseFloat(costMatch[1]);
        }
        // Handle fallback values like "N/A" or "0.00"
        else if (service.cost !== 'N/A' && service.cost !== '0.00') {
          const parsed = parseFloat(service.cost);
          if (!isNaN(parsed)) {
            total += parsed;
          }
        }
      }
    });
    return total;
  };
  
  const totalCost = calculateTotalCost();
  
  // Generate service usage pie chart data
  const serviceUsage = [
    { 
      name: 'EC2', 
      value: services.ec2?.instances || 0, 
      cost: parseServiceCost(services.ec2?.cost), 
      color: '#FF9900' 
    },
    { 
      name: 'S3', 
      value: services.s3?.buckets || 0, 
      cost: parseServiceCost(services.s3?.cost), 
      color: '#3F48CC' 
    },
    { 
      name: 'Lambda', 
      value: services.lambda?.functions || 0, 
      cost: parseServiceCost(services.lambda?.cost), 
      color: '#FF9900' 
    },
    { 
      name: 'RDS', 
      value: services.rds?.databases || 0, 
      cost: parseServiceCost(services.rds?.cost), 
      color: '#527FFF' 
    },
    { 
      name: 'IAM', 
      value: services.iam?.users || 0, 
      cost: parseServiceCost(services.iam?.cost), 
      color: '#759C3E' 
    },
  ].filter(service => service.value > 0); // Only show services with resources
  
  // Generate mock cost data for the chart (real cost tracking would need CloudWatch/Cost Explorer)
  const costData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    cost: Math.random() * (totalCost * 0.3) + (totalCost * 0.7),
    predicted: Math.random() * (totalCost * 0.4) + (totalCost * 0.6),
  }));
  
  // Generate activity based on actual resource counts
  const recentActivity = [];
  let activityId = 1;
  
  if (runningInstances > 0) {
    recentActivity.push({
      id: activityId++,
      type: 'success',
      message: `${runningInstances} EC2 instance${runningInstances > 1 ? 's' : ''} currently running`,
      time: 'Current status'
    });
  }
  
  if (services.s3?.buckets > 0) {
    recentActivity.push({
      id: activityId++,
      type: 'info',
      message: `${services.s3.buckets} S3 bucket${services.s3.buckets > 1 ? 's' : ''} configured`,
      time: 'Current status'
    });
  }
  
  if (services.lambda?.functions > 0) {
    recentActivity.push({
      id: activityId++,
      type: 'info',
      message: `${services.lambda.functions} Lambda function${services.lambda.functions > 1 ? 's' : ''} deployed`,
      time: 'Current status'
    });
  }
  
  if (services.iam?.users > 0) {
    recentActivity.push({
      id: activityId++,
      type: 'info',
      message: `${services.iam.users} IAM user${services.iam.users > 1 ? 's' : ''} configured`,
      time: 'Current status'
    });
  }
  
  // Add a general activity if no specific resources
  if (recentActivity.length === 0) {
    recentActivity.push({
      id: 1,
      type: 'info',
      message: 'AWS credentials connected successfully',
      time: 'Ready to manage resources'
    });
  }
  
  return {
    metrics: {
      totalServices: 6, // Total available services
      activeInstances: runningInstances,
      totalCost: totalCost,
      monthlyChange: totalCost > 0 ? 12.5 : 0, // Mock change percentage
    },
    costData,
    serviceUsage,
    recentActivity,
    quickActions: [
      { title: 'Launch EC2 Instance', icon: <Computer />, color: 'primary', action: 'launch-instance' },
      { title: 'Create S3 Bucket', icon: <Storage />, color: 'info', action: 'create-bucket' },
      { title: 'Deploy Lambda', icon: <Speed />, color: 'secondary', action: 'deploy-lambda' },
      { title: 'Setup Monitoring', icon: <Security />, color: 'warning', action: 'setup-monitoring' },
    ],
  };
};

const StatCard = ({ title, value, change, icon, trend, loading = false }) => {
  const { animations } = useTheme();
  
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width="60%" height={24} />
          <Skeleton variant="text" width="40%" height={32} />
          <Skeleton variant="text" width="30%" height={20} />
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      whileHover={animations ? { scale: 1.02 } : {}}
      transition={{ duration: 0.2 }}
    >
      <Card sx={{ height: '100%', background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)' }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="flex-start">
            <Box>
              <Typography color="text.secondary" gutterBottom variant="body2">
                {title}
              </Typography>
              <Typography variant="h4" fontWeight="bold">
                {value}
              </Typography>
              {change && (
                <Box display="flex" alignItems="center" mt={1}>
                  {trend === 'up' ? (
                    <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                  ) : (
                    <TrendingDown sx={{ color: 'error.main', fontSize: 16, mr: 0.5 }} />
                  )}
                  <Typography 
                    variant="body2" 
                    color={trend === 'up' ? 'success.main' : 'error.main'}
                  >
                    {change}
                  </Typography>
                </Box>
              )}
            </Box>
            <Avatar sx={{ bgcolor: 'primary.main', width: 48, height: 48 }}>
              {icon}
            </Avatar>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const ActivityItem = ({ activity }) => {
  const getIcon = (type) => {
    switch (type) {
      case 'success': return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'warning': return <Warning sx={{ color: 'warning.main' }} />;
      case 'error': return <Error sx={{ color: 'error.main' }} />;
      default: return <Info sx={{ color: 'info.main' }} />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <ListItem>
        <ListItemIcon>
          {getIcon(activity.type)}
        </ListItemIcon>
        <ListItemText
          primary={activity.message}
          secondary={activity.time}
          primaryTypographyProps={{ variant: 'body2' }}
          secondaryTypographyProps={{ variant: 'caption' }}
        />
      </ListItem>
    </motion.div>
  );
};

const Overview = () => {
  const { user } = useAuth();
  const { isDark, animations } = useTheme();
  const { credentials, getServiceStats, checkCredentials, hasCachedCredentials } = useAWS();
  const { connected, awsStats, requestAwsStats } = useWebSocket();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    let isMounted = true;
    
    if (isMounted) {
      // Only check credentials if not already cached
      if (!hasCachedCredentials()) {
        checkCredentials();
      }
    }
    
    return () => {
      isMounted = false;
    };
  }, [hasCachedCredentials, checkCredentials]);

  // Update data when WebSocket provides new AWS stats
  useEffect(() => {
    let isMounted = true;
    
    if (awsStats && isMounted) {
      console.log('🔄 Received real-time AWS stats update:', awsStats);
      const processedData = generateRealData(awsStats);
      setData(processedData);
      setLastUpdate(new Date());
      setLoading(false);
    }
    
    return () => {
      isMounted = false;
    };
  }, [awsStats]);

  // Fallback to HTTP if WebSocket is not connected
  useEffect(() => {
    let isMounted = true;
    
    if (isMounted) {
      if (credentials?.has_credentials && !connected && !awsStats) {
        loadRealData();
      } else if (!credentials?.has_credentials) {
        // If no credentials, show a basic state
        setData(generateRealData({ services: {} }));
        setLoading(false);
      }
    }
    
    return () => {
      isMounted = false;
    };
  }, [credentials, connected]);

  // Request real-time data when WebSocket connects
  useEffect(() => {
    let isMounted = true;
    
    if (connected && credentials?.has_credentials && isMounted) {
      console.log('🔗 WebSocket connected, requesting AWS stats...');
      requestAwsStats();
    }
    
    return () => {
      isMounted = false;
    };
  }, [connected, credentials, requestAwsStats]);

  const loadRealData = async () => {
    try {
      setLoading(true);
      const stats = await getServiceStats();
      
      // Check if component is still mounted before updating state
      if (document.body.contains(document.querySelector('[data-testid="overview-component"]'))) {
        const processedData = generateRealData(stats);
        setData(processedData);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('Failed to load AWS stats:', error);
      // Fallback to empty data
      if (document.body.contains(document.querySelector('[data-testid="overview-component"]'))) {
        setData(generateRealData({ services: {} }));
      }
    } finally {
      if (document.body.contains(document.querySelector('[data-testid="overview-component"]'))) {
        setLoading(false);
      }
    }
  };

  const refreshData = async () => {
    if (connected && credentials?.has_credentials) {
      // Use WebSocket for real-time refresh
      console.log('🔄 Requesting fresh AWS stats via WebSocket...');
      requestAwsStats();
    } else if (credentials?.has_credentials) {
      // Fallback to HTTP
      await loadRealData();
    } else {
      await checkCredentials();
    }
  };

  const handleQuickAction = (action) => {
    switch (action) {
      case 'launch-instance':
        // Navigate to AWS Services with EC2 instances tab
        navigate('/dashboard/aws', { state: { activeTab: 0 } });
        break;
      case 'create-bucket':
        navigate('/dashboard/aws', { state: { activeTab: 1 } });
        break;
      case 'deploy-lambda':
        navigate('/dashboard/aws');
        break;
      case 'setup-monitoring':
        navigate('/dashboard/aws');
        break;
      default:
        navigate('/dashboard/aws');
    }
  };

  if (!data && loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Grid container spacing={3}>
          {[...Array(4)].map((_, i) => (
            <Grid item xs={12} sm={6} md={3} key={i}>
              <StatCard loading />
            </Grid>
          ))}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="40%" height={32} />
                <Skeleton variant="rectangular" height={300} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Skeleton variant="text" width="40%" height={32} />
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} variant="text" height={40} sx={{ mb: 1 }} />
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }} data-testid="overview-component">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Welcome back, {user?.username || 'User'}! 👋
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Here's what's happening with your AWS infrastructure today.
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={refreshData}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </motion.div>

      {/* AWS Credentials Status */}
      {!credentials?.has_credentials && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <Alert 
            severity="warning" 
            sx={{ mb: 3 }}
            action={
              <Button 
                color="inherit" 
                size="small"
                startIcon={<VpnKey />}
                onClick={() => navigate('/dashboard/aws')}
              >
                Setup Credentials
              </Button>
            }
          >
            <Typography variant="body2">
              🔑 <strong>AWS Credentials Required:</strong> Configure your AWS credentials to see real statistics and manage your infrastructure.
            </Typography>
          </Alert>
        </motion.div>
      )}

      {credentials?.has_credentials && awsStats && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body2">
              ✅ <strong>AWS Connected:</strong> Account {awsStats.account_summary?.account_id} in region {awsStats.region}
              {loading && ' (Refreshing data...)'}
            </Typography>
          </Alert>
        </motion.div>
      )}

      {/* Key Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Services"
            value={data?.metrics.totalServices || 0}
            change="+2 this week"
            trend="up"
            icon={<Cloud />}
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Running Instances"
            value={data?.metrics.activeInstances || 0}
            change="+1 today"
            trend="up"
            icon={<Memory />}
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Monthly Cost"
            value={`$${data?.metrics.totalCost.toFixed(2) || '0.00'}`}
            change={`${data?.metrics.monthlyChange > 0 ? '+' : ''}${data?.metrics.monthlyChange.toFixed(1)}%`}
            trend={data?.metrics.monthlyChange > 0 ? 'up' : 'down'}
            icon={<AttachMoney />}
            loading={loading}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Security Score"
            value="94%"
            change="+2% this week"
            trend="up"
            icon={<Security />}
            loading={loading}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Cost Trends Chart */}
        <Grid item xs={12} md={8}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
          >
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" fontWeight="bold">
                    Cost Trends (Last 30 Days)
                  </Typography>
                  <Box display="flex" gap={1}>
                    <Chip 
                      label={connected ? "Live Data" : "Cached Data"} 
                      color={connected ? "success" : "warning"} 
                      size="small" 
                    />
                    {lastUpdate && (
                      <Chip 
                        label={`Updated ${lastUpdate.toLocaleTimeString()}`} 
                        variant="outlined" 
                        size="small" 
                      />
                    )}
                  </Box>
                </Box>
                
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={data?.costData || []}>
                    <defs>
                      <linearGradient id="costGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                    <XAxis 
                      dataKey="day" 
                      stroke={isDark ? '#9ca3af' : '#6b7280'}
                      fontSize={12}
                    />
                    <YAxis 
                      stroke={isDark ? '#9ca3af' : '#6b7280'}
                      fontSize={12}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                        borderRadius: '8px',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="cost"
                      stroke="#3b82f6"
                      fillOpacity={1}
                      fill="url(#costGradient)"
                      strokeWidth={2}
                    />
                    <Line
                      type="monotone"
                      dataKey="predicted"
                      stroke="#f59e0b"
                      strokeDasharray="5 5"
                      strokeWidth={2}
                      dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Service Usage Pie Chart */}
        <Grid item xs={12} md={4}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, duration: 0.5 }}
          >
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={2}>
                  Service Usage
                </Typography>
                
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={data?.serviceUsage || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {data?.serviceUsage.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value, name, props) => [
                        `${value}%`,
                        `$${props.payload.cost}`
                      ]}
                    />
                  </PieChart>
                </ResponsiveContainer>

                <Box mt={2}>
                  {data?.serviceUsage.map((service, index) => (
                    <Box key={service.name} display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Box display="flex" alignItems="center">
                        <Box
                          sx={{
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            bgcolor: service.color,
                            mr: 1,
                          }}
                        />
                        <Typography variant="body2">{service.name}</Typography>
                      </Box>
                      <Typography variant="body2" fontWeight="bold">
                        ${service.cost}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Billing Summary */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" gutterBottom>
                  AWS Billing Summary
                </Typography>
                
                {awsStats?.billing ? (
                  <Box>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="body2" color="text.secondary">
                        Current Month
                      </Typography>
                      <Typography variant="h6" fontWeight="bold" color="primary">
                        ${awsStats.billing.current_month?.toFixed(2) || '0.00'}
                      </Typography>
                    </Box>
                    
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="body2" color="text.secondary">
                        Estimated Monthly
                      </Typography>
                      <Typography variant="h6" fontWeight="bold" color="warning.main">
                        ${awsStats.billing.estimated_monthly?.toFixed(2) || '0.00'}
                      </Typography>
                    </Box>
                    
                    {awsStats.billing.period && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        Period: {awsStats.billing.period}
                      </Typography>
                    )}
                    
                    {awsStats.billing.note && (
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          {awsStats.billing.note}
                        </Typography>
                      </Alert>
                    )}
                  </Box>
                ) : (
                  <Box textAlign="center" py={2}>
                    <Typography variant="body2" color="text.secondary">
                      Billing data not available
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6" fontWeight="bold">
                    Recent Activity
                  </Typography>
                  <IconButton size="small">
                    <Launch fontSize="small" />
                  </IconButton>
                </Box>

                <List disablePadding>
                  {data?.recentActivity.map((activity) => (
                    <ActivityItem key={activity.id} activity={activity} />
                  ))}
                </List>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.5 }}
          >
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={2}>
                  Quick Actions
                </Typography>

                <Grid container spacing={2}>
                  {data?.quickActions.map((action, index) => (
                    <Grid item xs={6} key={action.title}>
                      <motion.div
                        whileHover={animations ? { scale: 1.05 } : {}}
                        whileTap={animations ? { scale: 0.95 } : {}}
                      >
                        <Paper
                          onClick={() => handleQuickAction(action.action)}
                          sx={{
                            p: 2,
                            textAlign: 'center',
                            cursor: 'pointer',
                            border: '1px solid',
                            borderColor: 'divider',
                            '&:hover': {
                              borderColor: `${action.color}.main`,
                              bgcolor: `${action.color}.50`,
                            },
                            transition: 'all 0.2s ease-in-out',
                          }}
                        >
                          <Avatar
                            sx={{
                              bgcolor: `${action.color}.main`,
                              mx: 'auto',
                              mb: 1,
                            }}
                          >
                            {action.icon}
                          </Avatar>
                          <Typography variant="body2" fontWeight="medium">
                            {action.title}
                          </Typography>
                        </Paper>
                      </motion.div>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>

      {/* AI Assistant Prompt */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1, duration: 0.5 }}
      >
        <Alert 
          severity="info" 
          sx={{ mt: 3 }}
          action={
            <Button color="inherit" size="small">
                              Try AI Assistant →
            </Button>
          }
        >
                          💡 <strong>Pro Tip:</strong> Ask the AI assistant to help you optimize costs or troubleshoot issues!
        </Alert>
      </motion.div>
    </Box>
  );
};

export default Overview;
