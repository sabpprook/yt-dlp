#!/usr/bin/env bash

uvx nuitka --onefile \
    --include-module=yt_dlp.compat._legacy \
    --include-module=yt_dlp.compat._deprecated \
    --include-module=yt_dlp.utils._legacy \
    --include-module=yt_dlp.utils._deprecated \
    --include-package=websockets \
    --include-package=requests \
    --include-package=urllib3 \
    --include-package=urllib3 \
    --include-package=mutagen \
    --include-package=brotli \
    --include-package=certifi \
    --include-package=secretstorage \
    --include-package=curl_cffi \
    yt_dlp/__main__.py

