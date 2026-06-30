# Этап 1: Сборка
FROM node:24-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Этап 2: Запуск
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

# Копируем только необходимые файлы сборки
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000
CMD ["npm", "start"]