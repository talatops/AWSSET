import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  List,
  ListItem,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  Fade,
  Button,
  Card,
  CardContent,
  Grid,
  Tooltip,
  Menu,
  MenuItem,
  Divider,
  Badge,
  LinearProgress,
  Collapse
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as BotIcon,
  Person as PersonIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Code as CommandIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  AttachFile as AttachFileIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  Publish as UploadIcon,
  CloudUpload as CloudUploadIcon,
  InsertDriveFile as FileIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  Description as DocIcon,
  ContentCopy as CopyIcon,
  GetApp as DownloadIcon,
  VolumeUp as VolumeUpIcon,
  Stop as StopIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-toastify';
import ReactMarkdown from 'react-markdown';

import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { getApiUrl } from '../../utils/env';

const ChatInterface = () => {
  const { user, token } = useAuth();
  const { theme } = useTheme();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [conversationId] = useState(`conv_${Date.now()}`);
  const [chatHealth, setChatHealth] = useState(null);
  
  // Advanced features state
  const [isRecording, setIsRecording] = useState(false);
  const [attachmentMenu, setAttachmentMenu] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [speechSynthesis, setSpeechSynthesis] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentlyPlaying, setCurrentlyPlaying] = useState(null);
  
  // Refs for advanced features
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  
  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat suggestions and health check on mount
  useEffect(() => {
    loadChatSuggestions();
    checkChatHealth();
    initializeSpeechSynthesis();
  }, []);

  // Initialize speech synthesis
  const initializeSpeechSynthesis = () => {
    if ('speechSynthesis' in window) {
      setSpeechSynthesis(window.speechSynthesis);
    }
  };

  // Voice recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await processVoiceInput(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      toast.info('🎤 Recording started... Speak now!');
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('Failed to access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      toast.success('🎤 Recording stopped, processing...');
    }
  };

  const processVoiceInput = async (audioBlob) => {
    try {
      // For now, we'll use a placeholder. In production, you'd send this to a speech-to-text service
      setInputMessage("Voice input: [Speech-to-text would process this audio]");
      toast.info('Voice processed! Edit the text and send.');
    } catch (error) {
      console.error('Error processing voice input:', error);
      toast.error('Failed to process voice input');
    }
  };

  // Text-to-speech functions
  const speakText = (text, messageId) => {
    if (speechSynthesis && 'speechSynthesis' in window) {
      // Stop any current speech
      speechSynthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 0.8;
      
      utterance.onstart = () => {
        setIsPlaying(true);
        setCurrentlyPlaying(messageId);
      };
      
      utterance.onend = () => {
        setIsPlaying(false);
        setCurrentlyPlaying(null);
      };
      
      speechSynthesis.speak(utterance);
    }
  };

  const stopSpeaking = () => {
    if (speechSynthesis) {
      speechSynthesis.cancel();
      setIsPlaying(false);
      setCurrentlyPlaying(null);
    }
  };

  // File upload functions
  const handleAttachmentClick = (event) => {
    setAttachmentMenu(event.currentTarget);
  };

  const handleAttachmentClose = () => {
    setAttachmentMenu(null);
  };

  const handleFileSelect = (type) => {
    handleAttachmentClose();
    if (type === 'file') {
      fileInputRef.current?.click();
    }
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setIsUploading(true);
    
    try {
      for (const file of files) {
        // Validate file size (10MB limit)
        if (file.size > 10 * 1024 * 1024) {
          toast.error(`File ${file.name} is too large. Maximum size is 10MB.`);
          continue;
        }

        const fileData = {
          id: `file_${Date.now()}_${Math.random()}`,
          name: file.name,
          size: file.size,
          type: file.type,
          data: await fileToBase64(file)
        };

        setUploadedFiles(prev => [...prev, fileData]);
        toast.success(`📎 ${file.name} uploaded successfully`);
      }
    } catch (error) {
      console.error('Error uploading files:', error);
      toast.error('Failed to upload files');
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  };

  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const getFileIcon = (fileType) => {
    if (fileType.startsWith('image/')) return <ImageIcon />;
    if (fileType.includes('pdf')) return <PdfIcon />;
    if (fileType.includes('doc') || fileType.includes('text')) return <DocIcon />;
    return <FileIcon />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      toast.success('📋 Copied to clipboard!');
    }).catch(() => {
      toast.error('Failed to copy to clipboard');
    });
  };

  const loadChatSuggestions = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/chat/suggestions`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const checkChatHealth = async () => {
    try {
      const response = await fetch(`${getApiUrl()}/api/chat/health`);
      if (response.ok) {
        const health = await response.json();
        setChatHealth(health);
      }
    } catch (error) {
      console.error('Error checking chat health:', error);
    }
  };

  const sendMessage = async () => {
    if ((!inputMessage.trim() && uploadedFiles.length === 0) || isLoading) return;

    const userMessage = {
      id: `msg_${Date.now()}`,
      type: 'user',
      content: inputMessage.trim() || '[File attachments]',
      timestamp: new Date().toISOString(),
      attachments: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined
    };

    // Add user message to chat
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setUploadedFiles([]);
    setIsLoading(true);
    setShowSuggestions(false);

    try {
      const response = await fetch(`${getApiUrl()}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      const botResponse = data.response;

      // Add bot response to chat
      const botMessage = {
        id: data.message_id,
        type: 'bot',
        content: botResponse.message,
        timestamp: data.timestamp,
        responseType: botResponse.type,
        executionResult: botResponse.execution_result,
        suggestions: botResponse.suggestions,
        actionRequired: botResponse.action_required
      };

      setMessages(prev => [...prev, botMessage]);

      // Handle special response types
      if (botResponse.type === 'aws_error' && botResponse.action_required === 'setup_credentials') {
        toast.warning('AWS credentials need to be configured');
      } else if (botResponse.execution_result?.success) {
        toast.success('AWS command executed successfully!');
      } else if (botResponse.execution_result?.success === false) {
        toast.error(`Command failed: ${botResponse.execution_result.error}`);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        id: `error_${Date.now()}`,
        type: 'bot',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        responseType: 'error',
        error: error.message
      };
      
      setMessages(prev => [...prev, errorMessage]);
      toast.error('Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
    setShowSuggestions(false);
    inputRef.current?.focus();
  };

  const clearChat = () => {
    setMessages([]);
    setShowSuggestions(true);
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    const isError = message.responseType === 'error';
    const isSuccess = message.executionResult?.success;
    const hasAttachments = message.attachments && message.attachments.length > 0;
    
    return (
      <motion.div
        key={message.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <ListItem
          sx={{
            flexDirection: 'column',
            alignItems: isUser ? 'flex-end' : 'flex-start',
            py: 1
          }}
        >
          <Box
            sx={{
              display: 'flex',
              flexDirection: isUser ? 'row-reverse' : 'row',
              alignItems: 'flex-start',
              maxWidth: '80%',
              width: 'fit-content'
            }}
          >
            <Avatar
              sx={{
                bgcolor: isUser ? theme.palette.primary.main : theme.palette.secondary.main,
                mx: 1,
                width: 32,
                height: 32
              }}
            >
              {isUser ? <PersonIcon fontSize="small" /> : <BotIcon fontSize="small" />}
            </Avatar>
            
            <Paper
              elevation={2}
              sx={{
                p: 2,
                bgcolor: isUser 
                  ? theme.palette.primary.main 
                  : theme.palette.background.paper,
                color: isUser 
                  ? theme.palette.primary.contrastText 
                  : theme.palette.text.primary,
                borderRadius: 2,
                maxWidth: '100%'
              }}
            >
              <Box>
                {isUser ? (
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </Typography>
                ) : (
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => (
                        <Typography variant="body1" component="p" sx={{ mb: 1 }}>
                          {children}
                        </Typography>
                      ),
                      h1: ({ children }) => (
                        <Typography variant="h5" component="h1" sx={{ fontWeight: 'bold', mb: 1, mt: 1 }}>
                          {children}
                        </Typography>
                      ),
                      h2: ({ children }) => (
                        <Typography variant="h6" component="h2" sx={{ fontWeight: 'bold', mb: 1, mt: 1 }}>
                          {children}
                        </Typography>
                      ),
                      h3: ({ children }) => (
                        <Typography variant="subtitle1" component="h3" sx={{ fontWeight: 'bold', mb: 0.5, mt: 1 }}>
                          {children}
                        </Typography>
                      ),
                      strong: ({ children }) => (
                        <Typography component="span" sx={{ fontWeight: 'bold' }}>
                          {children}
                        </Typography>
                      ),
                      em: ({ children }) => (
                        <Typography component="span" sx={{ fontStyle: 'italic' }}>
                          {children}
                        </Typography>
                      ),
                      ul: ({ children }) => (
                        <Box component="ul" sx={{ pl: 2, mb: 1 }}>
                          {children}
                        </Box>
                      ),
                      ol: ({ children }) => (
                        <Box component="ol" sx={{ pl: 2, mb: 1 }}>
                          {children}
                        </Box>
                      ),
                      li: ({ children }) => (
                        <Typography component="li" variant="body1" sx={{ mb: 0.3 }}>
                          {children}
                        </Typography>
                      ),
                      code: ({ inline, children }) => 
                        inline ? (
                          <Typography 
                            component="code" 
                            sx={{ 
                              backgroundColor: theme.palette.action.hover,
                              padding: '2px 4px',
                              borderRadius: 1,
                              fontFamily: 'monospace',
                              fontSize: '0.9em'
                            }}
                          >
                            {children}
                          </Typography>
                        ) : (
                          <Paper 
                            sx={{ 
                              backgroundColor: theme.palette.action.hover,
                              p: 1,
                              mb: 1,
                              fontFamily: 'monospace',
                              fontSize: '0.85em',
                              overflow: 'auto'
                            }}
                          >
                            <pre style={{ margin: 0 }}>{children}</pre>
                          </Paper>
                        )
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                )}
                
                {/* File attachments */}
                {hasAttachments && (
                  <Box sx={{ mt: 1 }}>
                    {message.attachments.map((file, index) => (
                      <Chip
                        key={index}
                        icon={getFileIcon(file.type)}
                        label={`${file.name} (${formatFileSize(file.size)})`}
                        size="small"
                        variant="outlined"
                        sx={{ mr: 0.5, mb: 0.5 }}
                      />
                    ))}
                  </Box>
                )}
                
                {/* Message actions */}
                {!isUser && (
                  <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
                    <Tooltip title="Copy message">
                      <IconButton 
                        size="small" 
                        onClick={() => copyToClipboard(message.content)}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    
                    <Tooltip title={isPlaying && currentlyPlaying === message.id ? "Stop speaking" : "Read aloud"}>
                      <IconButton 
                        size="small" 
                        onClick={() => {
                          if (isPlaying && currentlyPlaying === message.id) {
                            stopSpeaking();
                          } else {
                            speakText(message.content, message.id);
                          }
                        }}
                      >
                        {isPlaying && currentlyPlaying === message.id ? 
                          <StopIcon fontSize="small" /> : 
                          <VolumeUpIcon fontSize="small" />
                        }
                      </IconButton>
                    </Tooltip>
                  </Box>
                )}
              </Box>
              
              {/* Show execution results only if not already formatted in the main message */}
              {message.executionResult && message.responseType !== 'aws_command_success' && (
                <Box sx={{ mt: 1 }}>
                  {message.executionResult.success ? (
                    <Alert 
                      severity="success" 
                      icon={<SuccessIcon />}
                      sx={{ mt: 1 }}
                    >
                      <Typography variant="body2">
                        {message.executionResult.message}
                      </Typography>
                      {message.executionResult.data && !message.formatted && (
                        <Typography variant="caption" sx={{ display: 'block', mt: 0.5 }}>
                          {JSON.stringify(message.executionResult.data, null, 2).substring(0, 200)}...
                        </Typography>
                      )}
                    </Alert>
                  ) : (
                    <Alert 
                      severity="error" 
                      icon={<ErrorIcon />}
                      sx={{ mt: 1 }}
                    >
                      <Typography variant="body2">
                        {message.executionResult.error}
                      </Typography>
                    </Alert>
                  )}
                </Box>
              )}
              
              {/* Show suggestions */}
              {message.suggestions && (
                <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {message.suggestions.map((suggestion, index) => (
                    <Chip
                      key={index}
                      label={suggestion}
                      size="small"
                      clickable
                      onClick={() => handleSuggestionClick(suggestion)}
                      sx={{ fontSize: '0.75rem' }}
                    />
                  ))}
                </Box>
              )}
              
              <Typography 
                variant="caption" 
                sx={{ 
                  display: 'block', 
                  mt: 1, 
                  opacity: 0.7,
                  textAlign: isUser ? 'right' : 'left'
                }}
              >
                {new Date(message.timestamp).toLocaleTimeString()}
              </Typography>
            </Paper>
          </Box>
        </ListItem>
      </motion.div>
    );
  };

  const renderWelcomeScreen = () => {
    if (messages.length > 0) return null;

    return (
      <Fade in={showSuggestions}>
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          height: '100%',
          p: 2,
          textAlign: 'center',
          overflowY: 'auto'
        }}>
          {/* Welcome Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Box sx={{ mb: 3 }}>
              <Typography variant="h3" component="h1" fontWeight="bold" gutterBottom sx={{ color: 'primary.main' }}>
                CloudGenie ✨
              </Typography>
              <Typography variant="h6" color="textSecondary" sx={{ mb: 2 }}>
                Your magical AWS companion for seamless cloud operations
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                <Chip label="🤖 AI-Powered" color="primary" size="small" />
                <Chip label="☁️ AWS Native" color="secondary" size="small" />
                <Chip label="⚡ Real-time" color="success" size="small" />
                <Chip label="🔒 Secure" color="warning" size="small" />
              </Box>
            </Box>
          </motion.div>

          {/* Quick Start Suggestions */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            style={{ width: '100%', maxWidth: '900px' }}
          >
            <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
              💡 Try asking me:
            </Typography>
            <Grid container spacing={1.5}>
              {[
                { category: "EC2", suggestions: ["List my instances", "Launch new instance"] },
                { category: "Services", suggestions: ["Show S3 buckets", "Check Lambda functions"] },
                { category: "Monitoring", suggestions: ["Show AWS costs", "Check instance health"] },
                { category: "Quick Actions", suggestions: ["Create security group", "Generate SSH key"] }
              ].map((category, categoryIndex) => (
                <Grid item xs={12} sm={6} md={3} key={categoryIndex}>
                  <Card variant="outlined" sx={{ height: '100%', minHeight: '120px' }}>
                    <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="subtitle2" gutterBottom color="primary" fontWeight="bold">
                        {category.category}
                      </Typography>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        {category.suggestions.map((suggestion, index) => (
                          <Button
                            key={index}
                            variant="outlined"
                            size="small"
                            onClick={() => handleSuggestionClick(suggestion)}
                            sx={{ 
                              justifyContent: 'flex-start',
                              textAlign: 'left',
                              textTransform: 'none',
                              borderRadius: 2,
                              fontSize: '0.75rem',
                              minHeight: '28px',
                              p: 0.5
                            }}
                          >
                            {suggestion}
                          </Button>
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </motion.div>

          {/* Quick Tips */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            style={{ width: '100%', maxWidth: '700px', marginTop: '1rem' }}
          >
            <Paper elevation={1} sx={{ p: 2, borderRadius: 3, bgcolor: 'action.hover' }}>
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                💡 Quick Tips
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {[
                  "Be specific with requests",
                  "Use natural language",
                  "Real-time AWS operations",
                  "Ask for best practices"
                ].map((tip, index) => (
                  <Chip 
                    key={index}
                    label={tip} 
                    size="small" 
                    variant="outlined"
                    sx={{ fontSize: '0.75rem' }}
                  />
                ))}
              </Box>
            </Paper>
          </motion.div>
        </Box>
      </Fade>
    );
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Paper 
        elevation={2} 
        sx={{ 
          p: 2, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderRadius: '12px 12px 0 0'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Avatar sx={{ bgcolor: theme.palette.secondary.main, mr: 2 }}>
            <BotIcon />
          </Avatar>
          <Box>
            <Typography variant="h6">CloudGenie ✨</Typography>
            <Typography variant="caption" color="textSecondary">
              {chatHealth?.ai_service_configured ? 
                '🟢 AI Service Active' : 
                '🔴 AI Service Not Configured'
              }
            </Typography>
          </Box>
        </Box>
        
        <Box>
          <IconButton onClick={checkChatHealth} size="small">
            <RefreshIcon />
          </IconButton>
          <IconButton onClick={clearChat} size="small">
            <SettingsIcon />
          </IconButton>
        </Box>
      </Paper>

      {/* Messages Area */}
      <Box sx={{ 
        flexGrow: 1, 
        overflow: 'auto', 
        bgcolor: theme.palette.background.default,
        position: 'relative'
      }}>
        {messages.length === 0 ? (
          renderWelcomeScreen()
        ) : (
          <List sx={{ p: 0 }}>
            <AnimatePresence>
              {messages.map(renderMessage)}
            </AnimatePresence>
          </List>
        )}
        
        {/* Loading indicator */}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ ml: 1 }}>
              CloudGenie is thinking...
            </Typography>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 2, 
          borderRadius: '0 0 12px 12px',
          bgcolor: theme.palette.background.paper
        }}
      >
        {!chatHealth?.ai_service_configured && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            AI service is not configured. Please add your Gemini API key to enable chat functionality.
          </Alert>
        )}
        
        {/* File upload area */}
        {uploadedFiles.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="textSecondary" sx={{ mb: 1, display: 'block' }}>
              📎 Attached Files ({uploadedFiles.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {uploadedFiles.map((file) => (
                <Chip
                  key={file.id}
                  icon={getFileIcon(file.type)}
                  label={`${file.name} (${formatFileSize(file.size)})`}
                  onDelete={() => removeFile(file.id)}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}

        <Box sx={{ display: 'flex', alignItems: 'flex-end', gap: 1 }}>
          {/* Attachment button */}
          <Tooltip title="Attach files">
            <IconButton 
              onClick={handleAttachmentClick}
              disabled={isLoading}
              sx={{ 
                bgcolor: theme.palette.action.hover,
                '&:hover': {
                  bgcolor: theme.palette.action.selected
                }
              }}
            >
              <AttachFileIcon />
            </IconButton>
          </Tooltip>

          {/* Voice input button */}
          <Tooltip title={isRecording ? "Stop recording" : "Voice input"}>
            <IconButton 
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading}
              sx={{ 
                bgcolor: isRecording ? theme.palette.error.main : theme.palette.action.hover,
                color: isRecording ? theme.palette.error.contrastText : 'inherit',
                '&:hover': {
                  bgcolor: isRecording ? theme.palette.error.dark : theme.palette.action.selected
                }
              }}
            >
              {isRecording ? <MicOffIcon /> : <MicIcon />}
            </IconButton>
          </Tooltip>
          
          <TextField
            ref={inputRef}
            fullWidth
            multiline
            maxRows={4}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isRecording ? "🎤 Recording... Speak now!" : "Ask me anything about AWS... 💬"}
            variant="outlined"
            disabled={isLoading || !chatHealth?.ai_service_configured || isRecording}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3
              }
            }}
          />
          
          <IconButton 
            onClick={sendMessage}
            disabled={(!inputMessage.trim() && uploadedFiles.length === 0) || isLoading || !chatHealth?.ai_service_configured}
            sx={{ 
              bgcolor: theme.palette.primary.main,
              color: theme.palette.primary.contrastText,
              '&:hover': {
                bgcolor: theme.palette.primary.dark
              },
              '&:disabled': {
                bgcolor: theme.palette.action.disabled
              }
            }}
          >
            {isLoading ? <CircularProgress size={20} /> : <SendIcon />}
          </IconButton>
        </Box>

        {/* File input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="*/*"
          style={{ display: 'none' }}
          onChange={handleFileUpload}
        />

        {/* Attachment menu */}
        <Menu
          anchorEl={attachmentMenu}
          open={Boolean(attachmentMenu)}
          onClose={handleAttachmentClose}
          PaperProps={{
            elevation: 8,
            sx: {
              mt: 1.5,
              minWidth: 200,
              '& .MuiMenuItem-root': {
                px: 2,
                py: 1
              }
            }
          }}
        >
          <MenuItem onClick={() => handleFileSelect('file')}>
            <FileIcon sx={{ mr: 2 }} />
            Upload Files
          </MenuItem>
          <MenuItem onClick={() => handleFileSelect('cloud')}>
            <CloudUploadIcon sx={{ mr: 2 }} />
            Cloud Storage
            <Chip label="Soon" size="small" sx={{ ml: 1 }} />
          </MenuItem>
        </Menu>

        {isUploading && (
          <Box sx={{ mt: 1 }}>
            <LinearProgress />
            <Typography variant="caption" color="textSecondary">
              Uploading files...
            </Typography>
          </Box>
        )}
        
        <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
          Press Enter to send, Shift+Enter for new line
        </Typography>
      </Paper>
    </Box>
  );
};

export default ChatInterface;