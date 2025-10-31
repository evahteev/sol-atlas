# ---------- Base (pins Node & common env) ----------
FROM node:18-alpine AS base
ENV NODE_ENV=production
WORKDIR /app

# ---------- Deps (install deps with toolchain once) ----------
FROM base AS deps
# Toolchain for node-gyp
RUN apk add --no-cache --virtual .gyp-deps python3 make g++ linux-headers
COPY package*.json ./
# Use modern flags; also ensure node-gyp sees python3
RUN npm_config_python=/usr/bin/python3 npm ci --include=dev --no-audit --no-fund

# ---------- Build (produce JS/artefacts) ----------
FROM deps AS build
COPY . .
RUN npm run build

# After build, drop dev deps but keep compiled natives
RUN npm prune --omit=dev

# ---------- Runtime (no builds here) ----------
FROM base AS production
# Small init + non-root user
RUN apk add --no-cache dumb-init \
 && addgroup -g 1001 -S nodejs \
 && adduser -S squid -u 1001
WORKDIR /app

# Copy runtime deps and build outputs from build stage
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/lib ./lib
COPY --from=build /app/abi ./abi
COPY --from=build /app/schema.graphql ./schema.graphql
# (If you need package.json for runtime scripts)
COPY package*.json ./

USER squid
EXPOSE 3000
ENTRYPOINT ["dumb-init", "--"]
CMD ["npm", "run", "start"]
