# AWS Chatbot Frontend Dockerfile
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Set environment variables
ENV NODE_ENV=development
ENV GENERATE_SOURCEMAP=false
ENV CHOKIDAR_USEPOLLING=true

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy project files
COPY . .

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs \
    && adduser -S reactjs -u 1001 \
    && chown -R reactjs:nodejs /app
USER reactjs

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
