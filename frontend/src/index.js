import './utils/env'; // Import env polyfill first
import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import App from './App';
import { AuthProvider } from './contexts/AuthContext';
import { WebSocketProvider } from './contexts/WebSocketContext';
import { CustomThemeProvider } from './contexts/ThemeContext';
import './index.css';

ReactDOM.render(
  // Temporarily disable StrictMode to prevent duplicate OAuth calls in development
  // <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true
      }}
    >
      <CustomThemeProvider>
        <AuthProvider>
          <WebSocketProvider>
            <App />
            <ToastContainer
              position="top-right"
              autoClose={5000}
              hideProgressBar={false}
              newestOnTop={false}
              closeOnClick
              rtl={false}
              pauseOnFocusLoss
              draggable
              pauseOnHover
              theme="colored"
            />
          </WebSocketProvider>
        </AuthProvider>
      </CustomThemeProvider>
    </BrowserRouter>,
  // </React.StrictMode>,
  document.getElementById('root')
);
