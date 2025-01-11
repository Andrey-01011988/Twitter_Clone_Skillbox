FROM nginx

RUN rm /etc/nginx/nginx.conf /etc/nginx/conf.d/default.conf

COPY /client/static /app/static

COPY /client/nginx.conf /etc/nginx/nginx.conf

# Копируем скрипт запуска
COPY /client/entrypoint.sh /usr/local/bin/entrypoint.sh

# Устанавливаем точку входа
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# http://localhost:8080