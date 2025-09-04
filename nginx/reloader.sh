#!/bin/bash
nginx &
while inotifywait -e modify /etc/nginx/blacklist.conf /etc/nginx/stream_blacklist.conf; do
  nginx -s reload
done
