# The builder no longer injects BUILD_FROM from build.yaml, so the default here
# is what actually gets used. base-python is a manifest list covering amd64 and
# arm64, which is why no per-architecture image is named.
ARG BUILD_FROM=ghcr.io/home-assistant/base-python:3.13-alpine3.24

# The application source lives in its own repository and is consumed as a
# published image: there is no copy of it here to keep in sync. Bumping the tag
# on the line below is what releases a new version of this app.
FROM ghcr.io/driin0/ha-mcp-server:1.1.0 AS app

FROM ${BUILD_FROM}

# The dependencies are copied already compiled instead of being reinstalled.
# Both images are Alpine with the same Python minor, so the native extensions
# (pydantic_core, cryptography, rpds, websockets) load as they are — which also
# guarantees both distributions run the very same packages, not the same
# requirements.txt resolved twice. No gcc, no build toolchain, no compilation.
COPY --from=app /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

COPY --from=app /app/server.py /app/web.py /app/stats.py /app/
COPY --from=app /app/tools/ /app/tools/

# If a future base image breaks the ABI, this fails the build instead of the
# first start, where it would look like a runtime crash out of nowhere.
RUN python3 -c "import mcp, httpx, websockets, dotenv, pydantic_core, cryptography"

# jq non è chiamato da run.sh, ma bashio::config lo usa internamente per
# leggere le opzioni dell'app: senza, lo script fallisce alla prima riga utile.
RUN apk add --no-cache jq

COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
