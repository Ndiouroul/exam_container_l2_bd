# --- Étape 1 : build ---
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json ./
RUN npm install

COPY . .
# Les URLs des microservices sont injectées au build (voir docker-compose.yml)
ARG VITE_BOOKS_API_URL=http://localhost:8001
ARG VITE_USERS_API_URL=http://localhost:8002
ARG VITE_LOANS_API_URL=http://localhost:8003
ENV VITE_BOOKS_API_URL=$VITE_BOOKS_API_URL
ENV VITE_USERS_API_URL=$VITE_USERS_API_URL
ENV VITE_LOANS_API_URL=$VITE_LOANS_API_URL

RUN npm run build

# --- Étape 2 : service statique via Nginx ---
FROM nginx:1.25-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
