## 0.17.0 (February 28th, 2021)

### Added

* Add `httpx.MockTransport()`, allowing to mock out a transport using pre-determined responses. (Pull #1401, Pull #1449)
* Add `httpx.HTTPTransport()` and `httpx.AsyncHTTPTransport()` default transports. (Pull #1399)
* Add mount API support, using `httpx.Client(mounts=...)`. (Pull #1362)
* Add `chunk_size` parameter to `iter_raw()`, `iter_bytes()`, `iter_text()`. (Pull #1277)
* Add `keepalive_expiry` parameter to `httpx.Limits()` configuration. (Pull #1398)
* Add repr to `httpx.Cookies` to display available cookies. (Pull #1411)
* Add support for `params=<tuple>` (previously only `params=<list>` was supported). (Pull #1426)

### Fixed

* Add missing `raw_path` to ASGI scope. (Pull #1357)
* Tweak `create_ssl_context` defaults to use `trust_env=True`. (Pull #1447)
* Properly URL-escape WSGI `PATH_INFO`. (Pull #1391)
* Properly set default ports in WSGI transport. (Pull #1469)
* Properly encode slashes when using `base_url`. (Pull #1407)
* Properly map exceptions in `request.aclose()`. (Pull #1465)

