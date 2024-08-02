from __future__ import annotations

import dataclasses
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
import pathlib
import re
import sys
import types
import typing
import zipimport

from yt_dlp.networking import Request
from yt_dlp.utils._utils import _YDLLogger

if typing.TYPE_CHECKING:
    from yt_dlp.networking import RequestDirector, Response


@dataclasses.dataclass
class Source:
    name: str
    url: str
    hashes: dict[str, bytes]
    regexes: dict[str, str]


class ExtractorRepo:
    def __init__(
        self,
        source_urls: list[str],
        /,
        request_director: RequestDirector | None = None,
        root_dir: pathlib.Path | None = None,
        logger: _YDLLogger | None = None,
    ):
        self._request_director = request_director
        self._source_urls = source_urls
        self._root_dir = root_dir or self._get_root_dir()
        self._root_dir.mkdir(parents=True, exist_ok=True)
        self._logger = logger

    def load_sources(self, /, *, online=False):
        sources_path = self._root_dir / 'sources.json'
        self.sources: list[Source] = []

        sources = {}
        if online:
            for url in self._source_urls:
                with self._request(url) as response:
                    # TODO: allow data in different formats
                    sources[url] = json.load(response)
                    # TODO: write to disk
            if self._logger:
                self._logger.debug(f'Writing source info from {len(self._source_urls)} urls')
            with sources_path.open('w', encoding='utf8') as file:
                json.dump(sources, file, indent=2)

        elif sources_path.exists():
            if self._logger:
                self._logger.debug(f'Loading cached {len(sources)} urls')
            with sources_path.open('rb') as file:
                sources = json.load(file)

        # TODO: add what core version is required into json
        # TODO: error handling for invalid structure
        for _, source in sources.items():
            self.sources.extend(Source(
                name=name,
                url=value['src'],
                hashes=value.get('hash', {}),
                regexes=value['regex'],
            ) for name, value in source.items())
        if self._logger:
            self._logger.debug(f'Loaded {len(self.sources)} external extractors')

    def get_extractor_for_url(self, url, ie_key=None, online=False):
        for source in self.sources:
            for ie_name, regex in source.regexes.items():
                if ie_key in (None, ie_name[:-2]) and re.match(regex, url):
                    return self._get_extractor(source.name, ie_name, source.url if online else None)

        return None

    def _get_extractor(self, name: str, ie_name: str, /, url: str | None = None):
        # TODO: some sort of invalidation, so that we can update local extractors
        module = self._import_extractor(name)
        if module is None:
            if not url:
                raise FileNotFoundError(f'Could not find {name!r} locally')

            extension = pathlib.PurePosixPath(url).suffix.lstrip('.')
            if extension not in IMPORT_STRATEGIES:
                raise ImportError(f'No known import strategy for .{extension} files')
            output = self._root_dir / f'{name}.{extension}'

            with self._request(url) as response:
                data = response.read()
            # TODO: check hash of downloaded data
            if self._logger:
                self._logger.info(f'Writing extractor code for {name} to {output}')
            with output.open('wb') as file:
                file.write(data)

            module = self._import_extractor(name)
            assert module, 'After download, the module should be importable'

        return getattr(module, ie_name)

    def _import_extractor(self, name: str, /) -> types.ModuleType | None:
        # TEMP: for showcase only, should be `__name__`
        real_name = 'yt_dlp.utils.extractor_repository'
        module_name = importlib.util.resolve_name(f'..extractor.{name}', real_name)

        for extension, importer in IMPORT_STRATEGIES.items():
            path = self._root_dir / f'{name}.{extension}'
            if path.is_file():
                module = importer(module_name, path)
                break
        else:
            return None

        sys.modules[module_name] = module
        return module

    def _get_root_dir(self, /) -> pathlib.Path:
        root_path = pathlib.Path(os.getenv('XDG_DATA_HOME', '~/.local/share'))
        return root_path.expanduser().resolve() / 'yt-dlp'

    def _request(self, url: str, /) -> Response:
        if self._request_director is None:
            raise RuntimeError('No request director given, cannot do network requests')

        return self._request_director.send(Request(url))


def _import_zipfile(name: str, path: pathlib.Path) -> types.ModuleType:
    importer = zipimport.zipimporter(str(path))

    # py >= 3.10 deprecates `zipimporter.load_module`
    if sys.version_info < (3, 10):
        return importer.load_module(name)

    spec = importlib.machinery.ModuleSpec(name, None, origin=str(path), is_package=False)
    spec.has_location = True
    module = importlib.util.module_from_spec(spec)
    importer.exec_module(module)

    return module


def _import_pyfile(name: str, path: pathlib.Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, str(path))
    if not spec:
        raise ImportError('Could not create module spec')
    if not spec.loader:
        raise ImportError('No available loader')
    module = importlib.util.module_from_spec(spec)
    if not module:
        raise ImportError('Could not create module')
    spec.loader.exec_module(module)

    return module


IMPORT_STRATEGIES = {
    'py': _import_pyfile,
    'zip': _import_zipfile,
}

if __name__ == '__main__':
    import yt_dlp

    # Ignore this it's just so we don't eagerly construct `ydl._request_director`
    class Lazy:
        def __init__(self, accessor):
            self.__accessor = accessor

        def __getattribute__(self, name: str, /):
            accessor_name = f'_{type(self).__name__}__accessor'
            obj = object.__getattribute__(self, accessor_name)()
            self.__dict__ = obj.__dict__
            self.__class__ = type(obj)
            return getattr(obj, name)

    class YoutubeDLRepoDemo(yt_dlp.YoutubeDL):
        def __init__(self, params=None, auto_init=True):
            if params is None:
                params = {}
            super().__init__(params, auto_init)

            self._online_repo_lookup = bool(params.get('online_repo_lookup'))
            request_director = Lazy(lambda: self._request_director)
            logger = _YDLLogger(self)

            sources = params.get('extractor_repo_sources', [])
            self._extractor_repo = ExtractorRepo(sources, request_director, logger=logger)
            self._extractor_repo.load_sources(online=self._online_repo_lookup)

        def extract_info(self, url, *args, ie_key=None, **kwargs):
            extractor = self._extractor_repo.get_extractor_for_url(url, ie_key, online=self._online_repo_lookup)
            if extractor:
                # XXX: cringe workaround to add IE to the FRONT
                _ies = self._ies
                self._ies = {}
                self.add_info_extractor(extractor())
                self._ies.update(_ies)
            return super().extract_info(url, *args, ie_key=ie_key, **kwargs)

    parsed_opts = yt_dlp.parse_options()
    ydl_opts = {
        **parsed_opts.ydl_opts,
        # TODO: add these or similar to options.py
        'online_repo_lookup': True,
        'extractor_repo_sources': [
            'https://raw.grub4k.dev/yt-dlp-demo/extractors.json',
        ],
    }

    yt_dlp._IN_CLI = True
    with YoutubeDLRepoDemo(ydl_opts) as ydl:
        ydl.download(parsed_opts.urls)
