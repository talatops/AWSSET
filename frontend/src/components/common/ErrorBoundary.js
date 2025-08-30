import React from 'react';
import { Box, Card, CardContent, Typography, Button } from '@mui/material';
import { ErrorOutline, RefreshOutlined } from '@mui/icons-material';
import { motion } from 'framer-motion';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
    });
    
    // Log error to monitoring service
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  render() {
    if (this.state.hasError) {
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
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <Card sx={{ maxWidth: 500, textAlign: 'center' }}>
              <CardContent sx={{ p: 4 }}>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                >
                  <ErrorOutline 
                    sx={{ 
                      fontSize: 64, 
                      color: 'error.main', 
                      mb: 2 
                    }} 
                  />
                </motion.div>
                
                <Typography variant="h4" gutterBottom color="error">
                  Oops! Something went wrong
                </Typography>
                
                <Typography variant="body1" color="text.secondary" mb={3}>
                  An unexpected error occurred in the AWSSET dashboard. 
                  Don't worry, your data is safe.
                </Typography>

                <Box display="flex" gap={2} justifyContent="center">
                  <Button
                    variant="contained"
                    onClick={this.handleReset}
                    startIcon={<RefreshOutlined />}
                  >
                    Try Again
                  </Button>
                  
                  <Button
                    variant="outlined"
                    onClick={this.handleReload}
                  >
                    Reload Page
                  </Button>
                </Box>

                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <Box mt={3} textAlign="left">
                    <Typography variant="h6" color="error" gutterBottom>
                      Error Details (Development Only):
                    </Typography>
                    <Box
                      component="pre"
                      sx={{
                        backgroundColor: 'background.elevation1',
                        p: 2,
                        borderRadius: 1,
                        overflow: 'auto',
                        fontSize: '0.75rem',
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      {this.state.error.toString()}
                      {this.state.errorInfo?.componentStack}
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
