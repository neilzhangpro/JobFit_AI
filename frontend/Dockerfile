# =============================================================================
# JobFit AI — Frontend Dockerfile (Multi-Stage)
# =============================================================================

# --- Base stage: install dependencies ---
FROM node:20-alpine AS base
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# --- Development stage ---
FROM base AS dev
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# --- Builder stage ---
FROM base AS builder
COPY . .
RUN npm run build

# --- Production stage ---
FROM node:20-alpine AS prod
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["npm", "start"]
