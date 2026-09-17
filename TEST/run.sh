docker rm -f litellm-proxy

docker run -d \
  --name litellm-proxy \
  -p 4000:4000 \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/litellm_config.yaml:/app/litellm_config.yaml \
  -e CONFIG_FILE_PATH=/app/litellm_config.yaml \
  ghcr.io/berriai/litellm:v1.89.4