FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY astro.config.mjs tsconfig.json ./
COPY src ./src
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY proxy_params_inet.conf /etc/nginx/proxy_params_inet.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
