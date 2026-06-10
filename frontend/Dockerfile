FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Dev image: keeps node_modules for `docker compose` hot-reload workflow.
FROM node:20-alpine AS dev
WORKDIR /app
COPY package*.json ./
RUN npm ci
ENV NODE_ENV=development
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
