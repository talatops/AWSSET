import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Avatar,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Alert,
  LinearProgress,
  Badge,
  Dialog,
  DialogTitle,
  DialogContent,
  Tab,
  Tabs,
} from '@mui/material';
import {
  Launch,
  Refresh,
  PlayArrow,
  Stop,
  Settings,
  Monitor,
  Storage,
  Functions,
  Security,
  CloudQueue,
  DataObject,
  Psychology,
  VpnKey,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useAWS } from '../../hooks/useAWS';
import AWSCredentialsSetup from '../aws/AWSCredentialsSetup';
import EC2Instances from '../aws/EC2Instances';
import AMIManagement from '../aws/AMIManagement';
import SecurityGroupManagement from '../aws/SecurityGroupManagement';
import KeyPairManagement from '../aws/KeyPairManagement';

// Mock AWS services data
const awsServices = [
  {
    name: 'EC2',
    fullName: 'Elastic Compute Cloud',
    icon: <CloudQueue />,
    color: '#FF9900',
    status: 'active',
    instances: 8,
    running: 6,
    stopped: 2,
    cost: '$68.20',
    description: 'Virtual servers in the cloud',
  },
  {
    name: 'S3',
    fullName: 'Simple Storage Service',
    icon: <Storage />,
    color: '#3F48CC',
    status: 'active',
    buckets: 12,
    objects: '2.4M',
    storage: '145.2 GB',
    cost: '$32.10',
    description: 'Scalable object storage',
  },
  {
    name: 'Lambda',
    fullName: 'AWS Lambda',
    icon: <Functions />,
    color: '#FF9900',
    status: 'active',
    functions: 15,
    executions: '1.2M',
    errors: 23,
    cost: '$12.80',
    description: 'Serverless compute service',
  },
  {
    name: 'RDS',
    fullName: 'Relational Database Service',
    icon: <DataObject />,
    color: '#527FFF',
    status: 'active',
    databases: 3,
    connections: 45,
    storage: '89.5 GB',
    cost: '$28.90',
    description: 'Managed relational database',
  },
  {
    name: 'IAM',
    fullName: 'Identity & Access Management',
    icon: <Security />,
    color: '#DD344C',
    status: 'active',
    users: 12,
    roles: 8,
    policies: 25,
    cost: '$0.00',
    description: 'Identity and access management',
  },
  {
    name: 'Bedrock',
    fullName: 'Amazon Bedrock',
    icon: <Psychology />,
    color: '#FF4B4B',
    status: 'inactive',
    models: 0,
    requests: 0,
    tokens: 0,
    cost: '$0.00',
    description: 'Foundation models for AI apps',
  },
];

const ServiceCard = ({ service, onAction }) => {
  const { animations } = useTheme();
  const [loading, setLoading] = useState(false);

  const handleAction = async (action) => {
    setLoading(true);
    
    try {
      switch (action) {
        case 'view':
          // Open AWS Console in new tab with user's region
          const awsConsoleUrls = {
            'EC2': 'https://console.aws.amazon.com/ec2/',
            'S3': 'https://console.aws.amazon.com/s3/',
            'Lambda': 'https://console.aws.amazon.com/lambda/',
            'RDS': 'https://console.aws.amazon.com/rds/',
            'IAM': 'https://console.aws.amazon.com/iam/',
            'CloudWatch': 'https://console.aws.amazon.com/cloudwatch/',
            'VPC': 'https://console.aws.amazon.com/vpc/',
            'Bedrock': 'https://console.aws.amazon.com/bedrock/'
          };
          
          if (awsConsoleUrls[service.name]) {
            // Try to get user's AWS region from credentials
            let region = 'us-east-1'; // Default region
            try {
              const userRegion = localStorage.getItem('aws_region');
              if (userRegion) {
                region = userRegion;
              }
            } catch (error) {
              console.warn('Could not get AWS region from storage');
            }
            
            // Open AWS Console with region
            const consoleUrl = `${awsConsoleUrls[service.name]}?region=${region}`;
            window.open(consoleUrl, '_blank');
          }
          break;
          
        case 'monitor':
          // Navigate to service management page
          onAction(service.name, 'view');
          break;
          
        case 'settings':
          // Open service configuration/settings
          if (service.name === 'EC2') {
            // Navigate to EC2 with settings tab
            onAction(service.name, 'view');
            // You could also open a settings dialog here
          } else {
            onAction(service.name, 'view');
          }
          break;
          
        case 'start':
        case 'stop':
          // Handle service start/stop (if applicable)
          onAction(service.name, action);
          break;
          
        default:
          onAction(service.name, action);
      }
    } catch (error) {
      console.error(`Failed to handle action ${action}:`, error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'error': return 'error';
      case 'warning': return 'warning';
      default: return 'default';
    }
  };

  return (
    <motion.div
      whileHover={animations ? { scale: 1.02, y: -4 } : {}}
      transition={{ duration: 0.2 }}
    >
      <Card sx={{ height: '100%', position: 'relative', overflow: 'visible' }}>
        {loading && <LinearProgress />}
        
        <CardContent sx={{ p: 3 }}>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
            <Box display="flex" alignItems="center">
              <Avatar
                sx={{
                  bgcolor: service.color,
                  width: 48,
                  height: 48,
                  mr: 2,
                }}
              >
                {service.icon}
              </Avatar>
              <Box>
                <Typography variant="h6" fontWeight="bold">
                  {service.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {service.fullName}
                </Typography>
              </Box>
            </Box>
            
            <Chip
              label={service.status}
              color={getStatusColor(service.status)}
              size="small"
            />
          </Box>

          {/* Description */}
          <Typography variant="body2" color="text.secondary" mb={2}>
            {service.description}
          </Typography>

          {/* Metrics */}
          <Box mb={2}>
            {service.name === 'EC2' && (
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Instances
                  </Typography>
                  <Typography variant="h6">{service.instances}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Running
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {service.running}
                  </Typography>
                </Grid>
              </Grid>
            )}

            {service.name === 'S3' && (
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Buckets
                  </Typography>
                  <Typography variant="h6">{service.buckets}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Storage
                  </Typography>
                  <Typography variant="h6">{service.storage}</Typography>
                </Grid>
              </Grid>
            )}

            {service.name === 'Lambda' && (
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Functions
                  </Typography>
                  <Typography variant="h6">{service.functions}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Executions
                  </Typography>
                  <Typography variant="h6">{service.executions}</Typography>
                </Grid>
              </Grid>
            )}

            {service.name === 'RDS' && (
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Databases
                  </Typography>
                  <Typography variant="h6">{service.databases}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Storage
                  </Typography>
                  <Typography variant="h6">{service.storage}</Typography>
                </Grid>
              </Grid>
            )}

            {service.name === 'IAM' && (
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Users
                  </Typography>
                  <Typography variant="h6">{service.users}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Roles
                  </Typography>
                  <Typography variant="h6">{service.roles}</Typography>
                </Grid>
              </Grid>
            )}
          </Box>

          {/* Cost */}
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="body2" color="text.secondary">
              Monthly Cost
            </Typography>
            <Typography variant="h6" fontWeight="bold" color="primary.main">
              {service.cost}
            </Typography>
          </Box>

          {/* Actions */}
          <Box display="flex" gap={1}>
            <Tooltip title="Open AWS Console">
              <IconButton
                size="small"
                onClick={() => handleAction('view')}
                disabled={loading}
                color="primary"
              >
                <Launch />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Manage Service">
              <IconButton
                size="small"
                onClick={() => handleAction('monitor')}
                disabled={loading}
                color="info"
              >
                <Monitor />
              </IconButton>
            </Tooltip>
            
            <Tooltip title="Service Settings">
              <IconButton
                size="small"
                onClick={() => handleAction('settings')}
                disabled={loading}
                color="secondary"
              >
                <Settings />
              </IconButton>
            </Tooltip>

            {service.status === 'active' ? (
              <Tooltip title="Stop Service">
                <IconButton
                  size="small"
                  onClick={() => handleAction('stop')}
                  disabled={loading}
                  color="error"
                >
                  <Stop />
                </IconButton>
              </Tooltip>
            ) : (
              <Tooltip title="Start Service">
                <IconButton
                  size="small"
                  onClick={() => handleAction('start')}
                  disabled={loading}
                  color="success"
                >
                  <PlayArrow />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

const AWSServices = () => {
  const { credentials, checkCredentials, getServiceStats } = useAWS();
  const location = useLocation();
  const [services, setServices] = useState(awsServices);
  const [realStats, setRealStats] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [credentialsDialog, setCredentialsDialog] = useState(false);
  const [serviceDialog, setServiceDialog] = useState({ open: false, service: null });
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    checkCredentials();
  }, []);

  useEffect(() => {
    if (credentials?.has_credentials) {
      loadRealStats();
    }
  }, [credentials]);

  // Handle navigation state for opening EC2 dialog with specific tab
  useEffect(() => {
    if (location.state?.activeTab !== undefined) {
      setServiceDialog({ open: true, service: 'EC2' });
      setTabValue(location.state.activeTab);
      // Clear the state so it doesn't reopen on future navigations
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const loadRealStats = async () => {
    try {
      const stats = await getServiceStats();
      setRealStats(stats);
      updateServicesWithRealData(stats);
    } catch (error) {
      console.error('Failed to load real AWS stats:', error);
    }
  };

  const updateServicesWithRealData = (stats) => {
    if (!stats?.services) return;

    const updatedServices = services.map(service => {
      const serviceKey = service.name.toLowerCase();
      const serviceStats = stats.services[serviceKey];
      
      if (!serviceStats) return service;

      switch (service.name) {
        case 'EC2':
          return {
            ...service,
            status: serviceStats.status || 'inactive',
            instances: serviceStats.instances || 0,
            running: serviceStats.running || 0,
            stopped: serviceStats.stopped || 0,
            cost: serviceStats.cost || '$0.00'
          };
        case 'S3':
          return {
            ...service,
            status: serviceStats.status || 'inactive',
            buckets: serviceStats.buckets || 0,
            objects: serviceStats.objects || '0',
            storage: serviceStats.storage || '0 GB',
            cost: serviceStats.cost || '$0.00'
          };
        case 'Lambda':
          return {
            ...service,
            status: serviceStats.status || 'inactive',
            functions: serviceStats.functions || 0,
            executions: serviceStats.executions || '0',
            errors: serviceStats.errors || 0,
            cost: serviceStats.cost || '$0.00'
          };
        case 'RDS':
          return {
            ...service,
            status: serviceStats.status || 'inactive',
            databases: serviceStats.databases || 0,
            connections: serviceStats.connections || 0,
            storage: serviceStats.storage || '0 GB',
            cost: serviceStats.cost || '$0.00'
          };
        case 'IAM':
          return {
            ...service,
            status: serviceStats.status || 'active',
            users: serviceStats.users || 0,
            roles: serviceStats.roles || 0,
            policies: serviceStats.policies || 0,
            cost: serviceStats.cost || '$0.00'
          };
        case 'Bedrock':
          return {
            ...service,
            status: serviceStats.status || 'inactive',
            models: serviceStats.models || 0,
            requests: serviceStats.requests || 0,
            tokens: serviceStats.tokens || 0,
            cost: serviceStats.cost || '$0.00'
          };
        default:
          return service;
      }
    });

    setServices(updatedServices);
  };

  const handleServiceAction = (serviceName, action) => {
    if (!credentials || !credentials.has_credentials) {
      setCredentialsDialog(true);
      return;
    }

    if (action === 'view') {
      setServiceDialog({ open: true, service: serviceName });
    } else {
      console.log(`Action ${action} on service ${serviceName}`);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await checkCredentials();
    if (credentials?.has_credentials) {
      await loadRealStats();
    }
    setTimeout(() => {
      setRefreshing(false);
    }, 1000);
  };

  const handleCredentialsSuccess = () => {
    checkCredentials();
  };

  const activeServices = services.filter(s => s.status === 'active').length;
  const totalCost = services.reduce((sum, s) => sum + parseFloat(s.cost.replace('$', '')), 0);

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" fontWeight="bold">
              AWS Services
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage and monitor your AWS infrastructure
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
      </motion.div>

      {/* Summary Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1, duration: 0.5 }}
      >
        <Grid container spacing={3} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Active Services
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  {activeServices}
                </Typography>
                <Typography variant="body2" color="success.main">
                  of {services.length} total
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Total Monthly Cost
                </Typography>
                <Typography variant="h4" fontWeight="bold">
                  ${totalCost.toFixed(2)}
                </Typography>
                <Typography variant="body2" color="info.main">
                  Current month
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Security Status
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="success.main">
                  Secure
                </Typography>
                <Typography variant="body2" color="success.main">
                  All checks passed
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  Performance
                </Typography>
                <Typography variant="h4" fontWeight="bold" color="warning.main">
                  Good
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Some optimization available
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </motion.div>

      {/* AWS Credentials Alert */}
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
                onClick={() => setCredentialsDialog(true)}
              >
                Setup Credentials
              </Button>
            }
          >
            <Typography variant="body2">
              🔑 <strong>AWS Credentials Required:</strong> Configure your AWS credentials to manage your infrastructure through the dashboard.
            </Typography>
          </Alert>
        </motion.div>
      )}

      {credentials?.has_credentials && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <Alert severity="success" sx={{ mb: 3 }}>
            <Typography variant="body2">
              ✅ <strong>AWS Connected:</strong> Account {credentials.account_info?.account_id} connected successfully. 
              Region: {credentials.region}
              {!realStats && ' (Loading real-time data...)'}
            </Typography>
          </Alert>
        </motion.div>
      )}

      {/* Services Grid */}
      <Grid container spacing={3}>
        {services.map((service, index) => (
          <Grid item xs={12} sm={6} md={4} key={service.name}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 + index * 0.1, duration: 0.5 }}
            >
              <ServiceCard 
                service={service} 
                onAction={handleServiceAction}
              />
            </motion.div>
          </Grid>
        ))}
      </Grid>

      {/* AWS Credentials Setup Dialog */}
      <AWSCredentialsSetup
        open={credentialsDialog}
        onClose={() => setCredentialsDialog(false)}
        onSuccess={handleCredentialsSuccess}
      />

      {/* Service Detail Dialog */}
      <Dialog
        open={serviceDialog.open}
        onClose={() => setServiceDialog({ open: false, service: null })}
        maxWidth="xl"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              {serviceDialog.service} Management
            </Typography>
            <Button
              onClick={() => setServiceDialog({ open: false, service: null })}
            >
              Close
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {serviceDialog.service === 'EC2' && (
            <Box>
              <Tabs 
                value={tabValue} 
                onChange={(e, newValue) => setTabValue(newValue)}
                sx={{ borderBottom: 1, borderColor: 'divider', px: 3 }}
              >
                <Tab label="Instances" />
                <Tab label="Security Groups" />
                <Tab label="Key Pairs" />
                <Tab label="AMIs" />
              </Tabs>
              <Box sx={{ p: 0 }}>
                {tabValue === 0 && <EC2Instances />}
                {tabValue === 1 && <SecurityGroupManagement />}
                {tabValue === 2 && <KeyPairManagement />}
                {tabValue === 3 && <AMIManagement />}
              </Box>
            </Box>
          )}
          
          {serviceDialog.service && serviceDialog.service !== 'EC2' && (
            <Box p={3} textAlign="center">
              <Typography variant="h6" gutterBottom>
                {serviceDialog.service} Integration
              </Typography>
              <Typography color="text.secondary">
                {serviceDialog.service} service integration is coming in the next phase.
                Focus on EC2 functionality for now.
              </Typography>
            </Box>
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default AWSServices;
