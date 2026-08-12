# The builder no longer injects BUILD_FROM from build.yaml, so the default here
# is what actually gets used. base-python is a manifest list covering amd64 and
# arm64, which is why no per-architecture image is named.
ARG BUILD_FROM=ghcr.io/home-assistant/base-python:3.13-alpine3.24
FROM ${BUILD_FROM}

# Build tools needed for native Python extensions on Alpine
RUN apk add --no-cache jq gcc musl-dev python3-dev

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copy server
COPY server.py /app/server.py
COPY web.py /app/web.py
COPY stats.py /app/stats.py
COPY tools/ /app/tools/

# Copy startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
