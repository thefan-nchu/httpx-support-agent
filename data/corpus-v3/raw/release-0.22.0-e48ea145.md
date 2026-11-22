## 0.22.0 (26th January, 2022)

### Added

* Support for [the SOCKS5 proxy protocol](https://www.python-httpx.org/advanced/proxies/#socks) via [the `socksio` package](https://github.com/sethmlarson/socksio). (#2034)
* Support for custom headers in multipart/form-data requests (#1936)

### Fixed

* Don't perform unreliable close/warning on `__del__` with unclosed clients. (#2026)
* Fix `Headers.update(...)` to correctly handle repeated headers (#2038)

