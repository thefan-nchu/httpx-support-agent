## 0.19.0 (19th August, 2021)

### Added

* Add support for `Client(allow_redirects=<bool>)`. (Pull #1790)
* Add automatic character set detection, when no `charset` is included in the response `Content-Type` header. (Pull #1791)

### Changed

* Event hooks are now also called for any additional redirect or auth requests/responses. (Pull #1806)
* Strictly enforce that upload files must be opened in binary mode. (Pull #1736)
* Strictly enforce that client instances can only be opened and closed once, and cannot be re-opened. (Pull #1800)
* Drop `mode` argument from `httpx.Proxy(..., mode=...)`. (Pull #1795)

