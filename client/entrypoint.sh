#!/bin/sh

# Изменяем владельца файлов на www-data
chown -R www-data:www-data /app/static

# Запускаем Nginx
nginx -g 'daemon off;'