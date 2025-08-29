import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Box,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stepper,
  Step,
  StepLabel,
  Paper,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
} from '@mui/material';
import {
  Security,
  CloudQueue,
  CheckCircle,
  Warning,
  Info,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useAWS } from '../../hooks/useAWS';

const AWSCredentialsSetup = ({ open, onClose, onSuccess }) => {
  const { storeCredentials, validateCredentials, testPermissions, getRegions, loading } = useAWS();
  
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    access_key: '',
    secret_key: '',
    region: 'us-east-1',
  });
  const [showSecret, setShowSecret] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [permissionResults, setPermissionResults] = useState(null);
  const [regions, setRegions] = useState({});

  const steps = ['Enter Credentials', 'Validate', 'Test Permissions', 'Complete'];

  useEffect(() => {
    if (open) {
      loadRegions();
    }
  }, [open]);

  const loadRegions = async () => {
    try {
      const regionData = await getRegions();
      setRegions(regionData);
    } catch (error) {
      console.error('Failed to load regions:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = async () => {
    if (step === 0) {
      // Validate credentials
      try {
        const result = await validateCredentials(formData);
        setValidationResult(result);
        if (result.valid) {
          setStep(1);
        }
      } catch (error) {
        // Error handled by hook
      }
    } else if (step === 1) {
      // Test permissions
      try {
        const result = await testPermissions('ec2', formData);
        setPermissionResults(result);
        setStep(2);
      } catch (error) {
        // Error handled by hook
      }
    } else if (step === 2) {
      // Store credentials
      try {
        await storeCredentials(formData);
        setStep(3);
        setTimeout(() => {
          onSuccess?.();
          handleClose();
        }, 2000);
      } catch (error) {
        // Error handled by hook
      }
    }
  };

  const handleBack = () => {
    setStep(prev => Math.max(0, prev - 1));
  };

  const handleClose = () => {
    setStep(0);
    setFormData({ access_key: '', secret_key: '', region: 'us-east-1' });
    setValidationResult(null);
    setPermissionResults(null);
    onClose();
  };

  const isStepValid = () => {
    if (step === 0) {
      // AWS Access Key ID: 20 characters, starts with AKIA
      // AWS Secret Access Key: 40 characters
      const accessKeyValid = formData.access_key.length >= 20 && formData.access_key.startsWith('AKIA');
      const secretKeyValid = formData.secret_key.length >= 40;
      const regionValid = formData.region && formData.region.length > 0;
      return accessKeyValid && secretKeyValid && regionValid;
    }
    if (step === 1) {
      return validationResult?.valid;
    }
    if (step === 2) {
      // Allow proceeding even if some permissions are limited, as long as we have results
      return permissionResults !== null;
    }
    return true;
  };

  const renderStepContent = () => {
    switch (step) {
      case 0:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              AWS Credentials
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Enter your AWS Access Key ID and Secret Access Key. These will be encrypted and stored securely.
            </Typography>
            
            <TextField
              fullWidth
              label="AWS Access Key ID"
              value={formData.access_key}
              onChange={(e) => handleInputChange('access_key', e.target.value)}
              margin="normal"
              placeholder="AKIA..."
              helperText={`20-character access key starting with AKIA (${formData.access_key.length}/20)`}
              error={formData.access_key.length > 0 && (formData.access_key.length < 20 || !formData.access_key.startsWith('AKIA'))}
            />
            
            <TextField
              fullWidth
              label="AWS Secret Access Key"
              type={showSecret ? 'text' : 'password'}
              value={formData.secret_key}
              onChange={(e) => handleInputChange('secret_key', e.target.value)}
              margin="normal"
              placeholder="40-character secret key"
              helperText={`40-character secret access key (${formData.secret_key.length}/40)`}
              error={formData.secret_key.length > 0 && formData.secret_key.length < 40}
              InputProps={{
                endAdornment: (
                  <IconButton onClick={() => setShowSecret(!showSecret)} edge="end">
                    {showSecret ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                ),
              }}
            />
            
            <FormControl fullWidth margin="normal">
              <InputLabel>Default Region</InputLabel>
              <Select
                value={formData.region}
                onChange={(e) => handleInputChange('region', e.target.value)}
                label="Default Region"
              >
                {Object.entries(regions).map(([code, name]) => (
                  <MenuItem key={code} value={code}>
                    {name} ({code})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                Your credentials will be encrypted using AES-256 encryption before storage.
              </Typography>
            </Alert>
          </Box>
        );

      case 1:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Credential Validation
            </Typography>
            
            {validationResult ? (
              <Box>
                {validationResult.valid ? (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      ✅ Credentials validated successfully!
                    </Typography>
                  </Alert>
                ) : (
                  <Alert severity="error" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      ❌ {validationResult.error}
                    </Typography>
                  </Alert>
                )}
                
                {validationResult.account_info && (
                  <Paper elevation={1} sx={{ p: 2, mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Account Information:
                    </Typography>
                    <Typography variant="body2">
                      <strong>Account ID:</strong> {validationResult.account_info.account_id}
                    </Typography>
                    <Typography variant="body2">
                      <strong>User ARN:</strong> {validationResult.account_info.arn}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Region:</strong> {formData.region}
                    </Typography>
                  </Paper>
                )}
              </Box>
            ) : (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            )}
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Permission Testing
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Testing EC2 permissions for your AWS account...
            </Typography>
            
            {permissionResults ? (
              <Box>
                <Alert 
                  severity={permissionResults.success ? "success" : "warning"} 
                  sx={{ mb: 2 }}
                >
                  <Typography variant="body2">
                    {permissionResults.success ? 
                      "✅ Permission testing completed" : 
                      "⚠️ Some permissions may be limited"}
                  </Typography>
                </Alert>
                
                <Typography variant="subtitle2" gutterBottom>
                  EC2 Permissions:
                </Typography>
                <List dense>
                  {Object.entries(permissionResults.permissions || {}).map(([permission, hasAccess]) => {
                    if (permission.endsWith('_error')) return null;
                    return (
                      <ListItem key={permission}>
                        <ListItemIcon>
                          {hasAccess ? 
                            <CheckCircle color="success" /> : 
                            <Warning color="warning" />}
                        </ListItemIcon>
                        <ListItemText 
                          primary={permission.replace('ec2:', '')} 
                          secondary={hasAccess ? 'Allowed' : 'Denied'}
                        />
                      </ListItem>
                    );
                  })}
                </List>
              </Box>
            ) : (
              <Box display="flex" justifyContent="center" p={3}>
                <CircularProgress />
              </Box>
            )}
          </Box>
        );

      case 3:
        return (
          <Box textAlign="center">
            <CheckCircle color="success" sx={{ fontSize: 64, mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Setup Complete!
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your AWS credentials have been securely stored and validated.
              You can now use AWS services through the dashboard.
            </Typography>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog 
      open={open} 
      onClose={handleClose} 
      maxWidth="md" 
      fullWidth
      PaperProps={{
        component: motion.div,
        initial: { opacity: 0, scale: 0.9 },
        animate: { opacity: 1, scale: 1 },
        transition: { duration: 0.3 }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <Security color="primary" />
          AWS Credentials Setup
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Stepper activeStep={step} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        {renderStepContent()}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={handleClose}>
          Cancel
        </Button>
        {step > 0 && step < 3 && (
          <Button onClick={handleBack}>
            Back
          </Button>
        )}
        {step < 3 && (
          <Button 
            variant="contained" 
            onClick={handleNext}
            disabled={!isStepValid() || loading}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            {step === 2 ? 'Store Credentials' : 'Next'}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default AWSCredentialsSetup;
