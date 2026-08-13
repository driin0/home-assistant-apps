# The builder no longer injects BUILD_FROM from build.yaml, so the default here
# is what actually gets used. base:3.24 is a manifest list covering amd64 and
# arm64, which is why no per-architecture image is named. It ships Node 24.18,
# the same major as the standalone Docker image, so both distributions run on
# the same runtime.
ARG BUILD_FROM=ghcr.io/home-assistant/base:3.24

# The application source lives in its own repository and is consumed as a
# published image: there is no copy of it here to keep in sync. Bumping the tag
# on the line below is what releases a new version of this app.
FROM ghcr.io/driin0/iliad-tools:1.0.0 AS app

FROM ${BUILD_FROM}

RUN apk add --no-cache nodejs

COPY --from=app /app /app

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
