# Multi-stage build for React frontend

# Stage 1: Build the React application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the dashboard application
RUN npm run build

# Build the widget
RUN npm run build:widget

# Stage 2: Serve with nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built dashboard files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy built widget file to root for easy embedding
COPY --from=builder /app/dist-widget/widget.iife.js /usr/share/nginx/html/widget.iife.js

# Install wget for health checks
RUN apk add --no-cache wget

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
