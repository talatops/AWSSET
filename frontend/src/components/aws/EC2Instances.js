import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Grid,
  Alert,
  CircularProgress,
  Tooltip,
  Fab,
  Badge,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Delete,
  MoreVert,
  Add,
  Computer,
  Storage,
  Security,
  VpnKey,
  Refresh as RefreshIcon,
  FilterList,
  Info,
  ContentCopy,
  CheckCircle,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useEC2 } from '../../hooks/useAWS';
import { toast } from 'react-toastify';

const EC2Instances = () => {
  const {
    loading,
    error,
    listInstances,
    startInstance,
    stopInstance,
    rebootInstance,
    terminateInstance,
    createInstance,
    listSecurityGroups,
    listKeyPairs,
    listAMIs,
  } = useEC2();

  const [instances, setInstances] = useState([]);
  const [filters, setFilters] = useState({ state: '', tag: '' });
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedInstance, setSelectedInstance] = useState(null);
  const [createDialog, setCreateDialog] = useState(false);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: '', instance: null });
  const [detailsDialog, setDetailsDialog] = useState(false);
  
  // Resources for instance creation
  const [securityGroups, setSecurityGroups] = useState([]);
  const [keyPairs, setKeyPairs] = useState([]);
  const [amis, setAMIs] = useState([]);
  
  // New instance form
  const [newInstance, setNewInstance] = useState({
    name: '',
    image_id: '',
    instance_type: 't2.micro',
    key_name: '',
    security_group_ids: [],
  });

  useEffect(() => {
    loadInstances();
  }, []);

  const loadInstances = async () => {
    try {
      const result = await listInstances(filters);
      setInstances(result.instances || []);
    } catch (error) {
      console.error('Failed to load instances:', error);
    }
  };

  const loadResources = async () => {
    try {
      const [sgResult, kpResult, amiResult] = await Promise.all([
        listSecurityGroups(),
        listKeyPairs(),
        listAMIs({ name: 'amzn2' }) // Amazon Linux 2
      ]);
      
      setSecurityGroups(sgResult.security_groups || []);
      setKeyPairs(kpResult.key_pairs || []);
      setAMIs(amiResult.amis || []);
    } catch (error) {
      console.error('Failed to load resources:', error);
    }
  };

  const handleMenuOpen = (event, instance) => {
    setAnchorEl(event.currentTarget);
    setSelectedInstance(instance);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedInstance(null);
  };

  const handleViewDetails = () => {
    setDetailsDialog(true);
    handleMenuClose();
  };

  const handleAction = async (action, instance, force = false) => {
    try {
      switch (action) {
        case 'start':
          await startInstance(instance.instance_id);
          break;
        case 'stop':
          await stopInstance(instance.instance_id, force);
          break;
        case 'reboot':
          await rebootInstance(instance.instance_id);
          break;
        case 'terminate':
          await terminateInstance(instance.instance_id);
          break;
      }
      
      // Refresh instances after action
      setTimeout(loadInstances, 1000);
      handleMenuClose();
      setConfirmDialog({ open: false, action: '', instance: null });
    } catch (error) {
      console.error(`Failed to ${action} instance:`, error);
    }
  };

  const handleCreateInstance = async () => {
    try {
      await createInstance(newInstance);
      setCreateDialog(false);
      setNewInstance({
        name: '',
        image_id: '',
        instance_type: 't2.micro',
        key_name: '',
        security_group_ids: [],
      });
      
      // Refresh instances
      setTimeout(loadInstances, 2000);
    } catch (error) {
      console.error('Failed to create instance:', error);
    }
  };

  const openCreateDialog = () => {
    setCreateDialog(true);
    loadResources();
  };

  const getStateColor = (state) => {
    const colors = {
      running: 'success',
      stopped: 'default',
      stopping: 'warning',
      starting: 'info',
      pending: 'info',
      terminating: 'error',
      terminated: 'error',
    };
    return colors[state] || 'default';
  };

  const canPerformAction = (state, action) => {
    const allowedActions = {
      running: ['stop', 'reboot', 'terminate'],
      stopped: ['start', 'terminate'],
      stopping: [],
      starting: [],
      pending: [],
      terminating: [],
      terminated: [],
    };
    return allowedActions[state]?.includes(action) || false;
  };

  const formatUptime = (launchTime) => {
    if (!launchTime) return 'N/A';
    const now = new Date();
    const launch = new Date(launchTime);
    const diff = now - launch;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    return `${days}d ${hours}h`;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            EC2 Instances
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage your AWS EC2 virtual machines
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadInstances}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={openCreateDialog}
          >
            Launch Instance
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center">
            <FilterList color="action" />
            <Typography variant="subtitle2">Filters:</Typography>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>State</InputLabel>
              <Select
                value={filters.state}
                onChange={(e) => setFilters(prev => ({ ...prev, state: e.target.value }))}
                label="State"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="running">Running</MenuItem>
                <MenuItem value="stopped">Stopped</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="terminating">Terminating</MenuItem>
              </Select>
            </FormControl>
            <TextField
              size="small"
              label="Tag (key:value)"
              value={filters.tag}
              onChange={(e) => setFilters(prev => ({ ...prev, tag: e.target.value }))}
              placeholder="Name:web-server"
            />
            <Button variant="outlined" onClick={loadInstances} disabled={loading}>
              Apply
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Instance Table */}
      <Card>
        <CardContent>
          {loading && instances.length === 0 ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Instance ID</TableCell>
                    <TableCell>State</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Public IP</TableCell>
                    <TableCell>Private IP</TableCell>
                    <TableCell>Uptime</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {instances.map((instance) => (
                    <TableRow
                      key={instance.instance_id}
                      hover
                      component={motion.tr}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Computer color="action" />
                          {instance.name || 'Unnamed'}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {instance.instance_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={instance.state}
                          color={getStateColor(instance.state)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{instance.instance_type}</TableCell>
                      <TableCell>
                        {instance.public_ip ? (
                          <Typography variant="body2" fontFamily="monospace">
                            {instance.public_ip}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            -
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {instance.private_ip || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {formatUptime(instance.launch_time)}
                      </TableCell>
                      <TableCell>
                        <Box display="flex" gap={1}>
                          {canPerformAction(instance.state, 'start') && (
                            <Tooltip title="Start Instance">
                              <IconButton
                                size="small"
                                color="success"
                                onClick={() => handleAction('start', instance)}
                              >
                                <PlayArrow />
                              </IconButton>
                            </Tooltip>
                          )}
                          
                          {canPerformAction(instance.state, 'stop') && (
                            <Tooltip title="Stop Instance">
                              <IconButton
                                size="small"
                                color="warning"
                                onClick={() => setConfirmDialog({
                                  open: true,
                                  action: 'stop',
                                  instance: instance
                                })}
                              >
                                <Stop />
                              </IconButton>
                            </Tooltip>
                          )}

                          {/* Quick Connect Button for Running Instances */}
                          {instance.state === 'running' && instance.public_ip && instance.key_name && (
                            <Tooltip title="Copy SSH Command">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={() => {
                                  const command = `ssh -i ${instance.key_name}-private.pem ec2-user@${instance.public_ip}`;
                                  navigator.clipboard.writeText(command);
                                  toast.success('SSH command copied to clipboard!');
                                }}
                              >
                                <ContentCopy />
                              </IconButton>
                            </Tooltip>
                          )}

                          <IconButton
                            size="small"
                            onClick={(e) => handleMenuOpen(e, instance)}
                          >
                            <MoreVert />
                          </IconButton>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {instances.length === 0 && !loading && (
                <Box textAlign="center" p={4}>
                  <Typography variant="h6" color="text.secondary">
                    No instances found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Launch your first EC2 instance to get started
                  </Typography>
                </Box>
              )}
            </TableContainer>
          )}
        </CardContent>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleViewDetails}>
          <ListItemIcon><Computer /></ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        {selectedInstance && canPerformAction(selectedInstance.state, 'reboot') && (
          <MenuItem onClick={() => handleAction('reboot', selectedInstance)}>
            <ListItemIcon><Refresh /></ListItemIcon>
            <ListItemText>Reboot</ListItemText>
          </MenuItem>
        )}
        {selectedInstance && canPerformAction(selectedInstance.state, 'terminate') && (
          <MenuItem 
            onClick={() => setConfirmDialog({
              open: true,
              action: 'terminate',
              instance: selectedInstance
            })}
            sx={{ color: 'error.main' }}
          >
            <ListItemIcon><Delete color="error" /></ListItemIcon>
            <ListItemText>Terminate</ListItemText>
          </MenuItem>
        )}
      </Menu>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, action: '', instance: null })}
      >
        <DialogTitle>
          Confirm {confirmDialog.action?.charAt(0).toUpperCase() + confirmDialog.action?.slice(1)}
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to {confirmDialog.action} instance{' '}
            <strong>{confirmDialog.instance?.name || confirmDialog.instance?.instance_id}</strong>?
            {confirmDialog.action === 'terminate' && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                This action cannot be undone. All data on the instance will be lost.
              </Alert>
            )}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({ open: false, action: '', instance: null })}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={confirmDialog.action === 'terminate' ? 'error' : 'primary'}
            onClick={() => handleAction(confirmDialog.action, confirmDialog.instance)}
            disabled={loading}
          >
            {confirmDialog.action?.charAt(0).toUpperCase() + confirmDialog.action?.slice(1)}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Instance Details Dialog */}
      <Dialog
        open={detailsDialog}
        onClose={() => setDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Computer color="primary" />
            Instance Details
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedInstance && (
            <Box>
              <Grid container spacing={3}>
                {/* Basic Information */}
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Basic Information</Typography>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Instance Name</Typography>
                    <Typography variant="body1" fontWeight="medium">
                      {selectedInstance.name || 'Unnamed'}
                    </Typography>
                  </Box>
                  <Box mt={2}>
                    <Typography variant="body2" color="text.secondary">Instance ID</Typography>
                    <Typography variant="body1" fontFamily="monospace">
                      {selectedInstance.instance_id}
                    </Typography>
                  </Box>
                  <Box mt={2}>
                    <Typography variant="body2" color="text.secondary">State</Typography>
                    <Chip 
                      label={selectedInstance.state} 
                      color={getStateColor(selectedInstance.state)} 
                      size="small" 
                    />
                  </Box>
                  <Box mt={2}>
                    <Typography variant="body2" color="text.secondary">Instance Type</Typography>
                    <Typography variant="body1">{selectedInstance.instance_type}</Typography>
                  </Box>
                </Grid>

                {/* Network Information */}
                <Grid item xs={12} md={6}>
                  <Typography variant="h6" gutterBottom>Network Information</Typography>
                  <Box>
                    <Typography variant="body2" color="text.secondary">Public IP</Typography>
                    <Typography variant="body1" fontFamily="monospace">
                      {selectedInstance.public_ip || 'Not assigned'}
                    </Typography>
                  </Box>
                  <Box mt={2}>
                    <Typography variant="body2" color="text.secondary">Private IP</Typography>
                    <Typography variant="body1" fontFamily="monospace">
                      {selectedInstance.private_ip || 'Not assigned'}
                    </Typography>
                  </Box>
                  <Box mt={2}>
                    <Typography variant="body2" color="text.secondary">Availability Zone</Typography>
                    <Typography variant="body1">
                      {selectedInstance.availability_zone || 'Unknown'}
                    </Typography>
                  </Box>
                  <Box mt={2}>
                    <Typography variant="body2" color="text.secondary">VPC ID</Typography>
                    <Typography variant="body1" fontFamily="monospace">
                      {selectedInstance.vpc_id || 'Unknown'}
                    </Typography>
                  </Box>
                </Grid>

                {/* Connection Information */}
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>Connection Information</Typography>
                  
                  {selectedInstance.public_ip && selectedInstance.key_name ? (
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        SSH Connection Command (copy and paste):
                      </Typography>
                      
                      <Box 
                        sx={{ 
                          p: 2, 
                          bgcolor: 'grey.100', 
                          borderRadius: 1, 
                          border: '1px solid',
                          borderColor: 'grey.300',
                          position: 'relative'
                        }}
                      >
                        <Typography 
                          variant="body1" 
                          fontFamily="monospace" 
                          sx={{ wordBreak: 'break-all' }}
                        >
                          ssh -i {selectedInstance.key_name}-private.pem ec2-user@{selectedInstance.public_ip}
                        </Typography>
                        
                        <IconButton
                          size="small"
                          sx={{ 
                            position: 'absolute', 
                            top: 8, 
                            right: 8,
                            bgcolor: 'white'
                          }}
                          onClick={() => {
                            const command = `ssh -i ${selectedInstance.key_name}-private.pem ec2-user@${selectedInstance.public_ip}`;
                            navigator.clipboard.writeText(command);
                            toast.success('SSH command copied to clipboard!');
                          }}
                        >
                          <ContentCopy fontSize="small" />
                        </IconButton>
                      </Box>
                      
                      <Alert severity="info" sx={{ mt: 2 }}>
                        <Typography variant="body2">
                          <strong>Note:</strong> Make sure you have the private key file ({selectedInstance.key_name}-private.pem) 
                          in your current directory and set proper permissions (chmod 400).
                        </Typography>
                      </Alert>
                    </Box>
                  ) : (
                    <Alert severity="warning">
                      <Typography variant="body2">
                        <strong>Connection not available:</strong> This instance needs a public IP address and key pair to connect via SSH.
                      </Typography>
                    </Alert>
                  )}

                  {/* Additional Connection Options */}
                  <Box mt={3}>
                    <Typography variant="h6" gutterBottom>Alternative Connection Methods</Typography>
                    
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="subtitle2" gutterBottom>
                              AWS Systems Manager Session Manager
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Connect without SSH keys or public IP
                            </Typography>
                            <Button 
                              size="small" 
                              variant="outlined" 
                              startIcon={<Computer />}
                              onClick={() => {
                                const command = `aws ssm start-session --target ${selectedInstance.instance_id}`;
                                navigator.clipboard.writeText(command);
                                toast.success('Session Manager command copied!');
                              }}
                            >
                              Copy Command
                            </Button>
                          </CardContent>
                        </Card>
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <Card variant="outlined">
                          <CardContent>
                            <Typography variant="subtitle2" gutterBottom>
                              AWS Console EC2 Instance Connect
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              Browser-based SSH connection
                            </Typography>
                            <Button 
                              size="small" 
                              variant="outlined" 
                              startIcon={<Computer />}
                              onClick={() => {
                                const url = `https://console.aws.amazon.com/ec2/v2/home?region=${selectedInstance.region || 'us-east-1'}#Instance:instanceId=${selectedInstance.instance_id}`;
                                window.open(url, '_blank');
                              }}
                            >
                              Open in Console
                            </Button>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailsDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Create Instance Dialog */}
      <Dialog
        open={createDialog}
        onClose={() => setCreateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Launch New EC2 Instance</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Instance Name"
                value={newInstance.name}
                onChange={(e) => setNewInstance(prev => ({ ...prev, name: e.target.value }))}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>AMI</InputLabel>
                <Select
                  value={newInstance.image_id}
                  onChange={(e) => setNewInstance(prev => ({ ...prev, image_id: e.target.value }))}
                  label="AMI"
                >
                  {amis.slice(0, 10).map((ami) => (
                    <MenuItem key={ami.image_id} value={ami.image_id}>
                      {ami.name} ({ami.image_id})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Instance Type</InputLabel>
                <Select
                  value={newInstance.instance_type}
                  onChange={(e) => setNewInstance(prev => ({ ...prev, instance_type: e.target.value }))}
                  label="Instance Type"
                >
                  <MenuItem value="t2.micro">t2.micro (1 vCPU, 1 GB RAM) - Free Tier</MenuItem>
                  <MenuItem value="t2.small">t2.small (1 vCPU, 2 GB RAM)</MenuItem>
                  <MenuItem value="t2.medium">t2.medium (2 vCPU, 4 GB RAM)</MenuItem>
                  <MenuItem value="t3.micro">t3.micro (2 vCPU, 1 GB RAM)</MenuItem>
                  <MenuItem value="t3.small">t3.small (2 vCPU, 2 GB RAM)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Key Pair</InputLabel>
                <Select
                  value={newInstance.key_name}
                  onChange={(e) => setNewInstance(prev => ({ ...prev, key_name: e.target.value }))}
                  label="Key Pair"
                >
                  <MenuItem value="">None</MenuItem>
                  {keyPairs.map((kp) => (
                    <MenuItem key={kp.key_name} value={kp.key_name}>
                      {kp.key_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Security Group</InputLabel>
                <Select
                  multiple
                  value={newInstance.security_group_ids}
                  onChange={(e) => setNewInstance(prev => ({ ...prev, security_group_ids: e.target.value }))}
                  label="Security Group"
                >
                  {securityGroups.map((sg) => (
                    <MenuItem key={sg.group_id} value={sg.group_id}>
                      {sg.group_name} ({sg.group_id})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateInstance}
            disabled={!newInstance.image_id || !newInstance.instance_type || loading}
          >
            Launch Instance
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EC2Instances;
