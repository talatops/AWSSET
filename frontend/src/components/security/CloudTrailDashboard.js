import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Divider,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Security,
  Warning,
  CheckCircle,
  Error,
  Refresh,
  Search,
  Analytics,
  Timeline,
  Visibility,
  VisibilityOff,
  Download,
  FileDownload
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useWebSocket } from '../../contexts/WebSocketContext';
import { toast } from 'react-toastify';

const CloudTrailDashboard = () => {
  const { api } = useAuth();
  const { connected: wsConnected, sendMessage } = useWebSocket();
  const [loading, setLoading] = useState(false);
  const [cloudtrailStatus, setCloudtrailStatus] = useState({
    connected: false,
    status: 'checking',
    message: 'Checking CloudTrail connection...',
    trails: [],
    lastChecked: null
  });
  const [events, setEvents] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [securityAnalysis, setSecurityAnalysis] = useState(null);
  const [anomalyResults, setAnomalyResults] = useState(null);
  const [costAnalysis, setCostAnalysis] = useState(null);
  const [comprehensiveReport, setComprehensiveReport] = useState(null);
  const [selectedTab, setSelectedTab] = useState(0);
  const [timeRange, setTimeRange] = useState('24h');
  const [searchQuery, setSearchQuery] = useState('');
  const [analysisDialog, setAnalysisDialog] = useState(false);
  const [analysisType, setAnalysisType] = useState('');
  
  // Advanced filtering
  const [filters, setFilters] = useState({
    eventNames: [],
    userIdentities: [],
    sourceIPs: [],
    readOnly: null,
    managementEvent: null
  });
  
  // Real-time updates
  const [realTimeEnabled, setRealTimeEnabled] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // Export functionality
  const [exportLoading, setExportLoading] = useState(false);

  // Time range options
  const timeRanges = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ];

  useEffect(() => {
    checkCloudTrailStatus();
  }, []);

  useEffect(() => {
    if (cloudtrailStatus.connected) {
      loadCloudTrailData();
    }
  }, [timeRange, cloudtrailStatus.connected]);

  // Real-time updates effect
  useEffect(() => {
    let interval;
    if (realTimeEnabled && cloudtrailStatus.connected) {
      interval = setInterval(() => {
        loadCloudTrailData();
        setLastUpdate(new Date().toISOString());
      }, 30000); // Update every 30 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [realTimeEnabled, cloudtrailStatus.connected]);

  // WebSocket real-time CloudTrail updates
  useEffect(() => {
    if (wsConnected && realTimeEnabled && cloudtrailStatus.connected) {
      // Subscribe to CloudTrail real-time updates
      sendMessage({
        type: 'subscribe_cloudtrail_updates',
        data: { enabled: true }
      });
      
      return () => {
        // Unsubscribe when component unmounts
        sendMessage({
          type: 'unsubscribe_cloudtrail_updates',
          data: { enabled: false }
        });
      };
    }
  }, [wsConnected, realTimeEnabled, cloudtrailStatus.connected, sendMessage]);

  const checkCloudTrailStatus = async () => {
    try {
      setCloudtrailStatus(prev => ({
        ...prev,
        status: 'checking',
        message: 'Checking CloudTrail connection...'
      }));

      const response = await api.get('/api/cloudtrail/status');
      
      if (response.data.success) {
        const trails = response.data.trails || [];
        const hasTrails = trails.length > 0;
        
        setCloudtrailStatus({
          connected: hasTrails,
          status: hasTrails ? 'connected' : 'no_trails',
          message: hasTrails 
            ? `Connected to ${trails.length} CloudTrail trail(s)` 
            : 'No CloudTrail trails found. Please enable CloudTrail in your AWS account.',
          trails: trails,
          lastChecked: new Date().toISOString()
        });
      } else {
        setCloudtrailStatus({
          connected: false,
          status: 'error',
          message: response.data.error || 'Failed to check CloudTrail status',
          trails: [],
          lastChecked: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Failed to check CloudTrail status:', error);
      
      let errorMessage = 'Failed to connect to CloudTrail';
      if (error.response?.status === 401) {
        errorMessage = 'Authentication required. Please check your AWS credentials.';
      } else if (error.response?.status === 403) {
        errorMessage = 'Access denied. Insufficient permissions for CloudTrail.';
      } else if (error.response?.status === 404) {
        errorMessage = 'CloudTrail service not found. Please check your AWS region.';
      }
      
      setCloudtrailStatus({
        connected: false,
        status: 'error',
        message: errorMessage,
        trails: [],
        lastChecked: new Date().toISOString()
      });
    }
  };

  const loadCloudTrailData = async () => {
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }

    try {
      setLoading(true);
      
      // Load events
      const eventsResponse = await api.get(`/api/cloudtrail/events?max_results=100`);
      if (eventsResponse.data.success) {
        setEvents(eventsResponse.data.events);
      }
      
      // Load statistics
      const statsResponse = await api.get(`/api/cloudtrail/events/statistics`);
      if (statsResponse.data.success) {
        setStatistics(statsResponse.data.statistics);
      }
      
    } catch (error) {
      console.error('Failed to load CloudTrail data:', error);
      toast.error('Failed to load CloudTrail data');
    } finally {
      setLoading(false);
    }
  };

  const runSecurityAnalysis = async () => {
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }

    try {
      setLoading(true);
      setAnalysisType('security');
      setAnalysisDialog(true);
      
      const response = await api.post('/api/cloudtrail/analysis/security');
      if (response.data.success) {
        setSecurityAnalysis(response.data);
        toast.success('Security analysis completed');
      } else {
        toast.error('Security analysis failed');
      }
    } catch (error) {
      console.error('Security analysis failed:', error);
      toast.error('Security analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const detectAnomalies = async () => {
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }

    try {
      setLoading(true);
      setAnalysisType('anomalies');
      setAnalysisDialog(true);
      
      const response = await api.post('/api/cloudtrail/analysis/anomalies');
      if (response.data.success) {
        setAnomalyResults(response.data);
        toast.success('Anomaly detection completed');
      } else {
        toast.error('Anomaly detection failed');
      }
    } catch (error) {
      console.error('Anomaly detection failed:', error);
      toast.error('Anomaly detection failed');
      setLoading(false);
    }
  };

  const analyzeCosts = async () => {
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }

    try {
      setLoading(true);
      setAnalysisType('costs');
      setAnalysisDialog(true);
      
      const response = await api.post('/api/cloudtrail/analysis/costs');
      if (response.data.success) {
        setCostAnalysis(response.data);
        toast.success('Cost analysis completed');
      } else {
        toast.error('Cost analysis failed');
      }
    } catch (error) {
      console.error('Cost analysis failed:', error);
      toast.error('Cost analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const generateComprehensiveReport = async () => {
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }

    try {
      setLoading(true);
      setAnalysisType('complete');
      setAnalysisDialog(true);
      
      const response = await api.post('/api/cloudtrail/analysis/comprehensive');
      if (response.data.success) {
        setComprehensiveReport(response.data);
        toast.success('Comprehensive report generated');
      } else {
        toast.error('Report generation failed');
      }
    } catch (error) {
      console.error('Report generation failed:', error);
      toast.error('Report generation failed');
    } finally {
      setLoading(false);
    }
  };

  const searchEvents = async () => {
    if (!searchQuery.trim()) return;
    
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }
    
    try {
      setLoading(true);
      const response = await api.get(`/api/cloudtrail/events/search?query=${encodeURIComponent(searchQuery)}`);
      if (response.data.success) {
        setEvents(response.data.events);
        toast.success(`Found ${response.data.total_events} events`);
      } else {
        toast.error('Search failed');
      }
    } catch (error) {
      console.error('Search failed:', error);
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const applyAdvancedFilters = async () => {
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }

    try {
      setLoading(true);
      
      // Build filter parameters
      const filterParams = new URLSearchParams();
      if (filters.eventNames.length > 0) {
        filters.eventNames.forEach(name => filterParams.append('event_names', name));
      }
      if (filters.userIdentities.length > 0) {
        filters.userIdentities.forEach(identity => filterParams.append('user_identities', identity));
      }
      if (filters.sourceIPs.length > 0) {
        filters.sourceIPs.forEach(ip => filterParams.append('source_ips', ip));
      }
      if (filters.readOnly !== null) {
        filterParams.append('read_only', filters.readOnly);
      }
      if (filters.managementEvent !== null) {
        filterParams.append('management_event', filters.managementEvent);
      }

      const response = await api.get(`/api/cloudtrail/events?${filterParams.toString()}`);
      if (response.data.success) {
        setEvents(response.data.events);
        toast.success(`Filtered ${response.data.total_events} events`);
      } else {
        toast.error('Filtering failed');
      }
    } catch (error) {
      console.error('Advanced filtering failed:', error);
      toast.error('Advanced filtering failed');
    } finally {
      setLoading(false);
    }
  };

  const exportData = async (format = 'json') => {
    if (!cloudtrailStatus.connected) {
      toast.warning('CloudTrail is not connected. Please check the connection status.');
      return;
    }

    try {
      setExportLoading(true);
      
      if (format === 'json') {
        // Export as JSON
        const data = {
          events: events,
          statistics: statistics,
          filters: filters,
          timeRange: timeRange,
          exportDate: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cloudtrail-events-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        toast.success('Data exported as JSON successfully');
      } else if (format === 'csv') {
        // Export as CSV
        const csvContent = convertToCSV(events);
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `cloudtrail-events-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        toast.success('Data exported as CSV successfully');
      }
    } catch (error) {
      console.error('Export failed:', error);
      toast.error('Export failed');
    } finally {
      setExportLoading(false);
    }
  };

  const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';
    
    const headers = ['Event ID', 'Event Name', 'Event Source', 'Event Time', 'User Identity', 'Source IP', 'AWS Region', 'Read Only', 'Management Event'];
    const rows = data.map(event => [
      event.event_id || '',
      event.event_name || '',
      event.event_source || '',
      event.event_time || '',
      event.user_identity || '',
      event.source_ip_address || '',
      event.aws_region || '',
      event.read_only ? 'Yes' : 'No',
      event.management_event ? 'Yes' : 'No'
    ]);
    
    return [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
  };

  const getRiskColor = (riskScore) => {
    if (riskScore >= 0.7) return 'error';
    if (riskScore >= 0.4) return 'warning';
    return 'success';
  };

  const getRiskLabel = (riskScore) => {
    if (riskScore >= 0.7) return 'High Risk';
    if (riskScore >= 0.4) return 'Medium Risk';
    return 'Low Risk';
  };

  const renderSecurityOverview = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Security color="primary" /> Security Status
            </Typography>
            {statistics ? (
              <Box>
                <Typography variant="h4" color="primary">
                  {statistics.suspicious_events}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Suspicious Events Detected
                </Typography>
                <Box mt={2}>
                  <Typography variant="body2">
                    High Risk: {statistics.risk_distribution?.high || 0}
                  </Typography>
                  <Typography variant="body2">
                    Medium Risk: {statistics.risk_distribution?.medium || 0}
                  </Typography>
                  <Typography variant="body2">
                    Low Risk: {statistics.risk_distribution?.low || 0}
                  </Typography>
                </Box>
              </Box>
            ) : (
              <CircularProgress size={20} />
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              <Analytics color="primary" /> Cost Impact
            </Typography>
            {statistics ? (
              <Box>
                <Typography variant="h4" color="error">
                  ${statistics.cost_impact?.toFixed(2) || '0.00'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Estimated Cost Impact
                </Typography>
                <Box mt={2}>
                  <Typography variant="body2">
                    Total Events: {statistics.total_events}
                  </Typography>
                  <Typography variant="body2">
                    Event Types: {Object.keys(statistics.event_types || {}).length}
                  </Typography>
                </Box>
              </Box>
            ) : (
              <CircularProgress size={20} />
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderEventsTable = () => (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Recent CloudTrail Events
          </Typography>
          <Box>
            <TextField
              size="small"
              placeholder="Search events..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchEvents()}
              InputProps={{
                endAdornment: (
                  <IconButton onClick={searchEvents}>
                    <Search />
                  </IconButton>
                )
              }}
            />
          </Box>
        </Box>

        {/* Advanced Filters */}
        <Box mb={3}>
          <Typography variant="subtitle2" gutterBottom>Advanced Filters</Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                size="small"
                label="Event Names"
                placeholder="e.g., CreateInstance, DeleteBucket"
                value={filters.eventNames.join(', ')}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  eventNames: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                }))}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                size="small"
                label="User Identities"
                placeholder="e.g., admin, user123"
                value={filters.userIdentities.join(', ')}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  userIdentities: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                }))}
                fullWidth
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl size="small" fullWidth>
                <InputLabel>Read Only</InputLabel>
                <Select
                  value={filters.readOnly || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, readOnly: e.target.value || null }))}
                  label="Read Only"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="true">Read Only</MenuItem>
                  <MenuItem value="false">Write Operations</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl size="small" fullWidth>
                <InputLabel>Event Type</InputLabel>
                <Select
                  value={filters.managementEvent || ''}
                  onChange={(e) => setFilters(prev => ({ ...prev, managementEvent: e.target.value || null }))}
                  label="Event Type"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="true">Management</MenuItem>
                  <MenuItem value="false">Data</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <Button
                variant="contained"
                onClick={applyAdvancedFilters}
                disabled={loading}
                fullWidth
              >
                Apply Filters
              </Button>
            </Grid>
          </Grid>
        </Box>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Event</TableCell>
                <TableCell>User</TableCell>
                <TableCell>Source IP</TableCell>
                <TableCell>Time</TableCell>
                <TableCell>Risk Score</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {events.slice(0, 20).map((event, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {event.event_name}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {event.event_source}
                    </Typography>
                  </TableCell>
                  <TableCell>{event.user_identity}</TableCell>
                  <TableCell>{event.source_ip_address}</TableCell>
                  <TableCell>
                    {new Date(event.event_time).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getRiskLabel(event.risk_score)}
                      color={getRiskColor(event.risk_score)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {event.suspicious ? (
                      <Chip icon={<Warning />} label="Suspicious" color="error" size="small" />
                    ) : (
                      <Chip icon={<CheckCircle />} label="Normal" color="success" size="small" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardContent>
    </Card>
  );

  const renderAnalysisResults = () => {
    const currentAnalysis = analysisType === 'security' ? securityAnalysis :
                           analysisType === 'anomalies' ? anomalyResults :
                           analysisType === 'costs' ? costAnalysis :
                           comprehensiveReport;

    if (!currentAnalysis) return null;

    return (
      <Dialog open={analysisDialog} onClose={() => setAnalysisDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {analysisType === 'security' && 'Security Analysis Results'}
          {analysisType === 'anomalies' && 'Anomaly Detection Results'}
          {analysisType === 'costs' && 'Cost Analysis Results'}
          {analysisType === 'comprehensive' && 'Comprehensive Security Report'}
        </DialogTitle>
        <DialogContent>
          <Box mt={2}>
            {currentAnalysis.parsed === false ? (
              <Alert severity="warning">
                AI response could not be parsed. Raw response:
                <pre style={{ whiteSpace: 'pre-wrap', marginTop: '10px' }}>
                  {currentAnalysis.ai_response}
                </pre>
              </Alert>
            ) : (
              <Box>
                {currentAnalysis.security_risk_score && (
                  <Box mb={2}>
                    <Typography variant="h6">Security Risk Score</Typography>
                    <Typography variant="h3" color="error">
                      {currentAnalysis.security_risk_score}/100
                    </Typography>
                  </Box>
                )}
                
                {currentAnalysis.key_findings && (
                  <Box mb={2}>
                    <Typography variant="h6">Key Findings</Typography>
                    <ul>
                      {currentAnalysis.key_findings.map((finding, index) => (
                        <li key={index}>{finding}</li>
                      ))}
                    </ul>
                  </Box>
                )}
                
                {currentAnalysis.recommended_actions && (
                  <Box mb={2}>
                    <Typography variant="h6">Recommended Actions</Typography>
                    <ul>
                      {currentAnalysis.recommended_actions.map((action, index) => (
                        <li key={index}>{action}</li>
                      ))}
                    </ul>
                  </Box>
                )}
                
                {currentAnalysis.executive_summary && (
                  <Box mb={2}>
                    <Typography variant="h6">Executive Summary</Typography>
                    <Typography variant="body1">
                      {currentAnalysis.executive_summary}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAnalysisDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" component="h1">
            <Security color="primary" /> CloudTrail Security Dashboard
          </Typography>
          <Box>
            <FormControl size="small" sx={{ minWidth: 120, mr: 2 }}>
              <InputLabel>Time Range</InputLabel>
              <Select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                label="Time Range"
              >
                {timeRanges.map((range) => (
                  <MenuItem key={range.value} value={range.value}>
                    {range.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={loadCloudTrailData}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
        </Box>

        {/* CloudTrail Connection Status */}
        <Card sx={{ mb: 3, backgroundColor: cloudtrailStatus.status === 'error' ? '#fff3e0' : '#f3f4f6' }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box display="flex" alignItems="center" gap={2}>
                {cloudtrailStatus.status === 'checking' && (
                  <CircularProgress size={20} />
                )}
                {cloudtrailStatus.status === 'connected' && (
                  <CheckCircle color="success" />
                )}
                {cloudtrailStatus.status === 'no_trails' && (
                  <Warning color="warning" />
                )}
                {cloudtrailStatus.status === 'error' && (
                  <Error color="error" />
                )}
                
                <Box>
                  <Typography variant="h6" gutterBottom>
                    CloudTrail Connection Status
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {cloudtrailStatus.message}
                  </Typography>
                  {cloudtrailStatus.trails.length > 0 && (
                    <Box mt={1}>
                      <Typography variant="body2" color="text.secondary">
                        Active Trails: {cloudtrailStatus.trails.map(trail => trail.Name).join(', ')}
                      </Typography>
                    </Box>
                  )}
                  {cloudtrailStatus.lastChecked && (
                    <Typography variant="caption" color="text.secondary">
                      Last checked: {new Date(cloudtrailStatus.lastChecked).toLocaleString()}
                    </Typography>
                  )}
                </Box>
              </Box>
              
              <Box>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={checkCloudTrailStatus}
                  disabled={cloudtrailStatus.status === 'checking'}
                  size="small"
                >
                  Check Status
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>

        {/* Advanced Controls */}
        {cloudtrailStatus.connected && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Advanced Controls</Typography>
                <Box display="flex" gap={1}>
                  <Button
                    variant={realTimeEnabled ? "contained" : "outlined"}
                    color="primary"
                    size="small"
                    onClick={() => setRealTimeEnabled(!realTimeEnabled)}
                    startIcon={<Refresh />}
                  >
                    {realTimeEnabled ? 'Real-time ON' : 'Real-time OFF'}
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => exportData('json')}
                    disabled={exportLoading}
                  >
                    Export JSON
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => exportData('csv')}
                    disabled={exportLoading}
                  >
                    Export CSV
                  </Button>
                </Box>
              </Box>
              
              {realTimeEnabled && lastUpdate && (
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Last update: {new Date(lastUpdate).toLocaleString()}
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1} mt={1}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        backgroundColor: wsConnected ? 'success.main' : 'error.main'
                      }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {wsConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
                    </Typography>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        )}

        <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="Overview" />
          <Tab label="Events" />
          <Tab label="Analysis" />
        </Tabs>

        {selectedTab === 0 && (
          <Box>
            {!cloudtrailStatus.connected ? (
              <Card sx={{ p: 3, textAlign: 'center', backgroundColor: '#f5f5f5' }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  CloudTrail Not Connected
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {cloudtrailStatus.message}
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Refresh />}
                  onClick={checkCloudTrailStatus}
                  disabled={cloudtrailStatus.status === 'checking'}
                >
                  Retry Connection
                </Button>
              </Card>
            ) : (
              <>
                {renderSecurityOverview()}
                
                <Box mt={3}>
                  <Typography variant="h6" gutterBottom>
                    Quick Actions
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<Security />}
                        onClick={runSecurityAnalysis}
                        disabled={loading}
                      >
                        Run Security Analysis
                      </Button>
                    </Grid>
                    <Grid item>
                      <Button
                        variant="contained"
                        color="warning"
                        startIcon={<Warning />}
                        onClick={detectAnomalies}
                        disabled={loading}
                      >
                        Detect Anomalies
                      </Button>
                    </Grid>
                    <Grid item>
                      <Button
                        variant="contained"
                        color="info"
                        startIcon={<Analytics />}
                        onClick={analyzeCosts}
                        disabled={loading}
                      >
                        Analyze Costs
                      </Button>
                    </Grid>
                    <Grid item>
                      <Button
                        variant="contained"
                        color="secondary"
                        startIcon={<Timeline />}
                        onClick={generateComprehensiveReport}
                        disabled={loading}
                      >
                        Generate Report
                      </Button>
                    </Grid>
                  </Grid>
                </Box>
              </>
            )}
          </Box>
        )}

        {selectedTab === 1 && (
          !cloudtrailStatus.connected ? (
            <Card sx={{ p: 3, textAlign: 'center', backgroundColor: '#f5f5f5' }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                CloudTrail Not Connected
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                {cloudtrailStatus.message}
              </Typography>
              <Button
                variant="contained"
                startIcon={<Refresh />}
                onClick={checkCloudTrailStatus}
                disabled={cloudtrailStatus.status === 'checking'}
              >
                Retry Connection
              </Button>
            </Card>
          ) : (
            renderEventsTable()
          )
        )}

        {selectedTab === 2 && (
          <Box>
            {!cloudtrailStatus.connected ? (
              <Card sx={{ p: 3, textAlign: 'center', backgroundColor: '#f5f5f5' }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  CloudTrail Not Connected
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {cloudtrailStatus.message}
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Refresh />}
                  onClick={checkCloudTrailStatus}
                  disabled={cloudtrailStatus.status === 'checking'}
                >
                  Retry Connection
                </Button>
              </Card>
            ) : (
              <>
                <Typography variant="h6" gutterBottom>
                  AI-Powered Analysis
                </Typography>
                <Typography variant="body2" color="textSecondary" paragraph>
                  Use AI to analyze your CloudTrail events for security threats, anomalies, and cost implications.
                </Typography>
                
                <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Security Analysis
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Analyze events for security threats, unauthorized access, and suspicious activity.
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={runSecurityAnalysis}
                      disabled={loading}
                      fullWidth
                    >
                      Run Analysis
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Anomaly Detection
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Detect unusual patterns and behavior in your CloudTrail events.
                    </Typography>
                    <Button
                      variant="contained"
                      color="warning"
                      onClick={detectAnomalies}
                      disabled={loading}
                      fullWidth
                    >
                      Detect Anomalies
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Cost Analysis
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Analyze events for cost implications and optimization opportunities.
                    </Typography>
                    <Button
                      variant="contained"
                      color="info"
                      onClick={analyzeCosts}
                      disabled={loading}
                      fullWidth
                    >
                      Analyze Costs
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Comprehensive Report
                    </Typography>
                    <Typography variant="body2" color="textSecondary" paragraph>
                      Generate a complete security report with all analysis types.
                    </Typography>
                    <Button
                      variant="contained"
                      color="secondary"
                      onClick={generateComprehensiveReport}
                      disabled={loading}
                      fullWidth
                    >
                      Generate Report
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
                </>
              )}
          </Box>
        )}

        {renderAnalysisResults()}
      </motion.div>
    </Box>
  );
};

export default CloudTrailDashboard;
