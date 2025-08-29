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
  FormControl,
  InputLabel,
  Select,
  Grid,
} from '@mui/material';
import {
  MoreVert,
  Refresh,
  Add,
  Download,
  Delete,
  VpnKey,
  Info,
  Security,
  Fingerprint,
  FilterList,
  CloudUpload,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useEC2 } from '../../hooks/useAWS';
import { useTheme } from '../../contexts/ThemeContext';

const KeyPairManagement = () => {
  const { listKeyPairs, loading, error } = useEC2();
  const { isDark } = useTheme();
  
  const [keyPairs, setKeyPairs] = useState([]);
  const [filteredKeyPairs, setFilteredKeyPairs] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedKeyPair, setSelectedKeyPair] = useState(null);
  const [detailsDialog, setDetailsDialog] = useState(false);
  const [createDialog, setCreateDialog] = useState(false);
  const [newKeyPair, setNewKeyPair] = useState({
    name: '',
    type: 'rsa'
  });

  useEffect(() => {
    loadKeyPairs();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [keyPairs, searchTerm]);

  const loadKeyPairs = async () => {
    try {
      const result = await listKeyPairs();
      setKeyPairs(result.key_pairs || []);
    } catch (error) {
      console.error('Failed to load key pairs:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...keyPairs];

    if (searchTerm) {
      filtered = filtered.filter(kp => 
        kp.key_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        kp.key_fingerprint.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    setFilteredKeyPairs(filtered);
  };

  const handleMenuOpen = (event, keyPair) => {
    setAnchorEl(event.currentTarget);
    setSelectedKeyPair(keyPair);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedKeyPair(null);
  };

  const handleViewDetails = () => {
    setDetailsDialog(true);
    handleMenuClose();
  };

  const handleRefresh = () => {
    loadKeyPairs();
  };

  const handleCreateKeyPair = () => {
    setCreateDialog(true);
  };

  const handleCreateSubmit = () => {
    // TODO: Implement key pair creation
    console.log('Creating key pair:', newKeyPair);
    setCreateDialog(false);
    setNewKeyPair({ name: '', type: 'rsa' });
  };

  const getKeyTypeColor = (type) => {
    const colors = {
      'rsa': 'primary',
      'ed25519': 'secondary',
      'ecdsa': 'success'
    };
    return colors[type] || 'default';
  };

  const formatFingerprint = (fingerprint) => {
    if (!fingerprint) return 'N/A';
    // Format fingerprint with colons for better readability
    return fingerprint.length > 32 ? 
      fingerprint.match(/.{2}/g)?.join(':') || fingerprint :
      fingerprint;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold" display="flex" alignItems="center" gap={1}>
            <VpnKey color="primary" />
            Key Pairs
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage SSH key pairs for secure access to your EC2 instances
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
            onClick={handleCreateKeyPair}
          >
            Create Key Pair
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
              label="Search Key Pairs"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name or fingerprint..."
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

      {/* Key Pairs Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Key Pairs ({filteredKeyPairs.length})
          </Typography>
          
          {loading && filteredKeyPairs.length === 0 ? (
            <Box display="flex" justifyContent="center" p={4}>
              <CircularProgress />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Key Name</TableCell>
                    <TableCell>Key Type</TableCell>
                    <TableCell>Fingerprint</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredKeyPairs.map((keyPair, index) => (
                    <motion.tr
                      key={keyPair.key_name}
                      component={TableRow}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1, duration: 0.3 }}
                      hover
                    >
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={2}>
                          <Avatar sx={{ bgcolor: 'primary.main' }}>
                            <VpnKey />
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {keyPair.key_name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              SSH Key Pair
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      
                      <TableCell>
                        <Chip
                          label={keyPair.key_type.toUpperCase()}
                          color={getKeyTypeColor(keyPair.key_type)}
                          size="small"
                        />
                      </TableCell>
                      
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace" fontSize="0.75rem">
                          {formatFingerprint(keyPair.key_fingerprint)}
                        </Typography>
                      </TableCell>
                      
                      <TableCell>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            color="primary"
                            onClick={() => {
                              setSelectedKeyPair(keyPair);
                              setDetailsDialog(true);
                            }}
                          >
                            <Info />
                          </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Download Public Key">
                          <IconButton
                            size="small"
                            color="secondary"
                            onClick={() => {
                              console.log('Download public key:', keyPair.key_name);
                            }}
                          >
                            <Download />
                          </IconButton>
                        </Tooltip>
                        
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuOpen(e, keyPair)}
                        >
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
              
              {filteredKeyPairs.length === 0 && !loading && (
                <Box textAlign="center" p={4}>
                  <Typography variant="h6" color="text.secondary">
                    No key pairs found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Create a key pair to securely connect to your EC2 instances
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
          console.log('Download public key:', selectedKeyPair?.key_name);
          handleMenuClose();
        }}>
          <ListItemIcon><Download /></ListItemIcon>
          <ListItemText>Download Public Key</ListItemText>
        </MenuItem>
        
        <MenuItem 
          onClick={() => {
            console.log('Delete key pair:', selectedKeyPair?.key_name);
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
            <VpnKey color="primary" />
            Key Pair Details
          </Box>
        </DialogTitle>
        
        <DialogContent>
          {selectedKeyPair && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Key Name</Typography>
                  <Typography variant="body1" fontWeight="medium">{selectedKeyPair.key_name}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="body2" color="text.secondary">Key Type</Typography>
                  <Chip label={selectedKeyPair.key_type.toUpperCase()} color={getKeyTypeColor(selectedKeyPair.key_type)} />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">Key Fingerprint</Typography>
                  <Typography variant="body1" fontFamily="monospace" sx={{ wordBreak: 'break-all' }}>
                    {selectedKeyPair.key_fingerprint}
                  </Typography>
                </Grid>
              </Grid>

              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Security Note:</strong> The private key was only available for download when the key pair was created. 
                  If you've lost the private key, you'll need to create a new key pair.
                </Typography>
              </Alert>

              <Alert severity="warning" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>Important:</strong> Keep your private key secure and never share it. 
                  Anyone with access to your private key can connect to instances that use this key pair.
                </Typography>
              </Alert>
            </Box>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setDetailsDialog(false)}>Close</Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => {
              console.log('Download public key:', selectedKeyPair?.key_name);
              setDetailsDialog(false);
            }}
          >
            Download Public Key
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Key Pair Dialog */}
      <Dialog
        open={createDialog}
        onClose={() => setCreateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <Add color="primary" />
            Create New Key Pair
          </Box>
        </DialogTitle>
        
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Key Pair Name"
                value={newKeyPair.name}
                onChange={(e) => setNewKeyPair(prev => ({ ...prev, name: e.target.value }))}
                placeholder="my-key-pair"
                helperText="Choose a descriptive name for your key pair"
              />
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Key Type</InputLabel>
                <Select
                  value={newKeyPair.type}
                  onChange={(e) => setNewKeyPair(prev => ({ ...prev, type: e.target.value }))}
                  label="Key Type"
                >
                  <MenuItem value="rsa">RSA (Recommended)</MenuItem>
                  <MenuItem value="ed25519">ED25519 (Modern)</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              The private key will be automatically downloaded when created. 
              Store it securely - you won't be able to download it again.
            </Typography>
          </Alert>
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setCreateDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateSubmit}
            disabled={!newKeyPair.name.trim()}
            startIcon={<CloudUpload />}
          >
            Create Key Pair
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default KeyPairManagement;
