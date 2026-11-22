## 0.11.1 (January 17th, 2020)

### Fixed

* Fixed usage of `proxies=...` on `Client()`. (Pull #763)
* Support both `zlib` and `deflate` style encodings on `Content-Encoding: deflate`. (Pull #758)
* Fix for streaming a redirect response body with `allow_redirects=False`. (Pull #766)
* Handle redirect with malformed Location headers missing host. (Pull #774)

