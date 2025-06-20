FROM alpine:3.21 AS base

RUN apk --update add --no-cache \
        build-base \
        uv \
        scons \
        patchelf \
        binutils \
    ;
RUN uv tool install uv --force
RUN uv tool install nuitka

ENV PATH="/root/.local/bin:$PATH"
WORKDIR /yt-dlp
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/bin/ash", "/entrypoint.sh"]

