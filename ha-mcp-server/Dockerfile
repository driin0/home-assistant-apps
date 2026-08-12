ARG BUILD_FROM
FROM $BUILD_FROM

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
