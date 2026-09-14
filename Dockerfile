# container-autopsy — the whole tool in one tiny image.
# The docker CLI is included so the container can autopsy siblings
# through the mounted docker socket.
FROM python:3.12-alpine

RUN apk add --no-cache docker-cli

COPY container_autopsy.py /usr/local/bin/container-autopsy
RUN chmod +x /usr/local/bin/container-autopsy

ENTRYPOINT ["container-autopsy"]
CMD ["--help"]
