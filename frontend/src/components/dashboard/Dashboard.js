import React, { useState, useEffect } from 'react';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  useMediaQuery,
  Chip,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Cloud as CloudIcon,
  Chat as ChatIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
  Notifications as NotificationsIcon,
  Brightness4,
  Brightness7,
  Psychology,
  Speed,
} from '@mui/icons-material';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { useWebSocket } from '../../contexts/WebSocketContext';

// Dashboard components
import Overview from './Overview';
import ChatPage from './ChatPage';
import AWSServices from './AWSServices';
import UserSettings from './UserSettings';
import LoadingSpinner from '../common/LoadingSpinner';

const drawerWidth = 280;

const Dashboard = () => {
  const { user, logout, token } = useAuth();
  const { mode, toggleMode, isDark, animations } = useTheme();
  const { connected, systemStatus: wsSystemStatus, requestSystemStatus } = useWebSocket();
  const navigate = useNavigate();
  const location = useLocation();
  const isMobile = useMediaQuery((theme) => theme.breakpoints.down('md'));
  
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const [notificationCount] = useState(3); // Mock notifications
  const [systemStatus, setSystemStatus] = useState({
    chatbot: 'checking',
    aws: 'checking',
    backend: 'checking'
  });

  useEffect(() => {
    // Close mobile drawer when route changes
    setMobileOpen(false);
  }, [location.pathname]);

  // Use WebSocket system status when available
  useEffect(() => {
    if (wsSystemStatus) {
      console.log('🔧 Updating system status from WebSocket:', wsSystemStatus);
      setSystemStatus(wsSystemStatus);
    }
  }, [wsSystemStatus]);

  useEffect(() => {
    // Check system status on component mount
    if (connected) {
      // Use WebSocket to get system status
      requestSystemStatus();
    } else {
      // Fallback to HTTP check
      checkSystemStatus();
    }
    
    // Set up periodic status checks every 30 seconds (only if WebSocket not connected)
    const statusInterval = setInterval(() => {
      if (connected) {
        requestSystemStatus();
      } else {
        checkSystemStatus();
      }
    }, 30000);
    
    return () => clearInterval(statusInterval);
  }, [connected, requestSystemStatus]);

  const checkSystemStatus = async () => {
    try {
      // Check backend API health
      const backendResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/health`);
      const backendHealthy = backendResponse.ok;
      
      // Check chatbot service
      const chatResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/chat/health`);
      const chatData = chatResponse.ok ? await chatResponse.json() : null;
      const chatbotHealthy = chatData?.ai_service_configured;
      
      // Check AWS credentials
      const awsResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/aws/credentials`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        }
      });
      const awsData = awsResponse.ok ? await awsResponse.json() : null;
      const awsHealthy = awsData?.has_credentials;
      
      setSystemStatus({
        backend: backendHealthy ? 'connected' : 'disconnected',
        chatbot: chatbotHealthy ? 'connected' : 'disconnected',
        aws: awsHealthy ? 'connected' : 'disconnected'
      });
      
    } catch (error) {
      console.error('System status check failed:', error);
      setSystemStatus({
        backend: 'disconnected',
        chatbot: 'disconnected', 
        aws: 'disconnected'
      });
    }
  };

  const getOverallStatus = () => {
    const statuses = Object.values(systemStatus);
    if (statuses.includes('checking')) return 'checking';
    if (statuses.every(status => status === 'connected')) return 'connected';
    if (statuses.every(status => status === 'disconnected')) return 'disconnected';
    return 'partial';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'success';
      case 'disconnected': return 'error';
      case 'partial': return 'warning';
      case 'checking': return 'info';
      default: return 'default';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'connected': return 'All Systems Online';
      case 'disconnected': return 'Systems Offline';
      case 'partial': return 'Partial Systems';
      case 'checking': return 'Checking Status...';
      default: return 'Unknown Status';
    }
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleProfileMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    handleProfileMenuClose();
    await logout();
    navigate('/login');
  };

  const menuItems = [
    {
      text: 'Overview',
      icon: <DashboardIcon />,
      path: '/dashboard',
      color: 'primary.main',
    },
    {
      text: 'CloudGenie',
      icon: <ChatIcon />,
      path: '/dashboard/chat',
      color: 'secondary.main',
      badge: connected ? 'online' : 'offline',
    },
    {
      text: 'AWS Services',
      icon: <CloudIcon />,
      path: '/dashboard/aws',
      color: 'info.main',
    },
    {
      text: 'Settings',
      icon: <SettingsIcon />,
      path: '/dashboard/settings',
      color: 'warning.main',
    },
  ];

  const getCurrentPageTitle = () => {
    const currentPath = location.pathname;
    const currentItem = menuItems.find(item => item.path === currentPath);
    return currentItem?.text || 'Dashboard';
  };

  const drawer = (
    <Box sx={{ height: '100%', bgcolor: 'background.paper' }}>
      {/* Logo Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <Psychology 
              sx={{ 
                fontSize: 40, 
                color: 'primary.main',
                mb: 1,
                filter: isDark ? 'drop-shadow(0 0 10px rgba(79, 195, 247, 0.3))' : 'none'
              }} 
            />
          </motion.div>
          <Typography variant="h6" fontWeight="bold" color="primary">
            AWS Chatbot
          </Typography>
          <Typography variant="caption" color="text.secondary">
            AI-Powered Management
          </Typography>
        </Box>
      </motion.div>

      <Divider />

      {/* Navigation Menu */}
      <List sx={{ px: 2, py: 1 }}>
        {menuItems.map((item, index) => (
          <motion.div
            key={item.text}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
          >
            <ListItem
              button
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 2,
                mb: 1,
                backgroundColor: location.pathname === item.path 
                  ? 'primary.main' 
                  : 'transparent',
                color: location.pathname === item.path 
                  ? 'primary.contrastText' 
                  : 'text.primary',
                '&:hover': {
                  backgroundColor: location.pathname === item.path 
                    ? 'primary.dark' 
                    : 'action.hover',
                  transform: animations ? 'translateX(4px)' : 'none',
                },
                transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              }}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.path 
                    ? 'primary.contrastText' 
                    : item.color,
                  minWidth: 40,
                }}
              >
                {item.badge ? (
                  <Badge
                    variant="dot"
                    color={item.badge === 'online' ? 'success' : 'error'}
                  >
                    {item.icon}
                  </Badge>
                ) : (
                  item.icon
                )}
              </ListItemIcon>
              <ListItemText 
                primary={item.text}
                sx={{ ml: 1 }}
              />
            </ListItem>
          </motion.div>
        ))}
      </List>

      <Divider sx={{ mt: 'auto' }} />

      {/* System Status */}
      <Box sx={{ p: 2 }}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <Tooltip
            title={
              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>System Status Details:</Typography>
                <Typography variant="caption" display="block">
                  🖥️ Backend API: {systemStatus.backend === 'connected' ? '✅ Online' : '❌ Offline'}
                </Typography>
                <Typography variant="caption" display="block">
                  🤖 AI Chatbot: {systemStatus.chatbot === 'connected' ? '✅ Ready' : '❌ Not Available'}
                </Typography>
                <Typography variant="caption" display="block">
                  ☁️ AWS Integration: {systemStatus.aws === 'connected' ? '✅ Configured' : '❌ Not Configured'}
                </Typography>
              </Box>
            }
            placement="top"
          >
            <Chip
              icon={<Speed />}
              label={getStatusLabel(getOverallStatus())}
              color={getStatusColor(getOverallStatus())}
              variant="outlined"
              size="small"
              sx={{ 
                width: '100%',
                cursor: 'pointer',
                '&:hover': {
                  backgroundColor: theme => theme.palette.action.hover
                }
              }}
              onClick={checkSystemStatus}
            />
          </Tooltip>
        </motion.div>
      </Box>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', margin: 0, padding: 0 }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
          zIndex: 1300,
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {getCurrentPageTitle()}
          </Typography>

          {/* Theme Toggle */}
          <Tooltip title={`Switch to ${isDark ? 'light' : 'dark'} mode`}>
            <IconButton color="inherit" onClick={toggleMode} sx={{ mr: 1 }}>
              <motion.div
                key={mode}
                initial={{ rotate: -180, opacity: 0 }}
                animate={{ rotate: 0, opacity: 1 }}
                transition={{ duration: 0.3 }}
              >
                {isDark ? <Brightness7 /> : <Brightness4 />}
              </motion.div>
            </IconButton>
          </Tooltip>

          {/* Notifications */}
          <Tooltip title="Notifications">
            <IconButton color="inherit" sx={{ mr: 1 }}>
              <Badge badgeContent={notificationCount} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
          </Tooltip>

          {/* User Menu */}
          <Tooltip title="Account settings">
            <IconButton
              onClick={handleProfileMenuOpen}
              sx={{ p: 0 }}
            >
              <Avatar
                sx={{
                  bgcolor: 'secondary.main',
                  border: '2px solid',
                  borderColor: 'background.paper',
                }}
              >
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </Avatar>
            </IconButton>
          </Tooltip>

          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
            onClick={handleProfileMenuClose}
            PaperProps={{
              elevation: 0,
              sx: {
                overflow: 'visible',
                filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
                mt: 1.5,
                minWidth: 200,
                '& .MuiAvatar-root': {
                  width: 32,
                  height: 32,
                  ml: -0.5,
                  mr: 1,
                },
                '&:before': {
                  content: '""',
                  display: 'block',
                  position: 'absolute',
                  top: 0,
                  right: 14,
                  width: 10,
                  height: 10,
                  bgcolor: 'background.paper',
                  transform: 'translateY(-50%) rotate(45deg)',
                  zIndex: 0,
                },
              },
            }}
            transformOrigin={{ horizontal: 'right', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
          >
            <MenuItem onClick={() => navigate('/dashboard/settings')}>
              <PersonIcon sx={{ mr: 2 }} />
              Profile Settings
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <LogoutIcon sx={{ mr: 2 }} />
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        {drawer}
      </Drawer>

      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', md: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            position: 'fixed',
            height: '100vh',
            top: 0,
            left: 0,
            zIndex: 1200,
            border: 'none',
          },
        }}
        open
      >
        {drawer}
      </Drawer>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          marginLeft: { xs: 0, md: `${drawerWidth}px` },
          width: { xs: '100%', md: `calc(100% - ${drawerWidth}px)` },
          bgcolor: 'background.default',
          minHeight: '100vh',
          padding: 0,
        }}
      >
        <Toolbar />
        
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: animations ? 0.3 : 0 }}
            style={{ height: 'calc(100vh - 64px)', padding: 0, margin: 0 }}
          >
            <Routes>
              <Route path="/" element={<Overview />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/aws" element={<AWSServices />} />
              <Route path="/settings" element={<UserSettings />} />
            </Routes>
          </motion.div>
        </AnimatePresence>
      </Box>
    </Box>
  );
};

export default Dashboard;
