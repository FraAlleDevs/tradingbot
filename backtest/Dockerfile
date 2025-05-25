# Use Node.js 16 as specified in package.json engines
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
RUN npm ci && npm cache clean --force

# Copy TypeScript configuration
COPY tsconfig.json ./

# Copy source code
COPY src/ ./src/

# Default command - can be overridden
CMD ["npm", "run", "app:file"]