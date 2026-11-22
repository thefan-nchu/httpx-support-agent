## 0.25.0 (11th September, 2023)

### Removed

* Drop support for Python 3.7. (#2813)

### Added

* Support HTTPS proxies. (#2845)
* Change the type of `Extensions` from `Mapping[Str, Any]` to `MutableMapping[Str, Any]`. (#2803)
* Add `socket_options` argument to `httpx.HTTPTransport` and `httpx.AsyncHTTPTransport` classes. (#2716)
* The `Response.raise_for_status()` method now returns the response instance. For example: `data = httpx.get('...').raise_for_status().json()`. (#2776)

### Fixed

* Return `500` error response instead of exceptions when `raise_app_exceptions=False` is set on `ASGITransport`. (#2669)
* Ensure all `WSGITransport` environs have a `SERVER_PROTOCOL`. (#2708)
* Always encode forward slashes as `%2F` in query parameters (#2723)
* Use Mozilla documentation instead of `httpstatuses.com` for HTTP error reference (#2768)

