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

  // DEVELOPMENT MODE: Enable demo mode to bypass authentication
  const DEMO_MODE = true;

  // Show loading spinner while checking authentication (skip in demo mode)
  if (isLoading && !DEMO_MODE) {
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

  // In demo mode, treat as authenticated
  const isAuthenticatedOrDemo = DEMO_MODE || isAuthenticated;

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
              isAuthenticatedOrDemo ? <Navigate to="/dashboard" replace /> : <LoginPage />
            }
          />
          <Route
            path="/register"
            element={
              isAuthenticatedOrDemo ? <Navigate to="/dashboard" replace /> : <RegisterPage />
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
                to={isAuthenticatedOrDemo ? "/dashboard" : "/login"}
                replace
              />
            }
          />

          {/* Catch all other routes */}
          <Route
            path="*"
            element={
              <Navigate
                to={isAuthenticatedOrDemo ? "/dashboard" : "/login"}
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
