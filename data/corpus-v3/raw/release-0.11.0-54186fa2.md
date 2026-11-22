## 0.11.0 (January 9th, 2020)

The 0.11 release reintroduces our sync support, so that `httpx` now supports both a standard thread-concurrency API, and an async API.

Existing async `httpx` users that are upgrading to 0.11 should ensure that:

* Async codebases should always use a client instance to make requests, instead of the top-level API.
* The async client is named as `httpx.AsyncClient()`, instead of `httpx.Client()`.
* When instantiating proxy configurations use the `httpx.Proxy()` class, instead of the previous `httpx.HTTPProxy()`. This new configuration class works for configuring both sync and async clients.

We believe the API is now pretty much stable, and are aiming for a 1.0 release sometime on or before April 2020.

### Changed

- Top level API such as `httpx.get(url, ...)`, `httpx.post(url, ...)`, `httpx.request(method, url, ...)` becomes synchronous.
- Added `httpx.Client()` for synchronous clients, with `httpx.AsyncClient` being used for async clients.
- Switched to `proxies=httpx.Proxy(...)` for proxy configuration.
- Network connection errors are wrapped in `httpx.NetworkError`, rather than exposing lower-level exception types directly.

### Removed

- The `request.url.origin` property and `httpx.Origin` class are no longer available.
- The per-request `cert`, `verify`, and `trust_env` arguments are escalated from raising errors if used, to no longer being available. These arguments should be used on a per-client instance instead, or in the top-level API.
- The `stream` argument has escalated from raising an error when used, to no longer being available. Use the `client.stream(...)` or `httpx.stream()` streaming API instead.

### Fixed

- Redirect loop detection matches against `(method, url)` rather than `url`. (Pull #734)

---

