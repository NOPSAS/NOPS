# =============================================================================
# ByggSjekk – Web Dockerfile (multi-stage)
# Stage 1 (deps):    installer npm-avhengigheter
# Stage 2 (builder): bygg Next.js-applikasjonen
# Stage 3 (runner):  minimalt produksjonsbilde
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: deps – installer avhengigheter
# Gjenbrukes av docker-compose.dev.yml som base for utvikling
# -----------------------------------------------------------------------------
FROM node:20-alpine AS deps

WORKDIR /app

# Kopier pakkemanifester
COPY package.json package-lock.json* ./

# Installer avhengigheter
RUN npm install --legacy-peer-deps

# -----------------------------------------------------------------------------
# Stage 2: builder – bygg Next.js standalone-output
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Sett produksjonsmiljø for build
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# -----------------------------------------------------------------------------
# Stage 3: runner – minimalt produksjonsbilde
# Bruker Next.js standalone output for lavest mulig bildestørrelse
# -----------------------------------------------------------------------------
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Ikke kjør som root
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Kopier nødvendige filer fra builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Sett riktige filrettigheter
RUN chown -R nextjs:nodejs /app
USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
