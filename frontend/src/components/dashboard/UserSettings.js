import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Avatar,
  IconButton,
  Chip,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Edit,
  Save,
  Cancel,
  CloudUpload,
  Palette,
  Notifications,
  Security,
  Language,
  Speed,
  Brightness4,
  Brightness7,
  Psychology,
  Memory,
  Storage,
  VolumeUp,
  Visibility,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { toast } from 'react-toastify';

const UserSettings = () => {
  const { user, updateUserProfile } = useAuth();
  const { 
    mode, 
    toggleMode, 
    accentColor, 
    setAccentColor, 
    animations, 
    setAnimations,
    compactMode,
    setCompactMode,
  } = useTheme();

  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    fullName: user?.full_name || '',
    awsRegion: user?.aws_region || 'us-east-1',
  });

  const [preferences, setPreferences] = useState({
    notifications: true,
    emailAlerts: true,
    soundEnabled: true,
    autoRefresh: true,
    refreshInterval: 30,
    language: 'en',
    timezone: 'UTC',
    chatHistory: true,
    analyticsOptIn: false,
  });

  const accentColors = [
    { name: 'Blue', value: 'blue', color: '#1976D2' },
    { name: 'Purple', value: 'purple', color: '#7B1FA2' },
    { name: 'Green', value: 'green', color: '#388E3C' },
    { name: 'Orange', value: 'orange', color: '#F57C00' },
    { name: 'Pink', value: 'pink', color: '#C2185B' },
    { name: 'Teal', value: 'teal', color: '#00695C' },
  ];

  const awsRegions = [
    { value: 'us-east-1', label: 'US East (N. Virginia)' },
    { value: 'us-west-2', label: 'US West (Oregon)' },
    { value: 'eu-west-1', label: 'Europe (Ireland)' },
    { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
    { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)' },
  ];

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handlePreferenceChange = (field, value) => {
    setPreferences(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    try {
      // Prepare the update data
      const updateData = {
        username: formData.username !== user?.username ? formData.username : undefined,
        full_name: formData.fullName !== user?.full_name ? formData.fullName : undefined,
        aws_region: formData.awsRegion !== user?.aws_region ? formData.awsRegion : undefined,
      };

      // Remove undefined values
      Object.keys(updateData).forEach(key => updateData[key] === undefined && delete updateData[key]);

      // Only make API call if there are changes
      if (Object.keys(updateData).length > 0) {
        await updateUserProfile(updateData);
        toast.success('Profile updated successfully! Your changes will persist across logins.');
      } else {
        toast.info('No changes to save');
      }

      setEditing(false);
    } catch (error) {
      console.error('Profile update error:', error);
      toast.error(error.response?.data?.detail || error.message || 'Failed to update profile');
    }
  };

  const handleCancel = () => {
    setFormData({
      username: user?.username || '',
      email: user?.email || '',
      fullName: user?.full_name || '',
      awsRegion: user?.aws_region || 'us-east-1',
    });
    setEditing(false);
  };

  const SettingCard = ({ title, children, icon, delay = 0 }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5 }}
    >
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" mb={2}>
            {icon}
            <Typography variant="h6" fontWeight="bold" sx={{ ml: 1 }}>
              {title}
            </Typography>
          </Box>
          {children}
        </CardContent>
      </Card>
    </motion.div>
  );

  return (
    <Box sx={{ p: 3, maxWidth: 1000, mx: 'auto' }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Box>
            <Typography variant="h4" fontWeight="bold">
              Settings
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Customize your AWSSET experience
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            <Chip 
              label={user?.provider?.toUpperCase() || 'LOCAL'} 
              color="primary" 
              variant="outlined" 
            />
            {user?.profile_customized && (
              <Chip 
                label="CUSTOMIZED" 
                color="success" 
                variant="filled" 
                size="small"
              />
            )}
          </Box>
        </Box>
      </motion.div>

      {/* Profile Settings */}
      <SettingCard 
        title="Profile Information" 
        icon={<Edit color="primary" />}
        delay={0.1}
      >
        <Box display="flex" alignItems="center" mb={3}>
          <Avatar
            sx={{
              width: 80,
              height: 80,
              bgcolor: 'primary.main',
              fontSize: '2rem',
              mr: 3,
            }}
          >
            {user?.username?.charAt(0).toUpperCase() || 'U'}
          </Avatar>
          <Box>
            <Typography variant="h6">{user?.username}</Typography>
            <Typography variant="body2" color="text.secondary">
              {user?.email}
            </Typography>
            <Button
              size="small"
              startIcon={<CloudUpload />}
              sx={{ mt: 1 }}
              disabled
            >
              Upload Photo
            </Button>
          </Box>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Username"
              value={formData.username}
              onChange={(e) => handleInputChange('username', e.target.value)}
              disabled={!editing}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Email"
              value={formData.email}
              onChange={(e) => handleInputChange('email', e.target.value)}
              disabled={!editing}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Full Name"
              value={formData.fullName}
              onChange={(e) => handleInputChange('fullName', e.target.value)}
              disabled={!editing}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth disabled={!editing}>
              <InputLabel>Default AWS Region</InputLabel>
              <Select
                value={formData.awsRegion}
                onChange={(e) => handleInputChange('awsRegion', e.target.value)}
                label="Default AWS Region"
              >
                {awsRegions.map((region) => (
                  <MenuItem key={region.value} value={region.value}>
                    {region.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {user?.provider !== 'local' && !user?.profile_customized && (
          <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
            <Typography variant="body2">
              Your profile is currently synced with {user?.provider}. Once you edit and save changes, your customizations will persist across logins.
            </Typography>
          </Alert>
        )}

        {user?.profile_customized && (
          <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
            <Typography variant="body2">
              ✓ Your profile has been customized and will remain unchanged when logging in via {user?.provider}.
            </Typography>
          </Alert>
        )}

        <Box display="flex" gap={2} mt={3}>
          {editing ? (
            <>
              <Button
                variant="contained"
                startIcon={<Save />}
                onClick={handleSave}
              >
                Save Changes
              </Button>
              <Button
                variant="outlined"
                startIcon={<Cancel />}
                onClick={handleCancel}
              >
                Cancel
              </Button>
            </>
          ) : (
            <Button
              variant="outlined"
              startIcon={<Edit />}
              onClick={() => setEditing(true)}
            >
              Edit Profile
            </Button>
          )}
        </Box>
      </SettingCard>

      {/* Theme Settings */}
      <SettingCard 
        title="Appearance" 
        icon={<Palette color="primary" />}
        delay={0.2}
      >
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={mode === 'dark'}
                  onChange={toggleMode}
                  icon={<Brightness7 />}
                  checkedIcon={<Brightness4 />}
                />
              }
              label={`${mode === 'dark' ? 'Dark' : 'Light'} Mode`}
            />
          </Grid>

          <Grid item xs={12}>
            <Typography variant="body2" color="text.secondary" mb={2}>
              Accent Color
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {accentColors.map((color) => (
                <motion.div
                  key={color.value}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <IconButton
                    onClick={() => setAccentColor(color.value)}
                    sx={{
                      width: 40,
                      height: 40,
                      bgcolor: color.color,
                      border: accentColor === color.value ? '3px solid' : '1px solid',
                      borderColor: accentColor === color.value ? 'primary.main' : 'divider',
                      '&:hover': {
                        bgcolor: color.color,
                      },
                    }}
                  />
                </motion.div>
              ))}
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={animations}
                  onChange={(e) => setAnimations(e.target.checked)}
                />
              }
              label="Enable Animations"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={compactMode}
                  onChange={(e) => setCompactMode(e.target.checked)}
                />
              }
              label="Compact Mode"
            />
          </Grid>
        </Grid>
      </SettingCard>

      {/* Notifications */}
      <SettingCard 
        title="Notifications" 
        icon={<Notifications color="primary" />}
        delay={0.3}
      >
        <List>
          <ListItem>
            <ListItemIcon>
              <Notifications />
            </ListItemIcon>
            <ListItemText
              primary="Push Notifications"
              secondary="Receive notifications for important events"
            />
            <ListItemSecondaryAction>
              <Switch
                checked={preferences.notifications}
                onChange={(e) => handlePreferenceChange('notifications', e.target.checked)}
              />
            </ListItemSecondaryAction>
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <VolumeUp />
            </ListItemIcon>
            <ListItemText
              primary="Sound Effects"
              secondary="Play sounds for notifications and actions"
            />
            <ListItemSecondaryAction>
              <Switch
                checked={preferences.soundEnabled}
                onChange={(e) => handlePreferenceChange('soundEnabled', e.target.checked)}
              />
            </ListItemSecondaryAction>
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <Speed />
            </ListItemIcon>
            <ListItemText
              primary="Auto Refresh"
              secondary="Automatically refresh data"
            />
            <ListItemSecondaryAction>
              <Switch
                checked={preferences.autoRefresh}
                onChange={(e) => handlePreferenceChange('autoRefresh', e.target.checked)}
              />
            </ListItemSecondaryAction>
          </ListItem>
        </List>

        {preferences.autoRefresh && (
          <Box sx={{ px: 2, pb: 2 }}>
            <Typography variant="body2" color="text.secondary" mb={1}>
              Refresh Interval: {preferences.refreshInterval} seconds
            </Typography>
            <Slider
              value={preferences.refreshInterval}
              onChange={(e, value) => handlePreferenceChange('refreshInterval', value)}
              min={10}
              max={300}
              step={10}
              marks={[
                { value: 10, label: '10s' },
                { value: 60, label: '1m' },
                { value: 300, label: '5m' },
              ]}
              valueLabelDisplay="auto"
            />
          </Box>
        )}
      </SettingCard>

      {/* Privacy & Security */}
      <SettingCard 
        title="Privacy & Security" 
        icon={<Security color="primary" />}
        delay={0.4}
      >
        <List>
          <ListItem>
            <ListItemIcon>
              <Psychology />
            </ListItemIcon>
            <ListItemText
              primary="Chat History"
              secondary="Save chat conversations for future reference"
            />
            <ListItemSecondaryAction>
              <Switch
                checked={preferences.chatHistory}
                onChange={(e) => handlePreferenceChange('chatHistory', e.target.checked)}
              />
            </ListItemSecondaryAction>
          </ListItem>

          <ListItem>
            <ListItemIcon>
              <Visibility />
            </ListItemIcon>
            <ListItemText
              primary="Analytics"
              secondary="Help improve the service by sharing usage data"
            />
            <ListItemSecondaryAction>
              <Switch
                checked={preferences.analyticsOptIn}
                onChange={(e) => handlePreferenceChange('analyticsOptIn', e.target.checked)}
              />
            </ListItemSecondaryAction>
          </ListItem>
        </List>

        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            Your AWS credentials are encrypted and stored securely. We never store your actual AWS keys in plain text.
          </Typography>
        </Alert>
      </SettingCard>

      {/* Advanced Settings */}
      <SettingCard 
        title="Advanced" 
        icon={<Memory color="primary" />}
        delay={0.5}
      >
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Language</InputLabel>
              <Select
                value={preferences.language}
                onChange={(e) => handlePreferenceChange('language', e.target.value)}
                label="Language"
              >
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="es">Español</MenuItem>
                <MenuItem value="fr">Français</MenuItem>
                <MenuItem value="de">Deutsch</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Timezone</InputLabel>
              <Select
                value={preferences.timezone}
                onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                label="Timezone"
              >
                <MenuItem value="UTC">UTC</MenuItem>
                <MenuItem value="America/New_York">Eastern Time</MenuItem>
                <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
                <MenuItem value="Europe/London">London</MenuItem>
                <MenuItem value="Asia/Tokyo">Tokyo</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        <Box display="flex" gap={2} mt={3}>
          <Button variant="outlined" color="warning">
            Export Data
          </Button>
          <Button variant="outlined" color="error">
            Reset Settings
          </Button>
        </Box>
      </SettingCard>
    </Box>
  );
};

export default UserSettings;
