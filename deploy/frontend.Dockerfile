FROM node:20-bookworm-slim AS build

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

ARG VITE_APP_HOST=154.44.25.243
ARG VITE_API_URL=http://154.44.25.243:8080
ARG VITE_ADMIN_API_URL=http://154.44.25.243:5002
ARG VITE_QA_API_BASE=http://154.44.25.243:8081
ARG VITE_GEM_API_BASE=http://154.44.25.243:8080
ARG VITE_DEEP_LEARNING_URL=http://154.44.25.243:18080/

ENV VITE_APP_HOST=$VITE_APP_HOST \
    VITE_API_URL=$VITE_API_URL \
    VITE_ADMIN_API_URL=$VITE_ADMIN_API_URL \
    VITE_QA_API_BASE=$VITE_QA_API_BASE \
    VITE_GEM_API_BASE=$VITE_GEM_API_BASE \
    VITE_DEEP_LEARNING_URL=$VITE_DEEP_LEARNING_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
