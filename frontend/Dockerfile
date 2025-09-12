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
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Healthcheck konfigurieren
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-80}/health || exit 1

# Umgebungsvariablen
ENV PORT=8080
ENV BACKEND_URL=http://backend:8000

# Starte nginx mit Umgebungsvariablen
CMD /bin/sh -c "envsubst '\$PORT \$BACKEND_URL' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"
