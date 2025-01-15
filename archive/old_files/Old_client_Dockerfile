FROM nginx

RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY /client/static /app/static

COPY /client/templates /app/templates

COPY /client/nginx.conf /etc/nginx/nginx.conf

# http://localhost:8080