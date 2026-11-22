## 0.24.1 (17th May, 2023)

### Added

* Provide additional context in some `InvalidURL` exceptions. (#2675)

### Fixed

* Fix optional percent-encoding behaviour. (#2671)
* More robust checking for opening upload files in binary mode. (#2630)
* Properly support IP addresses in `NO_PROXY` environment variable. (#2659)
* Set default file for `NetRCAuth()` to `None` to use the stdlib default. (#2667)
* Set logging request lines to INFO level for async requests, in line with sync requests. (#2656)
* Fix which gen-delims need to be escaped for path/query/fragment components in URL. (#2701)

