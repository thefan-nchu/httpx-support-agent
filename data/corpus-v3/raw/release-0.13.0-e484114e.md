## 0.13.0 (May 22nd, 2020)

This release switches to `httpcore` for all the internal networking, which means:

* We're using the same codebase for both our sync and async clients.
* HTTP/2 support is now available with the sync client.
* We no longer have a `urllib3` dependency for our sync client, although there is still an *optional* `URLLib3Transport` class.

It also means we've had to remove our UDS support, since maintaining that would have meant having to push back our work towards a 1.0 release, which isn't a trade-off we wanted to make.

We also now have [a public "Transport API"](https://www.python-httpx.org/advanced/transports/#custom-transports), which you can use to implement custom transport implementations against. This formalises and replaces our previously private "Dispatch API".

### Changed

* Use `httpcore` for underlying HTTP transport. Drop `urllib3` requirement. (Pull #804, #967)
* Rename pool limit options from `soft_limit`/`hard_limit` to `max_keepalive`/`max_connections`. (Pull #968)
* The previous private "Dispatch API" has now been promoted to a public "Transport API". When customizing the transport use `transport=...`. The `ASGIDispatch` and `WSGIDispatch` class naming is deprecated in favour of `ASGITransport` and `WSGITransport`. (Pull #963)

### Added

* Added `URLLib3Transport` class for optional `urllib3` transport support. (Pull #804, #963)
* Streaming multipart uploads. (Pull #857)
* Logging via HTTPCORE_LOG_LEVEL and HTTPX_LOG_LEVEL environment variables
and TRACE level logging. (Pull encode/httpcore#79)

### Fixed

* Performance improvement in brotli decoder. (Pull #906)
* Proper warning level of deprecation notice in `Response.stream` and `Response.raw`. (Pull #908)
* Fix support for generator based WSGI apps. (Pull #887)
* Reuse of connections on HTTP/2 in close concurrency situations. (Pull encode/httpcore#81)
* Honor HTTP/2 max concurrent streams settings (Pull encode/httpcore#89, encode/httpcore#90)
* Fix bytes support in multipart uploads. (Pull #974)
* Improve typing support for `files=...`. (Pull #976)

### Removed

* Dropped support for `Client(uds=...)` (Pull #804)

