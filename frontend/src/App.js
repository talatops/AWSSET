import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import { useAuth } from './contexts/AuthContext';

// Components
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import OAuthCallback from './components/auth/OAuthCallback';
import Dashboard from './components/dashboard/Dashboard';
import ProtectedRoute from './components/common/ProtectedRoute';
import ErrorBoundary from './components/common/ErrorBoundary';

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
        bgcolor="#f7fafc"
      >
        <Box textAlign="center">
          <CircularProgress size={60} thickness={4} />
          <Box mt={2} color="text.secondary">
            Loading AWSSET...
          </Box>
        </Box>
      </Box>
    );
  }

  return (
    <ErrorBoundary>
      <Box minHeight="100vh" bgcolor="#f7fafc">
        <Routes>
          {/* OAuth callback routes - MUST be first to prevent wildcard interference */}
          <Route
            path="/auth/google/callback"
            element={<OAuthCallback provider="google" />}
          />
          <Route
            path="/auth/proton/callback"
            element={<OAuthCallback provider="proton" />}
          />

          {/* Public routes */}
          <Route
            path="/login"
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
            }
          />
          <Route
            path="/register"
            element={
              isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />
            }
          />

          {/* Protected routes */}
          <Route
            path="/dashboard/*"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          {/* Default redirects */}
          <Route
            path="/"
            element={
              <Navigate
                to={isAuthenticated ? "/dashboard" : "/login"}
                replace
              />
            }
          />

          {/* Catch all other routes */}
          <Route
            path="*"
            element={
              <Navigate
                to={isAuthenticated ? "/dashboard" : "/login"}
                replace
              />
            }
          />
        </Routes>
      </Box>
    </ErrorBoundary>
  );
}

export default App;
