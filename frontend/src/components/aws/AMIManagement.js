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
  FormControl,
  InputLabel,
  Select,
  Button,
  Alert,
  CircularProgress,
  Tooltip,
  Avatar,
  Stack,
} from '@mui/material';
import {
  MoreVert,
  Refresh,
  Launch,
  FilterList,
  Search,
  Computer,
  Security,
  Public,
  Lock,
  CloudQueue,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useEC2 } from '../../hooks/useAWS';
import { useTheme } from '../../contexts/ThemeContext';

const AMIManagement = () => {
  const { listAMIs, loading, error } = useEC2();
  const { isDark } = useTheme();
  
  const [amis, setAMIs] = useState([]);
  const [filteredAMIs, setFilteredAMIs] = useState([]);
  const [filters, setFilters] = useState({
    name: '',
    architecture: '',
    platform: '',
    owner: 'amazon'
  });
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedAMI, setSelectedAMI] = useState(null);

  useEffect(() => {
    loadAMIs();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [amis, filters]);

  const loadAMIs = async () => {
    try {
      const result = await listAMIs({ 
        name: filters.name || 'amzn2',
        architecture: filters.architecture 
      });
      setAMIs(result.amis || []);
    } catch (error) {
      console.error('Failed to load AMIs:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...amis];

    if (filters.name) {
      filtered = filtered.filter(ami => 
        ami.name.toLowerCase().includes(filters.name.toLowerCase())
      );
    }

    if (filters.architecture) {
      filtered = filtered.filter(ami => ami.architecture === filters.architecture);
    }

    if (filters.platform) {
      filtered = filtered.filter(ami => ami.platform === filters.platform);
    }

    if (filters.owner) {
      filtered = filtered.filter(ami => 
        filters.owner === 'amazon' ? ami.owner_id === 'amazon' : 
        filters.owner === 'self' ? ami.owner_id !== 'amazon' : true
      );
    }

    setFilteredAMIs(filtered);
  };

  const handleMenuOpen = (event, ami) => {
    setAnchorEl(event.currentTarget);
    setSelectedAMI(ami);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedAMI(null);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const handleRefresh = () => {
    loadAMIs();
  };

  const getOwnerIcon = (ownerId) => {
    return ownerId === 'amazon' ? <Public color="primary" /> : <Lock color="action" />;
  };

  const getArchitectureColor = (arch) => {
    return arch === 'x86_64' ? 'primary' : arch === 'arm64' ? 'secondary' : 'default';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" display="flex" alignItems="center" gap={1}>
            <CloudQueue color="primary" />
            AMI Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage Amazon Machine Images (AMIs) for launching instances
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
            <FilterList color="action" />
            <Typography variant="subtitle2">Filters:</Typography>
            
            <TextField
              size="small"
              label="Name"
              value={filters.name}
              onChange={(e) => handleFilterChange('name', e.target.value)}
              placeholder="e.g., amzn2, ubuntu"
              sx={{ minWidth: 150 }}
            />
            
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Architecture</InputLabel>
              <Select
                value={filters.architecture}
                onChange={(e) => handleFilterChange('architecture', e.target.value)}
                label="Architecture"
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="x86_64">x86_64</MenuItem>
                <MenuItem value="arm64">ARM64</MenuItem>
                <MenuItem value="i386">i386</MenuItem>
              </Select>
            </FormControl>

            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Owner</InputLabel>
              <Select
                value={filters.owner}
                onChange={(e) => handleFilterChange('owner', e.target.value)}
                label="Owner"
              >
                <MenuItem value="amazon">Amazon</MenuItem>
                <MenuItem value="self">My AMIs</MenuItem>
                <MenuItem value="">All</MenuItem>
              </Select>
            </FormControl>

            <Button variant="outlined" startIcon={<Search />} onClick={loadAMIs}>
              Search
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

      {/* AMI Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Available AMIs ({filteredAMIs.length})
          </Typography>
          
          {loading && filteredAMIs.length === 0 ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>AMI Details</TableCell>
                    <TableCell>Architecture</TableCell>
                    <TableCell>Platform</TableCell>
                    <TableCell>Owner</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredAMIs.map((ami, index) => (
                    <motion.tr
                      key={ami.image_id}
                      component={TableRow}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1, duration: 0.3 }}
                      hover
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ bgcolor: 'primary.main' }}>
                            <Computer />
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {ami.name || 'Unnamed AMI'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" fontFamily="monospace">
                              {ami.image_id}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={ami.architecture}
                          color={getArchitectureColor(ami.architecture)}
                          size="small"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2" sx={{ textTransform: 'capitalize' }}>
                          {ami.platform || 'Linux'}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getOwnerIcon(ami.owner_id)}
                          <Typography variant="body2">
                            {ami.owner_id === 'amazon' ? 'Amazon' : ami.owner_id}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2">
                          {formatDate(ami.creation_date)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={ami.state}
                          color={ami.state === 'available' ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Tooltip title="Launch Instance">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => {
                              // TODO: Integrate with instance creation
                              console.log('Launch instance with AMI:', ami.image_id);
                            }}
                          >
                            <Launch />
                          </IconButton>
                        </Tooltip>
                        
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, ami)}
                        >
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
              
              {filteredAMIs.length === 0 && !loading && (
                <Box textAlign="center" p={4}>
                  <Typography variant="h6" color="text.secondary">
                    No AMIs found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Try adjusting your filters or search criteria
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
        <MenuItem onClick={() => {
          console.log('View AMI details:', selectedAMI?.image_id);
          handleMenuClose();
        }}>
          <ListItemIcon><Search /></ListItemIcon>
          <ListItemText>View Details</ListItemText>
        </MenuItem>
        
        <MenuItem onClick={() => {
          console.log('Launch instance with AMI:', selectedAMI?.image_id);
          handleMenuClose();
        }}>
          <ListItemIcon><Launch /></ListItemIcon>
          <ListItemText>Launch Instance</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default AMIManagement;
