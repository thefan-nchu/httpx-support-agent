## 0.9.0 (December 6th, 2019)

The 0.9 releases brings some major new features, including:

* A new streaming API.
* Autodetection of either asyncio or trio.
* Nicer timeout configuration.
* HTTP/2 support off by default, but can be enabled.

We've also removed all private types from the top-level package export.

In order to ensure you are only ever working with public API you should make
sure to only import the top-level package eg. `import httpx`, rather than
importing modules within the package.

### Added

- Added concurrency backend autodetection. (Pull #585)
- Added `Client(backend='trio')` and `Client(backend='asyncio')` API. (Pull #585)
- Added `response.stream_lines()` API. (Pull #575)
- Added `response.is_error` API. (Pull #574)
- Added support for `timeout=Timeout(5.0, connect_timeout=60.0)` styles. (Pull #593)

### Fixed

- Requests or Clients with `timeout=None` now correctly always disable timeouts. (Pull #592)
- Request 'Authorization' headers now have priority over `.netrc` authentication info. (Commit 095b691)
- Files without a filename no longer set a Content-Type in multipart data. (Commit ed94950)

### Changed

- Added `httpx.stream()` API. Using `stream=True` now results in a warning. (Pull #600, #610)
- HTTP/2 support is switched to "off by default", but can be enabled explicitly. (Pull #584)
- Switched to `Client(http2=True)` API from `Client(http_versions=["HTTP/1.1", "HTTP/2"])`. (Pull #586)
- Removed all private types from the top-level package export. (Pull #608)
- The SSL configuration settings of `verify`, `cert`, and `trust_env` now raise warnings if used per-request when using a Client instance. They should always be set on the Client instance itself. (Pull #597)
- Use plain strings "TUNNEL_ONLY" or "FORWARD_ONLY" on the HTTPProxy `proxy_mode` argument. The `HTTPProxyMode` enum still exists, but its usage will raise warnings. (#610)
- Pool timeouts are now on the timeout configuration, not the pool limits configuration. (Pull #563)
- The timeout configuration is now named `httpx.Timeout(...)`, not `httpx.TimeoutConfig(...)`. The old version currently remains as a synonym for backwards compatibility.  (Pull #591)

---

