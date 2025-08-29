import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import ChatInterface from '../chat/ChatInterface';
import { motion } from 'framer-motion';

const ChatPage = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
    >
      <Box sx={{ p: 3, flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Paper elevation={3} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', borderRadius: 3, overflow: 'hidden' }}>
          <ChatInterface />
        </Paper>
      </Box>
    </motion.div>
  );
};

export default ChatPage;
