## 0.13.0.dev2 (May 12th, 2020)

The 0.13.0.dev2 is a *pre-release* version. To install it, use `pip install httpx --pre`.

### Added

* Logging via HTTPCORE_LOG_LEVEL and HTTPX_LOG_LEVEL environment variables
and TRACE level logging. (HTTPCore Pull #79)

### Fixed

* Reuse of connections on HTTP/2 in close concurrency situations. (HTTPCore Pull #81)
* When using an `app=<ASGI app>` observe neater disconnect behaviour instead of sending empty body messages. (Pull #919)

