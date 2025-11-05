FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml README.md ./
COPY auth_proxy ./auth_proxy

RUN pip install --no-cache-dir .

# Create config directory
RUN mkdir /config

# Set default config path
ENV CONFIG_PATH=/config/config.yaml

# Expose default port
EXPOSE 8000

# Run the proxy
CMD ["sh", "-c", "auth-proxy -c ${CONFIG_PATH}"]