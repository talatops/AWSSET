# AWS Chatbot Frontend Dockerfile
FROM node:16-slim

# Set working directory
WORKDIR /app

# Build arguments for React environment variables
ARG REACT_APP_API_URL=http://localhost:8000
ARG REACT_APP_WEBSOCKET_URL=ws://localhost:8000/ws/realtime

# Set environment variables
ENV NODE_ENV=development
ENV GENERATE_SOURCEMAP=false
ENV CHOKIDAR_USEPOLLING=true
ENV SKIP_PREFLIGHT_CHECK=true
ENV HOME=/app
ENV NPM_CONFIG_CACHE=/tmp/.npm
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_WEBSOCKET_URL=$REACT_APP_WEBSOCKET_URL

# Configure npm for faster installs
ENV NPM_CONFIG_PREFER_OFFLINE=false
ENV NPM_CONFIG_AUDIT=false
ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_PROGRESS=false

# Install dependencies first (better caching)
COPY package*.json ./

# Install dependencies with optimizations
RUN npm config set registry https://registry.npmjs.org/ && \
    npm config set fetch-retries 3 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 120000 && \
    npm install --legacy-peer-deps --prefer-offline --no-audit --no-fund

# Copy project files
COPY . .

# Create non-root user for security with home directory and writable npm cache
RUN groupadd -r nodejs && \
    useradd -r -g nodejs -d /app -s /bin/bash reactjs && \
    chown -R reactjs:nodejs /app && \
    mkdir -p /tmp/.npm && \
    chown -R reactjs:nodejs /tmp/.npm

# Set HOME environment variable
ENV HOME=/app

USER reactjs

# Expose port
EXPOSE 3000

# Start the application (Node 16 doesn't need openssl-legacy-provider)
CMD ["npm", "start"]
