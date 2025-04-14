# 1. Установка зависимостей (используем standalone output)
FROM node:18-alpine AS dependency-builder
WORKDIR /app
COPY package.json package-lock.json* ./
# Используем npm ci для установки точно по lock-файлу и только production зависимостей
RUN npm ci --only=production

# 2. Сборка приложения (используем standalone output)
FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=dependency-builder /app/node_modules ./node_modules
# Явно копируем package*.json и public перед остальными файлами
COPY package*.json ./
COPY public ./public
COPY . .
# Переменные окружения, необходимые для СБОРКИ (если NEXT_PUBLIC_*)
# Пример: ARG NEXT_PUBLIC_API_BASE_URL
# ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
RUN npm run build

# 3. Финальный образ для standalone-режима
FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Переменные окружения, необходимые во ВРЕМЯ ВЫПОЛНЕНИЯ
# Эти переменные будут установлены при деплое Serverless Container
# ENV NEXTAUTH_URL=...
# ENV NEXTAUTH_SECRET=...
# ENV NEXT_PUBLIC_API_BASE_URL=...
# ENV GOOGLE_CLIENT_ID=...
# ENV GOOGLE_CLIENT_SECRET=...

COPY --from=builder /app/public ./public
# Копируем standalone сборку
COPY --from=builder /app/.next/standalone ./
# Копируем статические ассеты, которые будут обслуживаться Node.js сервером (если Object Storage недоступен)
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
# Указываем пользователя node для безопасности
USER node
# Запускаем сервер из standalone-папки
CMD ["node", "server.js"]