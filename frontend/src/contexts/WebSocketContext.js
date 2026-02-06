import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import { useAuth } from './AuthContext';
import { debugLog } from '../utils/env';

const WebSocketContext = createContext();

export const WebSocketProvider = ({ children }) => {
  const { token, isAuthenticated } = useAuth();
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [typing, setTyping] = useState(false);
  const [awsStats, setAwsStats] = useState(null);
  const [systemStatus, setSystemStatus] = useState(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const pingIntervalRef = useRef(null);
  const isUnmountedRef = useRef(false);
  const systemStatusUpdateTimeoutRef = useRef(null);
  const maxReconnectAttempts = 5;

  const WEBSOCKET_URL = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/realtime';

  useEffect(() => {
    isUnmountedRef.current = false;
    
    if (isAuthenticated && token) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      isUnmountedRef.current = true;
      cleanup();
    };
  }, [isAuthenticated, token]);

  const connectWebSocket = () => {
    try {
      // For WebSocket endpoint, we need to use a different approach
      const wsUrl = `${WEBSOCKET_URL}?token=${encodeURIComponent(token)}`;
      debugLog('🔗 Connecting to WebSocket:', wsUrl);
      
      const newSocket = new WebSocket(wsUrl);
      
      newSocket.onopen = () => {
        debugLog('WebSocket connected');
        if (!isUnmountedRef.current) {
          setConnected(true);
          setSocket(newSocket);
          reconnectAttempts.current = 0;
          
          // Clear any existing reconnection timeout
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
          }

          // Start keepalive ping
          startPingInterval(newSocket);
        }
      };

      newSocket.onclose = (event) => {
        debugLog('WebSocket disconnected:', event.reason);
        stopPingInterval();
        
        if (!isUnmountedRef.current) {
          setConnected(false);
          setSocket(null);

          if (event.code === 1008 || event.code === 1011) {
            // Server initiated disconnect, don't reconnect
            debugLog('Server disconnected WebSocket');
          } else {
            // Connection lost, attempt to reconnect
            scheduleReconnect();
          }
        }
      };

      newSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnected(false);
        scheduleReconnect();
      };

      newSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      scheduleReconnect();
    }
  };

  // Check if user is on Settings page to prevent unnecessary updates
  const isOnSettingsPage = () => {
    return window.location.pathname.includes('/settings') || 
           window.location.pathname.includes('/dashboard/settings');
  };

  const handleWebSocketMessage = (data) => {
    debugLog('📨 Received WebSocket message:', data);
    
    // Check if component is still mounted before updating state
    if (isUnmountedRef.current) {
      debugLog('📨 Component unmounted, skipping message processing');
      return;
    }
    
    // Skip system status updates if user is on Settings page to prevent blinking
    if (data.type === 'system_status_update' && isOnSettingsPage()) {
      debugLog('🔧 Skipping system status update - user on Settings page');
      return;
    }
    
    switch (data.type) {
      case 'aws_stats_update':
        debugLog('📊 Updating AWS stats:', data.data);
        setAwsStats(data.data);
        break;
        
      case 'system_status_update':
        debugLog('🔧 Updating system status:', data.data);
        // Debounce system status updates to prevent rapid re-renders
        if (systemStatusUpdateTimeoutRef.current) {
          clearTimeout(systemStatusUpdateTimeoutRef.current);
        }
        systemStatusUpdateTimeoutRef.current = setTimeout(() => {
          // Only update if the status actually changed
          setSystemStatus(prevStatus => {
            if (JSON.stringify(prevStatus) === JSON.stringify(data.data)) {
              debugLog('🔧 System status unchanged, skipping update');
              return prevStatus;
            }
            debugLog('🔧 System status changed, updating');
            return data.data;
          });
        }, 1000); // Wait 1 second before updating
        break;
        
      case 'notification':
        handleNotification(data.data);
        break;
        
      case 'pong':
        debugLog('🏓 Received pong');
        break;
        
      case 'message':
        addMessage({
          id: Date.now(),
          type: 'bot',
          content: data.message || data.data?.message,
          timestamp: new Date(),
          metadata: data.metadata,
        });
        break;
        
      case 'error':
        console.error('❌ WebSocket error:', data.error);
        toast.error(data.error);
        break;
        
      default:
        debugLog('🔍 Unknown message type:', data.type, data);
    }
  };

  const handleNotification = (notificationData) => {
    switch (notificationData.type) {
      case 'info':
        toast.info(notificationData.message);
        break;
      case 'success':
        toast.success(notificationData.message);
        break;
      case 'warning':
        toast.warning(notificationData.message);
        break;
      case 'error':
        toast.error(notificationData.message);
        break;
      default:
        toast(notificationData.message);
    }
  };

  const disconnectWebSocket = () => {
    stopPingInterval();
    
    // Clear any pending system status updates
    if (systemStatusUpdateTimeoutRef.current) {
      clearTimeout(systemStatusUpdateTimeoutRef.current);
      systemStatusUpdateTimeoutRef.current = null;
    }
    
    if (socket) {
      socket.close();
      if (!isUnmountedRef.current) {
        setSocket(null);
        setConnected(false);
      }
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  };

  // Enhanced cleanup function
  const cleanup = () => {
    stopPingInterval();
    
    if (systemStatusUpdateTimeoutRef.current) {
      clearTimeout(systemStatusUpdateTimeoutRef.current);
      systemStatusUpdateTimeoutRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (socket) {
      socket.close();
    }
  };

  const startPingInterval = (socket) => {
    stopPingInterval(); // Clear any existing interval
    
    pingIntervalRef.current = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN && !isUnmountedRef.current) {
        try {
          socket.send(JSON.stringify({ type: 'ping' }));
          debugLog('🏓 Sent ping');
        } catch (error) {
          console.error('Failed to send ping:', error);
        }
      }
    }, 120000); // Send ping every 120 seconds (reduced frequency to match backend)
  };

  const stopPingInterval = () => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  };

  const scheduleReconnect = () => {
    if (isUnmountedRef.current) {
      return; // Don't reconnect if component is unmounted
    }
    
    if (reconnectAttempts.current >= maxReconnectAttempts) {
      toast.error('Failed to connect to chat server. Please refresh the page.');
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000); // Exponential backoff, max 30s
    reconnectAttempts.current += 1;

    debugLog(`Scheduling reconnection attempt ${reconnectAttempts.current} in ${delay}ms`);

    reconnectTimeoutRef.current = setTimeout(() => {
      if (isAuthenticated && token && !isUnmountedRef.current) {
        connectWebSocket();
      }
    }, delay);
  };

  const sendMessage = (message, metadata = {}) => {
    if (!socket || !connected) {
      toast.error('Not connected to real-time server');
      return false;
    }

    try {
      // Add user message to local state
      const userMessage = {
        id: Date.now(),
        type: 'user',
        content: message,
        timestamp: new Date(),
        metadata,
      };
      addMessage(userMessage);

      // Send to server
      socket.send(JSON.stringify({
        type: 'user_message',
        message,
        metadata,
        timestamp: new Date().toISOString(),
      }));

      return true;
    } catch (error) {
      console.error('Failed to send message:', error);
      toast.error('Failed to send message');
      return false;
    }
  };

  const addMessage = (message) => {
    if (!isUnmountedRef.current) {
      setMessages(prev => [...prev, message]);
    }
  };

  const clearMessages = () => {
    setMessages([]);
  };

  const sendWebSocketMessage = (type, data = {}) => {
    if (socket && connected) {
      try {
        socket.send(JSON.stringify({
          type,
          ...data
        }));
        return true;
      } catch (error) {
        console.error(`Failed to send WebSocket message (${type}):`, error);
        return false;
      }
    }
    return false;
  };

  const joinRoom = (roomId) => {
    sendWebSocketMessage('join_room', { room: roomId });
  };

  const leaveRoom = (roomId) => {
    sendWebSocketMessage('leave_room', { room: roomId });
  };

  const sendTypingStart = () => {
    sendWebSocketMessage('typing_start');
  };

  const sendTypingStop = () => {
    sendWebSocketMessage('typing_stop');
  };

  const requestAwsStats = () => {
    debugLog('📡 Requesting AWS stats via WebSocket...');
    return sendWebSocketMessage('request_aws_stats');
  };

  const requestSystemStatus = () => {
    debugLog('📡 Requesting system status via WebSocket...');
    return sendWebSocketMessage('request_system_status');
  };

  const value = {
    socket,
    connected,
    messages,
    typing,
    awsStats,
    systemStatus,
    sendMessage,
    addMessage,
    clearMessages,
    joinRoom,
    leaveRoom,
    sendTypingStart,
    sendTypingStop,
    requestAwsStats,
    requestSystemStatus,
    reconnect: connectWebSocket,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

export default WebSocketContext;
