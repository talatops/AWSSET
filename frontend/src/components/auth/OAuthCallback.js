import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Box, CircularProgress, Typography, Alert, Button } from '@mui/material';
import { motion } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import { debugLog } from '../../utils/env';

// Global flag to prevent multiple OAuth callback executions
let isOAuthCallbackProcessing = false;

const OAuthCallback = ({ provider }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { handleOAuthCallback } = useAuth();
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(true);

  useEffect(() => {
    const processCallback = async () => {
      // Prevent multiple executions using global flag
      if (isOAuthCallbackProcessing) {
        debugLog('OAuth Callback - Already processing, skipping...');
        return;
      }

      try {
        isOAuthCallbackProcessing = true;

        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');

        debugLog('OAuth Callback - Processing:', { code: code?.substring(0, 10) + '...', state: state?.substring(0, 10) + '...', error, provider });

        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        if (!code || !state) {
          throw new Error('Missing authorization code or state parameter');
        }

        debugLog('OAuth Callback - Calling handleOAuthCallback...');
        await handleOAuthCallback(code, state, provider);
        
        debugLog('OAuth Callback - Success! Redirecting to dashboard...');
        // Success - redirect to dashboard
        navigate('/dashboard', { replace: true });
        
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError(err.message || 'Authentication failed');
        setProcessing(false);
        isOAuthCallbackProcessing = false; // Reset on error
      }
    };

    processCallback();
  }, [searchParams, handleOAuthCallback, provider, navigate]);

  const handleRetry = () => {
    navigate('/login', { replace: true });
  };

  if (processing) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        bgcolor="background.default"
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <Box textAlign="center">
            <CircularProgress size={60} thickness={4} />
            <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
              Completing {provider} sign-in...
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Please wait while we securely authenticate your account
            </Typography>
          </Box>
        </motion.div>
      </Box>
    );
  }

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="100vh"
      bgcolor="background.default"
      p={3}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        style={{ maxWidth: 400, width: '100%' }}
      >
        <Alert 
          severity="error" 
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={handleRetry}>
              Try Again
            </Button>
          }
        >
          <Typography variant="h6" gutterBottom>
            Authentication Failed
          </Typography>
          <Typography variant="body2">
            {error}
          </Typography>
        </Alert>
      </motion.div>
    </Box>
  );
};

export default OAuthCallback;
