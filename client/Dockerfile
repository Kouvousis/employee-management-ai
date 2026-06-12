# syntax=docker/dockerfile:1

# --- Build stage: compile the Angular app with pnpm ---
FROM node:22-slim AS build

WORKDIR /app
RUN corepack enable

# Install dependencies first (cached layer).
# pnpm-workspace.yaml carries onlyBuiltDependencies (native build-script allowlist).
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN corepack prepare pnpm@11.4.0 --activate && pnpm install --frozen-lockfile

# Build the production bundle.
COPY . .
RUN pnpm build

# --- Serve stage: static files via nginx ---
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/client/browser /usr/share/nginx/html

EXPOSE 80