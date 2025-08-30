import React, { createContext, useContext, useReducer, useEffect, useCallback } from 'react';
import axios from 'axios';
import jwtDecode from 'jwt-decode';
import { toast } from 'react-toastify';
import { getApiUrl } from '../utils/env';

const AuthContext = createContext();

// Action types
const AUTH_ACTIONS = {
  LOGIN_START: 'LOGIN_START',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILURE: 'LOGIN_FAILURE',
  LOGOUT: 'LOGOUT',
  SET_USER: 'SET_USER',
  SET_LOADING: 'SET_LOADING',
  REFRESH_TOKEN: 'REFRESH_TOKEN',
};

// Initial state
const initialState = {
  user: null,
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Auth reducer
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.LOGIN_START:
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.access_token,
        refreshToken: action.payload.refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case AUTH_ACTIONS.LOGIN_FAILURE:
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        token: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    case AUTH_ACTIONS.SET_USER:
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    case AUTH_ACTIONS.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload,
      };
    case AUTH_ACTIONS.REFRESH_TOKEN:
      return {
        ...state,
        token: action.payload.access_token,
        refreshToken: action.payload.refresh_token,
      };
    default:
      return state;
  }
};

// API configuration
const API_BASE_URL = getApiUrl();

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Set up axios interceptors
  useEffect(() => {
    // Request interceptor to add token
    const requestInterceptor = api.interceptors.request.use(
      (config) => {
        if (state.token) {
          config.headers.Authorization = `Bearer ${state.token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle token refresh
    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          if (state.refreshToken) {
            try {
              const response = await refreshToken();
              if (response.access_token) {
                originalRequest.headers.Authorization = `Bearer ${response.access_token}`;
                return api(originalRequest);
              }
            } catch (refreshError) {
              logout();
              return Promise.reject(refreshError);
            }
          } else {
            logout();
          }
        }

        return Promise.reject(error);
      }
    );

    return () => {
      api.interceptors.request.eject(requestInterceptor);
      api.interceptors.response.eject(responseInterceptor);
    };
  }, [state.token, state.refreshToken]);

  // Check if user is authenticated on app load
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token');
      const refreshTokenStored = localStorage.getItem('refresh_token');

      if (token && refreshTokenStored) {
        try {
          // Check if token is valid
          const decodedToken = jwtDecode(token);
          const currentTime = Date.now() / 1000;

          if (decodedToken.exp > currentTime) {
            // Token is valid, get user profile
            const userResponse = await api.get('/api/auth/me');
            dispatch({
              type: AUTH_ACTIONS.SET_USER,
              payload: userResponse.data,
            });
          } else {
            // Token expired, try to refresh
            await refreshToken();
          }
        } catch (error) {
          console.error('Auth initialization error:', error);
          logout();
        }
      } else {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      }
    };

    initializeAuth();
  }, []);

  // Auth functions
  const login = async (email, password) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });

      const response = await api.post('/api/auth/login', {
        email,
        password,
      });

      const { access_token, refresh_token, user } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user,
          access_token,
          refresh_token,
        },
      });

      toast.success(`Welcome back, ${user.username}!`);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Login failed';
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage,
      });
      toast.error(errorMessage);
      throw error;
    }
  };

  const register = async (userData) => {
    try {
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });

      const response = await api.post('/api/auth/register', userData);

      const { access_token, refresh_token, user } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user,
          access_token,
          refresh_token,
        },
      });

              toast.success(`Welcome to AWSSET, ${user.username}!`);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage,
      });
      toast.error(errorMessage);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (state.token) {
        await api.post('/api/auth/logout');
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');

      dispatch({ type: AUTH_ACTIONS.LOGOUT });
      toast.info('You have been logged out');
    }
  };

  const refreshToken = async () => {
    try {
      const refreshTokenStored = localStorage.getItem('refresh_token');
      if (!refreshTokenStored) {
        throw new Error('No refresh token available');
      }

      const response = await api.post('/api/auth/refresh', {
        refresh_token: refreshTokenStored,
      });

      const { access_token, refresh_token, user } = response.data;

      // Update stored tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      dispatch({
        type: AUTH_ACTIONS.REFRESH_TOKEN,
        payload: {
          access_token,
          refresh_token,
        },
      });

      // Update user if provided
      if (user) {
        dispatch({
          type: AUTH_ACTIONS.SET_USER,
          payload: user,
        });
      }

      return response.data;
    } catch (error) {
      console.error('Token refresh error:', error);
      logout();
      throw error;
    }
  };

  const initializeOAuth = async (provider) => {
    try {
      const response = await api.get(`/api/auth/oauth/${provider}`);
      return response.data;
    } catch (error) {
      const errorMessage = error.response?.data?.detail || `${provider} OAuth initialization failed`;
      toast.error(errorMessage);
      throw error;
    }
  };

  const handleOAuthCallback = useCallback(async (code, state, provider) => {
    try {
      console.log('AuthContext - Starting OAuth callback for:', provider);
      dispatch({ type: AUTH_ACTIONS.LOGIN_START });

      console.log('AuthContext - Making API call to:', `${API_BASE_URL}/api/auth/oauth/callback`);
      const response = await api.post('/api/auth/oauth/callback', {
        code,
        state,
        provider,
      });

      console.log('AuthContext - OAuth callback response received:', response.status);
      const { access_token, refresh_token, user } = response.data;

      // Store tokens
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      dispatch({
        type: AUTH_ACTIONS.LOGIN_SUCCESS,
        payload: {
          user,
          access_token,
          refresh_token,
        },
      });

      toast.success(`Welcome, ${user.username}! Logged in via ${provider}`);
      return response.data;
    } catch (error) {
      console.error('AuthContext - OAuth callback error:', error);
      console.error('AuthContext - Error response:', error.response?.data);
      const errorMessage = error.response?.data?.detail || `${provider} OAuth failed`;
      dispatch({
        type: AUTH_ACTIONS.LOGIN_FAILURE,
        payload: errorMessage,
      });
      toast.error(errorMessage);
      throw error;
    }
  }, []);

  const getOAuthStatus = useCallback(async () => {
    try {
      const response = await api.get('/api/auth/oauth/status');
      return response.data;
    } catch (error) {
      console.error('OAuth status error:', error);
      return { google: { available: false }, proton: { available: false } };
    }
  }, []);

  const updateUserProfile = useCallback(async (profileData) => {
    try {
      const response = await api.put('/api/auth/me', profileData);
      
      // Update user in context
      dispatch({
        type: AUTH_ACTIONS.SET_USER,
        payload: response.data,
      });
      
      return response.data;
    } catch (error) {
      console.error('Profile update error:', error);
      throw error;
    }
  }, []);

  const value = {
    ...state,
    login,
    register,
    logout,
    refreshToken,
    initializeOAuth,
    handleOAuthCallback,
    getOAuthStatus,
    updateUserProfile,
    api, // Expose API instance for other components
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
