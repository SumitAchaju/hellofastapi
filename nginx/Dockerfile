FROM node:alpine AS builder

# Set the working directory
WORKDIR /app

# Copy the rest of the application code
COPY ui .

# Install dependencies
RUN npm install

# Build the application
RUN npm run build



FROM nginx:alpine

# Copy the nginx configuration file
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf

# Remove default nginx static files
RUN rm -rf /usr/share/nginx/html/*

# ✅ Copy built files from the builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80