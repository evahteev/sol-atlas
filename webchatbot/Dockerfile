# syntax=docker/dockerfile:1.4
# Multi-stage Dockerfile for Dojo Chatbot
# Optimized for production deployment in Kubernetes

# Base stage with pnpm tooling
FROM node:20-alpine AS base
RUN apk add --no-cache libc6-compat
WORKDIR /workspace

# Enable pnpm via Corepack (version pinned by package.json)
ENV PNPM_HOME="/root/.local/share/pnpm"
ENV PATH="${PNPM_HOME}:${PATH}"
RUN corepack enable
RUN pnpm add --global tsx@4.7.0

# Stage 1: Install dependencies with pnpm
FROM base AS deps

# Copy workspace manifests and sources (excluding node_modules for caching)
COPY pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./
COPY --link apps/dojo ./apps/dojo
COPY --link middlewares ./middlewares
COPY --link integrations ./integrations
COPY --link sdks ./sdks

# Install only what the dojo app needs
RUN pnpm install --filter demo-viewer... --frozen-lockfile

# Stage 2: Build the Next.js application
FROM base AS builder

# Reuse installed dependencies from deps stage
COPY --from=deps /workspace/node_modules ./node_modules
COPY --from=deps /workspace/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=deps /workspace/pnpm-workspace.yaml ./pnpm-workspace.yaml
COPY --from=deps /workspace/turbo.json ./turbo.json
COPY --from=deps /workspace/apps/dojo/node_modules ./apps/dojo/node_modules

# Copy source code (node_modules excluded via .dockerignore)
COPY --link apps/dojo ./apps/dojo
COPY --link middlewares ./middlewares
COPY --link integrations ./integrations
COPY --link sdks ./sdks

WORKDIR /workspace/apps/dojo

ENV NEXT_TELEMETRY_DISABLED=1

ARG NEXT_PUBLIC_GIT_COMMIT
ENV NEXT_PUBLIC_GIT_COMMIT=$NEXT_PUBLIC_GIT_COMMIT

ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL

ARG NEXT_PUBLIC_ENABLE_COMMANDS
ENV NEXT_PUBLIC_ENABLE_COMMANDS=$NEXT_PUBLIC_ENABLE_COMMANDS

ARG NEXT_PUBLIC_ENABLE_INLINE_MENU
ENV NEXT_PUBLIC_ENABLE_INLINE_MENU=$NEXT_PUBLIC_ENABLE_INLINE_MENU

ARG NEXT_PUBLIC_ENABLE_REPLY_MENU
ENV NEXT_PUBLIC_ENABLE_REPLY_MENU=$NEXT_PUBLIC_ENABLE_REPLY_MENU

ARG NEXT_PUBLIC_ENABLE_TASKS
ENV NEXT_PUBLIC_ENABLE_TASKS=$NEXT_PUBLIC_ENABLE_TASKS

ARG NEXT_PUBLIC_EMBEDDED_SITE_URL
ENV NEXT_PUBLIC_EMBEDDED_SITE_URL=$NEXT_PUBLIC_EMBEDDED_SITE_URL

# Build dependent workspace packages required at runtime (run from workspace root)
RUN pnpm --dir /workspace install \
      --filter @ag-ui/core... \
      --filter @ag-ui/proto... \
      --filter @ag-ui/encoder... \
      --filter @ag-ui/client... \
      --filter @ag-ui/langgraph... \
      --frozen-lockfile --prod=false && \
    pnpm --dir /workspace --filter @ag-ui/core run build && \
    pnpm --dir /workspace --filter @ag-ui/proto run generate && \
    pnpm --dir /workspace --filter @ag-ui/proto run build -- --tsconfig tsconfig.publish.json && \
    pnpm --dir /workspace --filter @ag-ui/encoder run build && \
    pnpm --dir /workspace --filter @ag-ui/client run build && \
    pnpm --dir /workspace --filter @ag-ui/langgraph run build

# Build Next.js application
RUN pnpm run generate-content-json && pnpm run build

# Verify standalone build was created
RUN ls -la .next/ && ls -la .next/standalone/

# Stage 3: Runtime image
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone build output
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/dojo/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/dojo/.next/static ./apps/dojo/.next/static
COPY --from=builder --chown=nextjs:nodejs /workspace/apps/dojo/public ./apps/dojo/public

# Switch to non-root user
USER nextjs

# Set working directory to the app root produced by Next.js
WORKDIR /app/apps/dojo

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', (r) => {process.exit(r.statusCode && r.statusCode < 500 ? 0 : 1)}).on('error', () => process.exit(1))"

# Start the application
CMD ["node", "server.js"]
