/**
 * Environment utility to handle process.env safely in browser
 */

// Comprehensive polyfill for process global in browser environment
if (typeof process === 'undefined') {
  window.process = {
    env: {
      NODE_ENV: 'development',
      REACT_APP_API_URL: 'http://localhost:8000'
    },
    // Add missing process methods that webpack might expect
    nextTick: (callback) => setTimeout(callback, 0),
    browser: true,
    version: '',
    versions: {},
    platform: 'browser',
    arch: 'x64',
    cwd: () => '/',
    chdir: () => {},
    umask: () => 0,
    kill: () => {},
    exit: () => {},
    on: () => {},
    once: () => {},
    emit: () => {},
    addListener: () => {},
    removeListener: () => {},
    removeAllListeners: () => {},
    setMaxListeners: () => {},
    getMaxListeners: () => 0,
    listeners: () => [],
    listenerCount: () => 0,
    prependListener: () => {},
    prependOnceListener: () => {},
    eventNames: () => [],
    // Add Buffer polyfill
    Buffer: typeof Buffer !== 'undefined' ? Buffer : undefined
  };
}

// Polyfill for Buffer if not available
if (typeof Buffer === 'undefined') {
  window.Buffer = {
    isBuffer: () => false,
    alloc: () => new Uint8Array(),
    allocUnsafe: () => new Uint8Array(),
    allocUnsafeSlow: () => new Uint8Array(),
    from: () => new Uint8Array(),
    concat: () => new Uint8Array(),
    byteLength: () => 0,
    compare: () => 0,
    copy: () => 0,
    fill: () => new Uint8Array(),
    includes: () => false,
    indexOf: () => -1,
    lastIndexOf: () => -1,
    readDoubleBE: () => 0,
    readDoubleLE: () => 0,
    readFloatBE: () => 0,
    readFloatLE: () => 0,
    readInt8: () => 0,
    readInt16BE: () => 0,
    readInt16LE: () => 0,
    readInt32BE: () => 0,
    readInt32LE: () => 0,
    readUInt8: () => 0,
    readUInt16BE: () => 0,
    readUInt16LE: () => 0,
    readUInt32BE: () => 0,
    readUInt32LE: () => 0,
    slice: () => new Uint8Array(),
    subarray: () => new Uint8Array(),
    swap16: () => new Uint8Array(),
    swap32: () => new Uint8Array(),
    swap64: () => new Uint8Array(),
    toJSON: () => ({}),
    toString: () => '',
    write: () => 0,
    writeDoubleBE: () => 0,
    writeDoubleLE: () => 0,
    writeFloatBE: () => 0,
    writeFloatLE: () => 0,
    writeInt8: () => 0,
    writeInt16BE: () => 0,
    writeInt16LE: () => 0,
    writeInt32BE: () => 0,
    writeInt32LE: () => 0,
    writeUInt8: () => 0,
    writeUInt16BE: () => 0,
    writeUInt16LE: () => 0,
    writeUInt32BE: () => 0,
    writeUInt32LE: () => 0
  };
}

export const getEnvVar = (key, defaultValue = '') => {
  if (typeof process !== 'undefined' && process.env) {
    return process.env[key] || defaultValue;
  }
  return defaultValue;
};

export const isDevelopment = () => {
  return getEnvVar('NODE_ENV', 'development') === 'development';
};

export const getApiUrl = () => {
  // For development, use direct backend connection
  return 'http://localhost:8000';
};

export const debugLog = (...args) => {
  // Centralized debug logger so we can easily suppress verbose logs
  // in production while keeping useful information in development.
  if (isDevelopment()) {
    // eslint-disable-next-line no-console
    console.debug(...args);
  }
};

// Suppress source map errors in development
if (typeof window !== 'undefined') {
  // Override console.error to filter out source map errors
  const originalError = console.error;
  console.error = (...args) => {
    const message = args.join(' ');
    if (message.includes('Source map error') || 
        message.includes('URL constructor') || 
        message.includes('is not a valid URL')) {
      // Suppress source map errors
      return;
    }
    originalError.apply(console, args);
  };
  
  // Suppress specific webpack warnings
  const originalWarn = console.warn;
  console.warn = (...args) => {
    const message = args.join(' ');
    if (message.includes('Source map error') || 
        message.includes('URL constructor')) {
      // Suppress source map warnings
      return;
    }
    originalWarn.apply(console, args);
  };
  
  // Global error handler to catch process errors
  window.addEventListener('error', (event) => {
    if (event.message.includes('process is not defined') || 
        event.message.includes('Buffer is not defined')) {
      event.preventDefault();
      debugLog('🔧 Suppressed polyfill error:', event.message);
      return false;
    }
  });
  
  // Global unhandled rejection handler
  window.addEventListener('unhandledrejection', (event) => {
    if (event.reason && event.reason.message && 
        (event.reason.message.includes('process is not defined') || 
         event.reason.message.includes('Buffer is not defined'))) {
      event.preventDefault();
      debugLog('🔧 Suppressed polyfill rejection:', event.reason.message);
      return false;
    }
  });
}
