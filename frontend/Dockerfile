FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

# Install with legacy peer deps to avoid resolution conflicts.
# Then explicitly install the Linux musl rollup binary that Vite needs
# when building inside an Alpine (musl libc) container.
RUN npm install --legacy-peer-deps && \
    npm install @rollup/rollup-linux-x64-musl --force --legacy-peer-deps || true

COPY . .

ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build


# Stage 2: serve with nginx
FROM nginx:1.25-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html

RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]