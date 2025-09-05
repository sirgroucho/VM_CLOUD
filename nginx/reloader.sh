#!/bin/sh
set -e
mkdir -p /var/cache/nginx /var/run/nginx
nginx -t
exec nginx -g 'daemon off;'
