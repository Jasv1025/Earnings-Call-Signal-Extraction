# 1. Install dependencies and build
FROM node:18-alpine AS builder

WORKDIR /app
COPY . .

ENV NODE_ENV=production

RUN npm install
RUN npm run build

# 2. Serve with Next.js production server
FROM node:18-alpine AS runner

WORKDIR /app

# Copy necessary runtime files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/tailwind.config.js ./tailwind.config.js
COPY --from=builder /app/postcss.config.js ./postcss.config.js
#COPY --from=builder /app/public ./public
COPY --from=builder /app/styles ./styles

EXPOSE 3000

CMD ["npm", "start"]
