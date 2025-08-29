import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { toast } from 'react-toastify';
import { useAuth } from './AuthContext';

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
  const maxReconnectAttempts = 5;

  const WEBSOCKET_URL = process.env.REACT_APP_WEBSOCKET_URL || 'ws://localhost:8000/ws/realtime';

  useEffect(() => {
    if (isAuthenticated && token) {
      connectWebSocket();
    } else {
      disconnectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [isAuthenticated, token]);

  const connectWebSocket = () => {
    try {
      // For WebSocket endpoint, we need to use a different approach
      const wsUrl = `${WEBSOCKET_URL}?token=${encodeURIComponent(token)}`;
      console.log('🔗 Connecting to WebSocket:', wsUrl);
      
      const newSocket = new WebSocket(wsUrl);
      
      newSocket.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setSocket(newSocket);
        reconnectAttempts.current = 0;
        
        // Clear any existing reconnection timeout
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }

        // Don't show toast for now to avoid spam
        // toast.success('Connected to real-time server');
      };

      newSocket.onclose = (event) => {
        console.log('WebSocket disconnected:', event.reason);
        setConnected(false);
        setSocket(null);

        if (event.code === 1008 || event.code === 1011) {
          // Server initiated disconnect, don't reconnect
          console.log('Server disconnected WebSocket');
        } else {
          // Connection lost, attempt to reconnect
          scheduleReconnect();
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

  const handleWebSocketMessage = (data) => {
    console.log('📨 Received WebSocket message:', data);
    
    switch (data.type) {
      case 'aws_stats_update':
        console.log('📊 Updating AWS stats:', data.data);
        setAwsStats(data.data);
        break;
        
      case 'system_status_update':
        console.log('🔧 Updating system status:', data.data);
        setSystemStatus(data.data);
        break;
        
      case 'notification':
        handleNotification(data.data);
        break;
        
      case 'pong':
        console.log('🏓 Received pong');
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
        console.log('🔍 Unknown message type:', data.type, data);
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
    if (socket) {
      socket.close();
      setSocket(null);
      setConnected(false);
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  };

  const scheduleReconnect = () => {
    if (reconnectAttempts.current >= maxReconnectAttempts) {
      toast.error('Failed to connect to chat server. Please refresh the page.');
      return;
    }

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000); // Exponential backoff, max 30s
    reconnectAttempts.current += 1;

    console.log(`Scheduling reconnection attempt ${reconnectAttempts.current} in ${delay}ms`);

    reconnectTimeoutRef.current = setTimeout(() => {
      if (isAuthenticated && token) {
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
    setMessages(prev => [...prev, message]);
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
    console.log('📡 Requesting AWS stats via WebSocket...');
    return sendWebSocketMessage('request_aws_stats');
  };

  const requestSystemStatus = () => {
    console.log('📡 Requesting system status via WebSocket...');
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
