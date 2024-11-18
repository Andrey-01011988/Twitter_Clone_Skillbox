FROM nginx

RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY /project/client/static /app/static

COPY /project/client/nginx.conf /etc/nginx/nginx.conf