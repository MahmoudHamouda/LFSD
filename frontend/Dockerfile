# Build Stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files first for better caching
COPY package.json package-lock.json ./
RUN npm install

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production Stage (Nginx)
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port (Cloud Run defaults to 8080)
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
