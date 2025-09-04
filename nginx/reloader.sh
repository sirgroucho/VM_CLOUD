#!/bin/bash
set -e
nginx

BLACKLIST_HTTP="/etc/nginx/blacklist.conf"
BLACKLIST_STREAM="/etc/nginx/stream_blacklist.conf"

last_http_mtime=""
last_stream_mtime=""

while true; do
  sleep 2
  cur_http_mtime="$(stat -c %Y "$BLACKLIST_HTTP" 2>/dev/null || echo 0)"
  cur_stream_mtime="$(stat -c %Y "$BLACKLIST_STREAM" 2>/dev/null || echo 0)"
  if [ "$cur_http_mtime" != "$last_http_mtime" ] || [ "$cur_stream_mtime" != "$last_stream_mtime" ]; then
    echo "[reloader] change detected -> nginx reload"
    nginx -t && nginx -s reload
    last_http_mtime="$cur_http_mtime"
    last_stream_mtime="$cur_stream_mtime"
  fi
done
