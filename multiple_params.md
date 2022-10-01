# YoutubeDL extractor specific params

## Important Issues/PRs
- [Different proxy per extractor](https://github.com/yt-dlp/yt-dlp/issues/1191)
- [filename template support for --download-archive](https://github.com/yt-dlp/yt-dlp/issues/953)
- [Different cookie files per extractor](https://github.com/yt-dlp/yt-dlp/issues/258)

- [Networking rework 1/2](https://github.com/yt-dlp/yt-dlp/pull/2861)
- [Networking rework 1/2](https://github.com/yt-dlp/yt-dlp/pull/3668)

- `class YoutubeDL`
    - `563`: `__init__(self, params=None, auto_init=True)`
        - `self.params`: either descriptor or additional key like `extractor_args`
        - `self._pps` are needed per additional extractor that specifies pp related args

        - `self._first_webpage_request = True`
        - `self._post_hooks = []`: fine
        - `self._progress_hooks = []`: fine
        - `self._postprocessor_hooks = []`: problematic

        - `self._download_retcode = 0`
        - `self._num_downloads = 0`
        - `self._num_videos = 0`
        - `self._playlist_level = 0`
        - `self._playlist_urls = set()`

        - `self.cache = Cache(self)` caching should already be handled in a way that should not break

        <!-- 642+: Overwriting behavior -->
        - `overwrites`
        - `nooverwrites`

        - `self.format_selector`
        - `http_headers`
        <!-- 742: Download archive -->
        - `download_archive`
    - `760`: `def add_info_extractor(self, ie)`
            - `self`: use proxy ydl object if needed
    - `780`: `self.add_default_info_extractors()`
            - `add_info_extractor(self, ie)`, logic should go there
    - `899`: `__exit__(self, *args)`
            - `cookiefile`
    - `1024`: `raise_no_formats(self, info, forced=False, *, msg=None)`
            - `ignore_no_formats_error` maybe extractor specific?
    - `1032`: `parse_outtmpl(self)`
        - hard since we cant know what exactly it should do... Ignore since deprecated?
    - `1037`: `_parse_outtmpl(self)`
            - `restrictfilenames`
            - `outtmpl`
    - `1047`: `def get_output_path(self, dir_type='', filename=None)`
            - `paths`
    - `1099`: `prepare_outtmpl(self, outtmpl, info_dict, sanitize=False)`
            - `autonumber_start`
            - `autonumber_size`
            - `outtmpl_na_placeholder`
        - Potentially get extractor from `info_dict`, match for url or sth like that
    - `1300`: `_prepare_filename(self, info_dict, *, outtmpl=None, tmpl_type=None)`
            - `outtmpl`
            - `final_ext`
        - reimplement based on `info_dict` extractor
    - `1330`: `prepare_filename(self, info_dict, dir_type='', *, outtmpl=None, warn=False)`
            - `paths`
    - `1351`: `def _match_entry(self, info_dict, incomplete=False, silent=False)`
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
            - `break_on_existing`
            - `allowed_extractors`
    - `1472`: `_handle_extraction_exceptions(func)`
            - `ignoreerrors`
    - `1504`: `_wait_for_video(self, ie_result={})`
            - `wait_for_video`
            - `noprogress`
    - `1551`: `__extract_info(self, url, ie, download, extra_info, process)`
            - `wait_for_video`
            - `self.process_ie_result(ie_result, download, extra_info)`
    - `1596`: `process_ie_result(self, ie_result, download=True, extra_info=None)`
        <!-- 1608: result_type in ('url', 'url_transparent') -->
        - `prefer_insecure`
        - `extract_flat`
        - `info_copy, _ = self.pre_process(info_copy)`
        - `self.__forced_printings(info_copy, self.prepare_filename(info_copy), incomplete=True)`
        - `force_write_download_archive`
        - `self.sanitize_info(info_dict)`

        <!-- 1630: result_type == 'video' -->
        - `self.process_video_result(ie_result, download=download)`
        - `force_generic_extractor`

        <!-- 1687: result_type in ('playlist', 'multi_video') -->
        - `self._playlist_level += 1`
        - `self._playlist_urls.add(webpage_url)`
        - `self.__process_playlist(ie_result, download)`
        - `self._playlist_level -= 1`
        - `self._playlist_urls.clear()`

    - `1759`: `__process_playlist(self, ie_result, download)`
        - `PlaylistEntries(self, ie_result)`
        - `lazy_playlist`
        - `allow_playlist_files`
        - `list_thumbnails`
        - `simulate`
        - `self._write_info_json()`
        - `playlistreverse`
        - `playlistrandom`
        - `extract_flat`
        - `skip_playlist_after_errors`
        - `compat_opts`
        - `self.__process_iterable_entry()`
        - `self.run_all_pps('playlist', ...)`

    - `1874`: `__process_iterable_entry(self, entry, download, extra_info)`

    - `1946`: `_check_formats(self, formats)`
        - `self.get_output_path('temp')`
        - `self.dl(temp_file.name, f, test=True)`

    - `1969`: `_default_format_spec(self, info_dict, download=True)`
        - `simulate`
        - `live_from_start`
        - `outtmpl`
        - `allow_multiple_audio_streams`

    - `1992`: `build_format_selector(self, format_spec)`
        - `allow_multiple_audio_streams`
        - `allow_multiple_video_streams`
        - `check_formats`
        <!-- 2107: _merge(formats_pair) -->
        - `merge_output_format`
        - `prefer_free_formats`

    - `2323`: `_calc_headers(self, info_dict)`
        - `http_headers`

    - `2337`: `_calc_cookies(self, url)`
        - `self.cookiejar`

    - `2342`: `_sort_thumbnails(self, thumbnails)`

    - `2350`: `_sanitize_thumbnails(self, info_dict)`
        - `check_formats`

    - `2383`: `_fill_common_fields(self, info_dict, is_video=True)`

    - `2383`: `_fill_common_fields(self, info_dict, is_video=True)`

    - `2436`: `_raise_pending_errors(self, info)`

    - `2441`: `process_video_result(self, info_dict, download=True)`
        - TODO

    - `2756`: `process_subtitles(self, video_id, normal_subtitles, automatic_captions)`
        - TODO

    - `2812`: `_forceprint(self, key, info_dict)`
        - `forceprint`
        - `print_to_file`

    - `2844`: `__forced_printings(self, info_dict, filename, incomplete)`
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

    - `2885`: `dl(self, name, info, subtitle=False, test=False)`
        - `verbose`
        - `quiet`
        - `self`

    - `2920`: `existing_file(self, filepaths, *, default_overwrite=True)`
        - `overwrites`

    - `2930`: `process_info(self, info_dict)`
        - `self.post_extract(info_dict)`
        - `self._num_downloads += 1`
        - `max_downloads`
        - `simulate`
        - `force_write_download_archive`
        - `writeannotations`
        - `overwrites`

        <!-- 3020: _write_link_file(link_type) -->
        - `overwrites`
        - `writeurllink`
        - `writewebloclink`
        - `writedesktoplink`
        - `writelink`

        - `self.pre_process(info_dict, 'before_dl', files_to_move)`
        - `skip_download`
        - `self.run_pp(MoveFilesAfterDownloadPP(self, False), info_dict)`

        <!-- 3081: existing_video_file(*filepaths) -->
        - `final_ext`

        - `merge_output_format`
        - `FFmpegMergerPP(self)`
        - `allow_unplayable_formats`
        - `ignoreerrors`

        <!-- 3214: fixup() -->
        - `fixup`

        - `get_suitable_downloader(info_dict, self.params)`

    - `3287`: `__download_wrapper(self, func)`
        - `break_per_url`
        - `dump_single_json`
        - `self.post_extract(res)`

    - `3305`: `download(self, url_list)`
        - `outtmpl`
        - `max_downloads`
        - `force_generic_extractor`

    - `3321`: `download_with_info_file(self, info_filename)`
        - `clean_infojson`

    - `3341`: `sanitize_info(info_dict, remove_private_keys=False)`
    - `3375`: `filter_requested_info(info_dict, actually_filter=True)`
    - `3379`: `_delete_downloaded_files(self, *files_to_delete, info={}, msg=None)`
    - `3391`: `post_extract(info_dict)`
    - `3403`: `run_pp(self, pp, infodict)`
        - `ignoreerrors`
        - `keepvideo`
    - `3426`: `run_all_pps(self, key, info, *, additional_pps=None)`
        - `additional_pps`?
        - `self._pps`
        - `self.run_pp(pp, info)`
    - `3432`: `pre_process(self, ie_info, key='pre_process', files_to_move=None)`
        - `self.run_all_pps(key, info)`
    - `3443`: `post_process(self, filename, info, files_to_move=None)`
        - `self.run_all_pps('post_process', info, additional_pps=info.get('__postprocessors'))`
        - `self`
        - `self.run_pp(MoveFilesAfterDownloadPP(self), info)`
        - `self.run_all_pps('after_move', info)`
    - `3452`: `_make_archive_id(self, info_dict)`
        - Can be static
    - `3472`: `in_download_archive(self, info_dict)`
        - `self.archive`
    - `3480`: `record_download_archive(self, info_dict)`
        - `download_archive`
        - `self.archive`
    - `3494`: `format_resolution(format, default='unknown')`
        - static
    - `3507`: `_list_format_headers(self, *headers)`
        - `listformats_table`
    - `3512`: `_format_note(self, fdict)`
        - Can be static
    - `3572`: `render_formats_table(self, info_dict)`
        - `listformats_table`
    - `3637`: `render_thumbnails_table(self, info_dict)`
        - can be static
    - `3645`: `render_subtitles_table(self, video_id, subtitles)`
        - `video_id` prameter unused
    - `3659`: `__list_table(self, video_id, name, func, *args)`
    - `3667`: `list_formats(self, info_dict)`
    - `3670`: `list_thumbnails(self, info_dict)`
    - `3673`: `list_subtitles(self, video_id, subtitles, name='subtitles')`
    - `3676`: `urlopen(self, req)`
        - `self._opener`
    - `3682`: `print_debug_header(self)`
        - `verbose`
        - `logger`
        - `FFmpegPostProcessor.get_versions_and_features(self)`
        - never used: `call_home`
    - `3777`: `_setup_opener(self)`
        - `socket_timeout`
        - `cookiesfrombrowser`
        - `cookiefile`
        - `proxy`
        - `self.cookiejar`
        - `debug_printtraffic`
        - `make_HTTPS_handler(self.params, debuglevel=debuglevel)`
        - `YoutubeDLHandler(self.params, debuglevel=debuglevel)`
    - `3827`: `encode(self, s)`
    - `3837`: `get_encoding(self)`
        - `encoding`
    - `3843`: `_write_info_json(self, label, ie_result, infofn, overwrite=None)`
        - `overwrites`
        - `writeinfojson`
        - `clean_infojson`
    - `3866`: `_write_description(self, label, ie_result, descfn)`
        - `writedescription`
        - `overwrites`
    - `3890`: `_write_subtitles(self, info_dict, filename)`
        - `writesubtitles`
        - `ignoreerrors`
    - `3943`: `_write_thumbnails(self, label, info_dict, filename, thumb_filename_base=None)`
        - `write_all_thumbnails`
        - `writethumbnail`

## Things to revisit:
- search for `self.params`
- search for `self._pps`
- `get_suitable_downloader`

## Things noticed while going through code
- `877`: If console sequences are supported, it should use these instead on windows.
        API has been declared [deprecated](https://learn.microsoft.com/en-us/windows/console/setconsoletitle)
- `1105`: `info_dict.setdefault('epoch', int(time.time()))  # keep epoch consistent once set`
    This mutates the `info_dict`, which might be unexpected. Set epoch after copy?
- `2297`: potential to break on multiple lines?
