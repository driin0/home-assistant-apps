ARG BUILD_FROM=ghcr.io/home-assistant/base:3.24
FROM zoraxydocker/zoraxy:v3.3.4 AS zoraxy-source
FROM ${BUILD_FROM}

# Copy the Zoraxy binary from the official upstream image
COPY --from=zoraxy-source /usr/local/bin/zoraxy /usr/local/bin/zoraxy
RUN chmod +x /usr/local/bin/zoraxy

# Required by update-ca-certificates at startup
RUN apk add --no-cache ca-certificates

# Copy the s6 service definition
COPY rootfs /

LABEL \
    org.opencontainers.image.title="Home Assistant App: Zoraxy" \
    org.opencontainers.image.description="A general purpose HTTP reverse proxy and forwarding tool" \
    org.opencontainers.image.source="https://github.com/driin0/home-assistant-apps" \
    org.opencontainers.image.url="https://github.com/tobychui/zoraxy" \
    org.opencontainers.image.licenses="AGPL-3.0-or-later"
