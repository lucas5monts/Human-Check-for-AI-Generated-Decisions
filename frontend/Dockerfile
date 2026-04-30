# Stage 1: Build the Astro site
FROM node:22-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve with Caddy
FROM caddy:2-alpine
COPY --from=builder /app/dist /usr/share/caddy
EXPOSE 80