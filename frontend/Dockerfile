FROM node:18-alpine AS builder

WORKDIR /app

# Kopiere Package-Dateien und installiere Dependencies
COPY package*.json ./
RUN npm ci

# Kopiere den Rest des Codes und build
COPY . .
ARG VITE_API_URL=/api
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM nginx:alpine

# Kopiere die gebauten Dateien und die nginx-Konfiguration
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Starte nginx
CMD ["nginx", "-g", "daemon off;"]
