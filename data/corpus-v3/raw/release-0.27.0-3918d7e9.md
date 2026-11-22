## 0.27.0 (21st February, 2024)

### Deprecated

* The `app=...` shortcut has been deprecated. Use the explicit style of `transport=httpx.WSGITransport()` or `transport=httpx.ASGITransport()` instead.

### Fixed

* Respect the `http1` argument while configuring proxy transports. (#3023)
* Fix RFC 2069 mode digest authentication. (#3045)

