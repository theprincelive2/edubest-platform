# ============================================================
# Edubest Frontend - Multi-Stage Dockerfile
# ============================================================

# ---- Base ----
FROM node:20-alpine as base
WORKDIR /app
ENV NODE_ENV=development

# ---- Development ----
FROM base as development

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

EXPOSE 3000
CMD ["npm", "run", "dev"]

# ---- Builder ----
FROM base as builder

ENV NODE_ENV=production

COPY package.json package-lock.json* ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# ---- Production ----
FROM node:20-alpine as production

WORKDIR /app
ENV NODE_ENV=production

# Copy built app from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Non-root user
RUN addgroup -S edubest && adduser -S edubest -G edubest
USER edubest

EXPOSE 3000
CMD ["node", "server.js"]
