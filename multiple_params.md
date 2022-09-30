# YoutubeDL extractor specific params

## Important Issues/PRs
- [Different proxy per extractor](https://github.com/yt-dlp/yt-dlp/issues/1191)
- [filename template support for --download-archive](https://github.com/yt-dlp/yt-dlp/issues/953)
- [Different cookie files per extractor](https://github.com/yt-dlp/yt-dlp/issues/258)

- [Networking rework 1/2](https://github.com/yt-dlp/yt-dlp/pull/2861)
- [Networking rework 1/2](https://github.com/yt-dlp/yt-dlp/pull/3668)

## YoutubeDL
- `570`: `self.params` either descriptor or additional key like `extractor_args`
- `573`: `self._pps` are needed per additional extractor that specifies pp related args
    - `798`: `add_post_processor` has no info on extractor, potentially also needs proxy ydl
    - `812`: `add_postprocessor_hook` registers with `self._pps`
- `575`: `self._first_webpage_request = True`
- `576+`: hooks, need investigation
    - `self._post_hooks = []`: fine
    - `self._progress_hooks = []`: fine
    - `self._postprocessor_hooks = []`: problematic

- `579+`: state tracking numbers, need investigation
    - `self._download_retcode = 0`
    - `self._num_downloads = 0`
    - `self._num_videos = 0`
    - `self._playlist_level = 0`
    - `self._playlist_urls = set()`

- `584`: `self.cache = Cache(self)` caching should already be handled in a way that should not break

- `642+`: Overwriting behavior:
    - Uses:
        - `overwrites`
        - `nooverwrites`
- `697`: `self.format_selector` extractor specific
- `703`: `self.params['http_headers']` extractor specific
- `714+`: `self.add_post_processor` extractor specific
- `742`: Download archive:
    - Uses:
        - `download_archive`
- `760`: `def add_info_extractor(self, ie)`:
    - Uses:
        - `self`: use proxy ydl object if needed
- `780`: `self.add_default_info_extractors()`
    - Uses:
        - `add_info_extractor(self, ie)`, logic should go there
- `899`: `__exit__(self, *args)`
    - Uses:
        - `cookiefile`
- `1024`: `raise_no_formats(self, info, forced=False, *, msg=None)`
    - Uses:
        - `ignore_no_formats_error` maybe extractor specific?
- `1032`: `parse_outtmpl(self)`
    - Uses:
        - Stateful `_parse_outtmpl(self)`
    - hard since we cant know what exactly it should do... Ignore since deprecated?
- `1037`: `_parse_outtmpl(self)`
    - Uses:
        - `restrictfilenames`
        - `outtmpl`
- `1047`: `def get_output_path(self, dir_type='', filename=None)`
    - Uses:
        - `paths`
- `1099`: `prepare_outtmpl(self, outtmpl, info_dict, sanitize=False)`
    - Uses:
        - `autonumber_start`
        - `autonumber_size`
        - `outtmpl_na_placeholder`
    - Potentially get extractor from `info_dict`, match for url or sth like that
- `1300`: `_prepare_filename(self, info_dict, *, outtmpl=None, tmpl_type=None)`
    - Uses:
        - `outtmpl`
        - `final_ext`
    - reimplement based on `info_dict` extractor
- `1330`: `prepare_filename(self, info_dict, dir_type='', *, outtmpl=None, warn=False)`
    - Uses:
        - `paths`
- `1351`: `def _match_entry(self, info_dict, incomplete=False, silent=False)`
    - Uses:
        - `matchtitle`: Maybe not
        - `rejecttitle`: Maybe not
        - `daterange`
        - `min_views`: Maybe not
        - `max_views`: Maybe not
        - `age_limit`
        - `match_filter`: Maybe not
        - `break_on_existing`
        - `break_on_reject`
- `1423`: `extract_info(self, url, download=True, ie_key=None, extra_info=None, process=True, force_generic_extractor=False)`
    - Uses:
        - `break_on_existing`
        - `allowed_extractors`
- `1472`: `_handle_extraction_exceptions(func)`
    - Uses:
        - `ignoreerrors`
- `1504`: `_wait_for_video(self, ie_result={})`
    - Uses:
        - `wait_for_video`
        - `noprogress`
- `1551`: `__extract_info(self, url, ie, download, extra_info, process)`
    - Uses:
        - `wait_for_video`
        - `self.process_ie_result(ie_result, download, extra_info)`
- `1596`: `process_ie_result(self, ie_result, download=True, extra_info=None)`
    - Uses:
        <!-- result_type in ('url', 'url_transparent') -->
        - `prefer_insecure`
        - `extract_flat`
        - `info_copy, _ = self.pre_process(info_copy)`
        - `self.__forced_printings(info_copy, self.prepare_filename(info_copy), incomplete=True)`
        - `force_write_download_archive`
        - `self.sanitize_info(info_dict)`

        <!-- result_type == 'video' -->
        - `self.process_video_result(ie_result, download=download)`
        - `force_generic_extractor`

        <!-- result_type in ('playlist', 'multi_video') -->
        - `self._playlist_level += 1`
        - `self._playlist_urls.add(webpage_url)`
        - `self.__process_playlist(ie_result, download)`
        - `self._playlist_level -= 1`
        - `self._playlist_urls.clear()`

- `2350`: `_sanitize_thumbnails(self, info_dict)`
    - Uses:
        - `check_formats`

- `2844`: `__forced_printings(self, info_dict, filename, incomplete)`
    - Uses:
        - `forcejson`
        - `forceprint`
        - `print_to_file`
        - `forcetitle`
        - `forceid`
        - `forceurl`
        - `forcethumbnail`
        - `forcedescription`
        - `forcefilename`
        - `forceduration`

## Things noticed while going through code
- `877`: If console sequences are supported, it should use these instead on windows.
        API has been declared [deprecated](https://learn.microsoft.com/en-us/windows/console/setconsoletitle)
- `1105`: `info_dict.setdefault('epoch', int(time.time()))  # keep epoch consistent once set`
    This mutates the `info_dict`, which might be unexpected. Set epoch after copy?
