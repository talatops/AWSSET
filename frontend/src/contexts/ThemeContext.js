import React, { createContext, useContext, useState, useEffect } from 'react';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

const ThemeContext = createContext();

// Define custom themes
const getTheme = (mode, accentColor = 'blue') => {
  const isDark = mode === 'dark';
  
  const accentColors = {
    blue: isDark ? '#4FC3F7' : '#1976D2',
    purple: isDark ? '#BA68C8' : '#7B1FA2',
    green: isDark ? '#81C784' : '#388E3C',
    orange: isDark ? '#FFB74D' : '#F57C00',
    pink: isDark ? '#F48FB1' : '#C2185B',
    teal: isDark ? '#4DB6AC' : '#00695C',
  };

  return createTheme({
    palette: {
      mode,
      primary: {
        main: accentColors[accentColor],
        light: isDark ? '#81C784' : '#4CAF50',
        dark: isDark ? '#2E7D32' : '#1B5E20',
        contrastText: '#ffffff',
      },
      secondary: {
        main: isDark ? '#FF9800' : '#FF5722',
        light: isDark ? '#FFB74D' : '#FF8A65',
        dark: isDark ? '#E65100' : '#D84315',
      },
      background: {
        default: isDark ? '#0a0e1a' : '#f8fafc',
        paper: isDark ? '#1a1f36' : '#ffffff',
        elevation1: isDark ? '#252b42' : '#f9fafb',
        elevation2: isDark ? '#2d3651' : '#f1f5f9',
        elevation3: isDark ? '#364166' : '#e2e8f0',
      },
      text: {
        primary: isDark ? '#e2e8f0' : '#1e293b',
        secondary: isDark ? '#94a3b8' : '#475569',
        disabled: isDark ? '#64748b' : '#94a3b8',
      },
      divider: isDark ? '#334155' : '#e2e8f0',
      error: {
        main: isDark ? '#f87171' : '#dc2626',
        light: isDark ? '#fca5a5' : '#ef4444',
        dark: isDark ? '#dc2626' : '#b91c1c',
      },
      warning: {
        main: isDark ? '#fbbf24' : '#d97706',
        light: isDark ? '#fcd34d' : '#f59e0b',
        dark: isDark ? '#d97706' : '#b45309',
      },
      info: {
        main: isDark ? '#60a5fa' : '#2563eb',
        light: isDark ? '#93c5fd' : '#3b82f6',
        dark: isDark ? '#2563eb' : '#1d4ed8',
      },
      success: {
        main: isDark ? '#34d399' : '#059669',
        light: isDark ? '#6ee7b7' : '#10b981',
        dark: isDark ? '#059669' : '#047857',
      },
      // Custom colors for AWS services
      aws: {
        ec2: '#FF9900',
        s3: '#3F48CC',
        lambda: '#FF9900',
        rds: '#527FFF',
        iam: '#DD344C',
        cloudtrail: '#759C3E',
        bedrock: '#FF4B4B',
      }
    },
    typography: {
      fontFamily: '"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 700,
        lineHeight: 1.2,
        letterSpacing: '-0.025em',
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
        lineHeight: 1.3,
        letterSpacing: '-0.025em',
      },
      h3: {
        fontSize: '1.5rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h4: {
        fontSize: '1.25rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h5: {
        fontSize: '1.125rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      h6: {
        fontSize: '1rem',
        fontWeight: 600,
        lineHeight: 1.4,
      },
      body1: {
        fontSize: '1rem',
        lineHeight: 1.6,
        letterSpacing: '0.00938em',
      },
      body2: {
        fontSize: '0.875rem',
        lineHeight: 1.5,
        letterSpacing: '0.01071em',
      },
      button: {
        textTransform: 'none',
        fontWeight: 500,
        letterSpacing: '0.02857em',
      },
      caption: {
        fontSize: '0.75rem',
        lineHeight: 1.66,
        letterSpacing: '0.03333em',
      },
    },
    shape: {
      borderRadius: 12,
    },
    shadows: isDark 
      ? [
          'none',
          '0px 1px 3px rgba(0, 0, 0, 0.5), 0px 1px 2px rgba(0, 0, 0, 0.24)',
          '0px 1px 5px rgba(0, 0, 0, 0.5), 0px 2px 2px rgba(0, 0, 0, 0.24)',
          '0px 1px 8px rgba(0, 0, 0, 0.5), 0px 3px 4px rgba(0, 0, 0, 0.24)',
          '0px 2px 4px rgba(0, 0, 0, 0.5), 0px 4px 5px rgba(0, 0, 0, 0.24)',
          '0px 3px 5px rgba(0, 0, 0, 0.5), 0px 5px 8px rgba(0, 0, 0, 0.24)',
          '0px 3px 5px rgba(0, 0, 0, 0.5), 0px 6px 10px rgba(0, 0, 0, 0.24)',
          '0px 4px 5px rgba(0, 0, 0, 0.5), 0px 8px 10px rgba(0, 0, 0, 0.24)',
          '0px 5px 5px rgba(0, 0, 0, 0.5), 0px 10px 10px rgba(0, 0, 0, 0.24)',
          '0px 5px 6px rgba(0, 0, 0, 0.5), 0px 12px 12px rgba(0, 0, 0, 0.24)',
          '0px 6px 6px rgba(0, 0, 0, 0.5), 0px 14px 14px rgba(0, 0, 0, 0.24)',
          '0px 6px 7px rgba(0, 0, 0, 0.5), 0px 16px 16px rgba(0, 0, 0, 0.24)',
          '0px 7px 8px rgba(0, 0, 0, 0.5), 0px 18px 18px rgba(0, 0, 0, 0.24)',
          '0px 7px 8px rgba(0, 0, 0, 0.5), 0px 20px 20px rgba(0, 0, 0, 0.24)',
          '0px 7px 9px rgba(0, 0, 0, 0.5), 0px 22px 22px rgba(0, 0, 0, 0.24)',
          '0px 8px 9px rgba(0, 0, 0, 0.5), 0px 24px 24px rgba(0, 0, 0, 0.24)',
          '0px 8px 10px rgba(0, 0, 0, 0.5), 0px 26px 26px rgba(0, 0, 0, 0.24)',
          '0px 8px 11px rgba(0, 0, 0, 0.5), 0px 28px 28px rgba(0, 0, 0, 0.24)',
          '0px 9px 11px rgba(0, 0, 0, 0.5), 0px 30px 30px rgba(0, 0, 0, 0.24)',
          '0px 9px 12px rgba(0, 0, 0, 0.5), 0px 32px 32px rgba(0, 0, 0, 0.24)',
          '0px 10px 13px rgba(0, 0, 0, 0.5), 0px 34px 34px rgba(0, 0, 0, 0.24)',
          '0px 10px 13px rgba(0, 0, 0, 0.5), 0px 36px 36px rgba(0, 0, 0, 0.24)',
          '0px 10px 14px rgba(0, 0, 0, 0.5), 0px 38px 38px rgba(0, 0, 0, 0.24)',
          '0px 11px 14px rgba(0, 0, 0, 0.5), 0px 40px 40px rgba(0, 0, 0, 0.24)',
          '0px 11px 15px rgba(0, 0, 0, 0.5), 0px 42px 42px rgba(0, 0, 0, 0.24)',
        ]
      : [
          'none',
          '0px 1px 3px rgba(0, 0, 0, 0.12), 0px 1px 2px rgba(0, 0, 0, 0.08)',
          '0px 1px 5px rgba(0, 0, 0, 0.12), 0px 2px 2px rgba(0, 0, 0, 0.08)',
          '0px 1px 8px rgba(0, 0, 0, 0.12), 0px 3px 4px rgba(0, 0, 0, 0.08)',
          '0px 2px 4px rgba(0, 0, 0, 0.12), 0px 4px 5px rgba(0, 0, 0, 0.08)',
          '0px 3px 5px rgba(0, 0, 0, 0.12), 0px 5px 8px rgba(0, 0, 0, 0.08)',
          '0px 3px 5px rgba(0, 0, 0, 0.12), 0px 6px 10px rgba(0, 0, 0, 0.08)',
          '0px 4px 5px rgba(0, 0, 0, 0.12), 0px 8px 10px rgba(0, 0, 0, 0.08)',
          '0px 5px 5px rgba(0, 0, 0, 0.12), 0px 10px 10px rgba(0, 0, 0, 0.08)',
          '0px 5px 6px rgba(0, 0, 0, 0.12), 0px 12px 12px rgba(0, 0, 0, 0.08)',
          '0px 6px 6px rgba(0, 0, 0, 0.12), 0px 14px 14px rgba(0, 0, 0, 0.08)',
          '0px 6px 7px rgba(0, 0, 0, 0.12), 0px 16px 16px rgba(0, 0, 0, 0.08)',
          '0px 7px 8px rgba(0, 0, 0, 0.12), 0px 18px 18px rgba(0, 0, 0, 0.08)',
          '0px 7px 8px rgba(0, 0, 0, 0.12), 0px 20px 20px rgba(0, 0, 0, 0.08)',
          '0px 7px 9px rgba(0, 0, 0, 0.12), 0px 22px 22px rgba(0, 0, 0, 0.08)',
          '0px 8px 9px rgba(0, 0, 0, 0.12), 0px 24px 24px rgba(0, 0, 0, 0.08)',
          '0px 8px 10px rgba(0, 0, 0, 0.12), 0px 26px 26px rgba(0, 0, 0, 0.08)',
          '0px 8px 11px rgba(0, 0, 0, 0.12), 0px 28px 28px rgba(0, 0, 0, 0.08)',
          '0px 9px 11px rgba(0, 0, 0, 0.12), 0px 30px 30px rgba(0, 0, 0, 0.08)',
          '0px 9px 12px rgba(0, 0, 0, 0.12), 0px 32px 32px rgba(0, 0, 0, 0.08)',
          '0px 10px 13px rgba(0, 0, 0, 0.12), 0px 34px 34px rgba(0, 0, 0, 0.08)',
          '0px 10px 13px rgba(0, 0, 0, 0.12), 0px 36px 36px rgba(0, 0, 0, 0.08)',
          '0px 10px 14px rgba(0, 0, 0, 0.12), 0px 38px 38px rgba(0, 0, 0, 0.08)',
          '0px 11px 14px rgba(0, 0, 0, 0.12), 0px 40px 40px rgba(0, 0, 0, 0.08)',
          '0px 11px 15px rgba(0, 0, 0, 0.12), 0px 42px 42px rgba(0, 0, 0, 0.08)',
        ],
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarColor: isDark ? '#6b7280 #374151' : '#d1d5db #f3f4f6',
            '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
              width: 8,
              height: 8,
            },
            '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
              borderRadius: 8,
              backgroundColor: isDark ? '#6b7280' : '#d1d5db',
              minHeight: 24,
              border: `2px solid ${isDark ? '#374151' : '#f3f4f6'}`,
            },
            '&::-webkit-scrollbar-thumb:focus, & *::-webkit-scrollbar-thumb:focus': {
              backgroundColor: isDark ? '#9ca3af' : '#9ca3af',
            },
            '&::-webkit-scrollbar-thumb:active, & *::-webkit-scrollbar-thumb:active': {
              backgroundColor: isDark ? '#9ca3af' : '#9ca3af',
            },
            '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover': {
              backgroundColor: isDark ? '#9ca3af' : '#9ca3af',
            },
            '&::-webkit-scrollbar-corner, & *::-webkit-scrollbar-corner': {
              backgroundColor: isDark ? '#374151' : '#f3f4f6',
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            padding: '8px 16px',
            fontWeight: 500,
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              transform: 'translateY(-1px)',
              boxShadow: isDark 
                ? '0 4px 12px rgba(0, 0, 0, 0.4)' 
                : '0 4px 12px rgba(0, 0, 0, 0.15)',
            },
          },
          contained: {
            background: `linear-gradient(135deg, ${accentColors[accentColor]}, ${accentColors[accentColor]}dd)`,
            '&:hover': {
              background: `linear-gradient(135deg, ${accentColors[accentColor]}dd, ${accentColors[accentColor]}bb)`,
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              transform: 'translateY(-4px)',
              boxShadow: isDark 
                ? '0 20px 40px rgba(0, 0, 0, 0.4)' 
                : '0 20px 40px rgba(0, 0, 0, 0.1)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            borderRadius: 12,
          },
          elevation1: {
            backgroundColor: isDark ? '#1a1f36' : '#ffffff',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            backgroundColor: isDark ? '#1a1f36' : '#ffffff',
            color: isDark ? '#e2e8f0' : '#1e293b',
            backdropFilter: 'blur(20px)',
            borderBottom: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`,
            boxShadow: 'none',
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            backgroundColor: isDark ? '#0f172a' : '#ffffff',
            borderRight: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`,
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 8,
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                transform: 'translateY(-1px)',
              },
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 8,
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            height: 6,
          },
        },
      },
    },
  });
};

export const CustomThemeProvider = ({ children }) => {
  const [mode, setMode] = useState(() => {
    const savedMode = localStorage.getItem('themeMode');
    return savedMode || 'light';
  });
  
  const [accentColor, setAccentColor] = useState(() => {
    const savedAccent = localStorage.getItem('accentColor');
    return savedAccent || 'blue';
  });

  const [animations, setAnimations] = useState(() => {
    const savedAnimations = localStorage.getItem('animationsEnabled');
    return savedAnimations !== 'false';
  });

  const [compactMode, setCompactMode] = useState(() => {
    const savedCompact = localStorage.getItem('compactMode');
    return savedCompact === 'true';
  });

  useEffect(() => {
    localStorage.setItem('themeMode', mode);
  }, [mode]);

  useEffect(() => {
    localStorage.setItem('accentColor', accentColor);
  }, [accentColor]);

  useEffect(() => {
    localStorage.setItem('animationsEnabled', animations);
  }, [animations]);

  useEffect(() => {
    localStorage.setItem('compactMode', compactMode);
  }, [compactMode]);

  const toggleMode = () => {
    setMode(prevMode => prevMode === 'light' ? 'dark' : 'light');
  };

  const theme = getTheme(mode, accentColor);

  const value = {
    mode,
    setMode,
    toggleMode,
    accentColor,
    setAccentColor,
    animations,
    setAnimations,
    compactMode,
    setCompactMode,
    theme,
    isDark: mode === 'dark',
  };

  return (
    <ThemeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AnimatePresence mode="wait">
          <motion.div
            key={mode}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </ThemeProvider>
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a CustomThemeProvider');
  }
  return context;
};

export default ThemeContext;
