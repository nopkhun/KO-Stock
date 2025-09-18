# Multi-stage build for React frontend
FROM node:18-alpine AS base

# Install pnpm globally for better caching
RUN npm install -g pnpm@10.4.1

# Set working directory
WORKDIR /app

# Copy package files for dependency caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies with frozen lockfile for reproducible builds
RUN pnpm install --frozen-lockfile --production=false

# Build stage
FROM base AS builder

# Copy source code
COPY . .

# Build the application with optimizations
RUN pnpm run build

# Production stage with Nginx
FROM nginx:1.25-alpine AS production

# Create non-root user for security
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-user -g nginx-user nginx-user

# Install curl for health checks, security updates, and remove cache
RUN apk update && \
    apk upgrade && \
    apk add --no-cache curl ca-certificates && \
    rm -rf /var/cache/apk/* /tmp/*

# Copy built files from builder stage with proper ownership
COPY --from=builder --chown=nginx-user:nginx-user /app/dist /usr/share/nginx/html

# Copy custom nginx configurations
COPY --chown=nginx-user:nginx-user nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=nginx-user:nginx-user nginx-main.conf /etc/nginx/nginx.conf

# Create nginx directories with proper permissions and secure file permissions
RUN mkdir -p /var/cache/nginx/client_temp /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp /var/log/nginx /var/run && \
    chown -R nginx-user:nginx-user /var/cache/nginx /var/log/nginx \
    /var/run /usr/share/nginx/html /etc/nginx/conf.d && \
    chmod -R 755 /usr/share/nginx/html && \
    chmod 644 /etc/nginx/conf.d/default.conf && \
    chmod 644 /etc/nginx/nginx.conf

# Switch to non-root user
USER nginx-user

# Expose port 80
EXPOSE 80

# Enhanced health check with better error handling
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost/health || curl -f http://localhost/ || exit 1

# Start nginx with proper signal handling
CMD ["nginx", "-g", "daemon off;"]
