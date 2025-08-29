import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Divider,
  Alert,
  IconButton,
  InputAdornment,
  Link,
  Chip,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Google as GoogleIcon,
  Email as EmailIcon,
  Security as SecurityIcon,
} from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const LoginPage = () => {
  const { login, initializeOAuth, getOAuthStatus, error, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [formErrors, setFormErrors] = useState({});
  const [oauthStatus, setOauthStatus] = useState({
    google: { available: false },
    proton: { available: false }
  });

  useEffect(() => {
    // Check OAuth provider availability
    const checkOAuthStatus = async () => {
      try {
        const status = await getOAuthStatus();
        setOauthStatus(status);
      } catch (error) {
        console.error('Failed to check OAuth status:', error);
      }
    };
    
    checkOAuthStatus();
  }, [getOAuthStatus]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear field error when user starts typing
    if (formErrors[name]) {
      setFormErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters long';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await login(formData.email, formData.password);
    } catch (error) {
      // Error is handled by the AuthContext
      console.error('Login error:', error);
    }
  };

  const handleOAuthLogin = async (provider) => {
    try {
      const oauthData = await initializeOAuth(provider);
      if (oauthData.auth_url) {
        window.location.href = oauthData.auth_url;
      }
    } catch (error) {
      console.error(`${provider} OAuth error:`, error);
    }
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: 2,
      }}
    >
      <Card
        sx={{
          width: '100%',
          maxWidth: 450,
          boxShadow: '0 8px 40px rgba(0,0,0,0.12)',
          borderRadius: 3,
        }}
      >
        <CardContent sx={{ p: 4 }}>
          {/* Header */}
          <Box textAlign="center" mb={3}>
            <SecurityIcon sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h4" fontWeight="bold" color="primary.main">
              AWS Chatbot
            </Typography>
            <Typography variant="body1" color="text.secondary" mt={1}>
              AI-Powered AWS Management Dashboard
            </Typography>
          </Box>

          {/* Error Alert */}
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {/* Login Form */}
          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              name="email"
              label="Email Address"
              type="email"
              value={formData.email}
              onChange={handleInputChange}
              error={!!formErrors.email}
              helperText={formErrors.email}
              margin="normal"
              autoComplete="email"
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailIcon color="action" />
                  </InputAdornment>
                ),
              }}
            />

            <TextField
              fullWidth
              name="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={handleInputChange}
              error={!!formErrors.password}
              helperText={formErrors.password}
              margin="normal"
              autoComplete="current-password"
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={isLoading}
              sx={{
                mt: 3,
                mb: 2,
                py: 1.5,
                fontSize: '1rem',
                fontWeight: 600,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                },
              }}
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </Button>
          </Box>

          {/* OAuth Options */}
          {(oauthStatus.google.available || oauthStatus.proton.available) && (
            <>
              <Divider sx={{ my: 3 }}>
                <Typography variant="body2" color="text.secondary">
                  Or continue with
                </Typography>
              </Divider>

              <Box display="flex" flexDirection="column" gap={2}>
                {oauthStatus.google.available && (
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<GoogleIcon />}
                    onClick={() => handleOAuthLogin('google')}
                    sx={{
                      py: 1.5,
                      borderColor: '#db4437',
                      color: '#db4437',
                      '&:hover': {
                        borderColor: '#c23321',
                        backgroundColor: 'rgba(219, 68, 55, 0.04)',
                      },
                    }}
                  >
                    Continue with Google
                  </Button>
                )}

                {oauthStatus.proton.available && (
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<EmailIcon />}
                    onClick={() => handleOAuthLogin('proton')}
                    sx={{
                      py: 1.5,
                      borderColor: '#6d4aae',
                      color: '#6d4aae',
                      '&:hover': {
                        borderColor: '#5a3d91',
                        backgroundColor: 'rgba(109, 74, 174, 0.04)',
                      },
                    }}
                  >
                    Continue with Proton
                    {!oauthStatus.proton.configured && (
                      <Chip
                        label="Beta"
                        size="small"
                        sx={{ ml: 1, fontSize: '0.7rem' }}
                      />
                    )}
                  </Button>
                )}
              </Box>
            </>
          )}

          {/* Register Link */}
          <Box textAlign="center" mt={3}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{' '}
              <Link
                component={RouterLink}
                to="/register"
                sx={{
                  fontWeight: 600,
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                  },
                }}
              >
                Sign up here
              </Link>
            </Typography>
          </Box>

          {/* OAuth Status Info */}
          {(!oauthStatus.google.available && !oauthStatus.proton.available) && (
            <Box mt={3}>
              <Alert severity="info" sx={{ fontSize: '0.875rem' }}>
                <Typography variant="body2">
                  OAuth providers not configured. Contact administrator to enable 
                  Google or Proton sign-in options.
                </Typography>
              </Alert>
            </Box>
          )}

          {/* Proton Free Tier Notice */}
          {oauthStatus.proton.available && !oauthStatus.proton.configured && (
            <Box mt={2}>
              <Alert severity="warning" sx={{ fontSize: '0.875rem' }}>
                <Typography variant="body2">
                  Proton OAuth may have limited availability on free tier accounts.
                </Typography>
              </Alert>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default LoginPage;
