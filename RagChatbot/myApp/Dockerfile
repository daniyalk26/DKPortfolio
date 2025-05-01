# Stage 1: Build the Ionic app
FROM node:20 AS build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json to the working directory
COPY package*.json ./

# Install global dependencies
RUN npm install -g @ionic/cli

# Install project dependencies with legacy peer deps
RUN npm install --legacy-peer-deps

# Clear npm cache
RUN npm cache clean --force

# Copy the rest of the application code
COPY . .

# Build the Ionic app
RUN ionic build --prod

# Stage 2: Serve the Ionic app using nginx
FROM nginx:alpine

# Copy the build files from the previous stage
COPY --from=build /app/www /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
