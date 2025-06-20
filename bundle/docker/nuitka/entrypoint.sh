#!/bin/ash
set -e

uv venv --managed-python --python 3.9
uv pip install -r pyproject.toml \
    --extra default \
    --extra curl-cffi \
    --extra secretstorage \
;
uv pip install nuitka
source .venv/bin/activate
# python -m devscripts.make_lazy_extractors
# python devscripts/update-version.py -c "${channel}" -r "${origin}" "${version}"
# python -m bundle.pyinstaller
nuitka --onefile \
    --include-module=yt_dlp.compat._legacy \
    --include-module=yt_dlp.compat._deprecated \
    --include-module=yt_dlp.utils._legacy \
    --include-module=yt_dlp.utils._deprecated \
    --include-module=requests \
    --include-module=urllib3 \
    --include-module=curl_cffi \
    --include-module=websockets \
    --include-module=mutagen \
    --include-module=brotli \
    --include-module=certifi \
    --include-module=secretstorage \
    yt_dlp/__main__.py
deactivate

