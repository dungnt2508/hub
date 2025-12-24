# =========================
# Builder
# =========================
FROM node:20-alpine AS builder

RUN apk add --no-cache python3 make g++ libc6-compat

WORKDIR /app

# ---- Copy package manifests first (cache-friendly) ----
COPY package.json package-lock.json ./
COPY packages/shared-types/package.json packages/shared-types/
COPY backend/package.json backend/

# ---- Install all deps (workspace-style) ----
RUN npm install --prefer-offline --no-audit

# ---- Copy source ----
COPY packages/shared-types packages/shared-types
COPY backend backend

# ---- Build shared-types ----
WORKDIR /app/packages/shared-types
RUN npm run build

RUN test -f dist/index.js && test -f dist/index.d.ts

# ---- Build backend ----
WORKDIR /app/backend
RUN npm run build

# =========================
# Production
# =========================
FROM node:20-alpine

WORKDIR /app
ENV NODE_ENV=production

# ---- Copy only necessary runtime files ----
COPY package.json package-lock.json ./
COPY backend/package.json backend/

# Install prod deps only
RUN npm ci --omit=dev --prefer-offline --no-audit && \
    npm cache clean --force

# ---- Copy built packages ----
COPY --from=builder /app/packages/shared-types/dist packages/shared-types/dist
COPY --from=builder /app/packages/shared-types/package.json packages/shared-types/package.json

# ---- Link internal package properly ----
RUN mkdir -p node_modules/@gsnake && \
    ln -s /app/packages/shared-types node_modules/@gsnake/shared-types

# ---- Copy backend build ----
COPY --from=builder /app/backend/dist backend/dist

# ---- Runtime files ----
COPY backend/migrations backend/migrations
COPY backend/scripts backend/scripts
COPY backend/migrate-config.js backend/
COPY backend/docker-entrypoint.sh ./

RUN chmod +x ./docker-entrypoint.sh

USER node

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3001/health', r => process.exit(r.statusCode === 200 ? 0 : 1))"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["node", "backend/dist/index.js"]
