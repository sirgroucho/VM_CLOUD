# NOTE: minecraft.marx-tec.com here would only handle HTTPS (e.g., a web panel).
# The Minecraft game server uses TCP (default 25565) and cannot be JWT-gated via HTTP nginx.
# If you need SNI/TCP proxying, you'd use the nginx 'stream' module separately.
# For now, we omit a server block since you said MC doesn't need JWT and port 80 is closed.
