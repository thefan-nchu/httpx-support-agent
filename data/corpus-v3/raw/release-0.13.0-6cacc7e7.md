## 0.13.0.dev0 (April 30th, 2020)

The 0.13.0.dev0 is a *pre-release* version. To install it, use `pip install httpx --pre`.

This release switches to `httpcore` for all the internal networking, which means:

* We're using the same codebase for both our sync and async clients.
* HTTP/2 support is now available with the sync client.
* We no longer have a `urllib3` dependency for our sync client, although there is still an *optional* `URLLib3Dispatcher` class.

It also means we've had to remove our UDS support, since maintaining that would have meant having to push back our work towards a 1.0 release, which isn't a trade-off we wanted to make.

### Changed

* Use `httpcore` for underlying HTTP transport. Drop `urllib3` requirement. (Pull #804)

### Added

* Added `URLLib3Dispatcher` class for optional `urllib3` transport support. (Pull #804)
* Streaming multipart uploads. (Pull #857)

### Fixed

* Performance improvement in brotli decoder. (Pull #906)
* Proper warning level of deprecation notice in `Response.stream` and `Response.raw`. (Pull #908)
* Fix support for generator based WSGI apps. (Pull #887)

### Removed

* Dropped support for `Client(uds=...)` (Pull #804)

---

