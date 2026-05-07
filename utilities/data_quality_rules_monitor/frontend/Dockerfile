# ── Stage 1: Build ────────────────────────────────────────────
# vite outDir is "../static" relative to frontend/ui →
# running from /app/ui, output lands at /app/static
FROM node:20-alpine AS build

WORKDIR /app/ui

COPY ui/package.json ui/package-lock.json ./
RUN npm ci

COPY ui/ ./
RUN npm run build
# Output: /app/static/assets/index.{js,css} + index.html

# ── Stage 2: Serve with nginx ──────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=build /app/static /usr/share/nginx/html

# SPA config: allow iframe embedding from any origin (required for Atlan)
RUN printf 'server {\n\
    listen 8080;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    gzip on;\n\
    gzip_types text/plain text/css application/javascript application/json;\n\
    location /assets/ {\n\
        add_header Cache-Control "public, max-age=31536000, immutable";\n\
    }\n\
    location / {\n\
        add_header X-Frame-Options "";\n\
        add_header Content-Security-Policy "frame-ancestors *";\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
