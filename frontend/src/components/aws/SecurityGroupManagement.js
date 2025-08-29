import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
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
  TextField,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  Divider,
  Grid,
} from '@mui/material';
import {
  MoreVert,
  Refresh,
  Add,
  Edit,
  Delete,
  Security,
  Info,
  ArrowForward,
  ArrowBack,
  Public,
  VpnLock,
  FilterList,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useEC2 } from '../../hooks/useAWS';
import { useTheme } from '../../contexts/ThemeContext';

const SecurityGroupManagement = () => {
  const { listSecurityGroups, loading, error } = useEC2();
  const { isDark } = useTheme();
  
  const [securityGroups, setSecurityGroups] = useState([]);
  const [filteredGroups, setFilteredGroups] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [detailsDialog, setDetailsDialog] = useState(false);

  useEffect(() => {
    loadSecurityGroups();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [securityGroups, searchTerm]);

  const loadSecurityGroups = async () => {
    try {
      const result = await listSecurityGroups();
      setSecurityGroups(result.security_groups || []);
    } catch (error) {
      console.error('Failed to load security groups:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...securityGroups];

    if (searchTerm) {
      filtered = filtered.filter(sg => 
        sg.group_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        sg.group_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        sg.description.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredGroups(filtered);
  };

  const handleMenuOpen = (event, group) => {
    setAnchorEl(event.currentTarget);
    setSelectedGroup(group);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedGroup(null);
  };

  const handleViewDetails = () => {
    setDetailsDialog(true);
    handleMenuClose();
  };

  const handleRefresh = () => {
    loadSecurityGroups();
  };

  const getRuleTypeColor = (isInbound) => {
    return isInbound ? 'success' : 'warning';
  };

  const getRuleTypeIcon = (isInbound) => {
    return isInbound ? <ArrowBack /> : <ArrowForward />;
  };

  const formatProtocol = (protocol) => {
    const protocols = {
      'tcp': 'TCP',
      'udp': 'UDP',
      'icmp': 'ICMP',
      '-1': 'All'
    };
    return protocols[protocol] || protocol.toUpperCase();
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" display="flex" alignItems="center" gap={1}>
            <Security color="primary" />
            Security Groups
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage network access control for your EC2 instances
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => console.log('Create new security group')}
          >
            Create Security Group
          </Button>
        </Box>
      </Box>

      {/* Search */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center">
            <FilterList color="action" />
            <TextField
              fullWidth
              size="small"
              label="Search Security Groups"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, ID, or description..."
            />
          </Box>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Security Groups Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Security Groups ({filteredGroups.length})
          </Typography>
          
          {loading && filteredGroups.length === 0 ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Security Group</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell>VPC</TableCell>
                    <TableCell>Inbound Rules</TableCell>
                    <TableCell>Outbound Rules</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredGroups.map((group, index) => (
                    <motion.tr
                      key={group.group_id}
                      component={TableRow}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1, duration: 0.3 }}
                      hover
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ bgcolor: 'secondary.main' }}>
                            <VpnLock />
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {group.group_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" fontFamily="monospace">
                              {group.group_id}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {group.description}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={group.vpc_id || 'EC2-Classic'}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={`${group.inbound_rules} rules`}
                          color="success"
                          size="small"
                          icon={<ArrowBack />}
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={`${group.outbound_rules} rules`}
                          color="warning"
                          size="small"
                          icon={<ArrowForward />}
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => {
                              setSelectedGroup(group);
                              setDetailsDialog(true);
                            }}
                          >
                            <Info />
                          </IconButton>
                        </Tooltip>
                        
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, group)}
                        >
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
              
              {filteredGroups.length === 0 && !loading && (
                <Box textAlign="center" p={4}>
                  <Typography variant="h6" color="text.secondary">
                    No security groups found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Try adjusting your search criteria
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
          <ListItemIcon><Info /></ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => {
          console.log('Edit security group:', selectedGroup?.group_id);
          handleMenuClose();
        }}>
          <ListItemIcon><Edit /></ListItemIcon>
          <ListItemText>Edit Rules</ListItemText>
        </MenuItem>
        
        <MenuItem 
          onClick={() => {
            console.log('Delete security group:', selectedGroup?.group_id);
            handleMenuClose();
          }}
          sx={{ color: 'error.main' }}
        >
          <ListItemIcon><Delete color="error" /></ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* Details Dialog */}
      <Dialog
        open={detailsDialog}
        onClose={() => setDetailsDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Security color="primary" />
            Security Group Details
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedGroup && (
            <Box>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Group Name</Typography>
                  <Typography variant="body1" fontWeight="medium">{selectedGroup.group_name}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Group ID</Typography>
                  <Typography variant="body1" fontFamily="monospace">{selectedGroup.group_id}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">Description</Typography>
                  <Typography variant="body1">{selectedGroup.description}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">VPC ID</Typography>
                  <Typography variant="body1">{selectedGroup.vpc_id || 'EC2-Classic'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Owner</Typography>
                  <Typography variant="body1">{selectedGroup.owner_id}</Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Network Rules Summary
              </Typography>
              
              <Box display="flex" gap={2} mb={2}>
                <Chip
                  label={`${selectedGroup.inbound_rules} Inbound Rules`}
                  color="success"
                  icon={<ArrowBack />}
                />
                <Chip
                  label={`${selectedGroup.outbound_rules} Outbound Rules`}
                  color="warning"
                  icon={<ArrowForward />}
                />
              </Box>

              <Alert severity="info">
                <Typography variant="body2">
                  To view and edit detailed rules, use the AWS Console or CLI.
                  This interface provides an overview of your security group configuration.
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailsDialog(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => {
              console.log('Edit rules for:', selectedGroup?.group_id);
              setDetailsDialog(false);
            }}
          >
            Edit Rules
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SecurityGroupManagement;
