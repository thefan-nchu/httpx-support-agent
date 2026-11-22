## 0.10.0 (December 29th, 2019)

The 0.10.0 release makes some changes that will allow us to support both sync and async interfaces.

In particular with streaming responses the `response.read()` method becomes `response.aread()`, and the `response.close()` method becomes `response.aclose()`.

If following redirects explicitly the `response.next()` method becomes `response.anext()`.

### Fixed

- End HTTP/2 streams immediately on no-body requests, rather than sending an empty body message. (Pull #682)
- Improve typing for `Response.request`: switch from `Optional[Request]` to `Request`. (Pull #666)
- `Response.elapsed` now reflects the entire download time. (Pull #687, #692)

### Changed

- Added `AsyncClient` as a synonym for `Client`. (Pull #680)
- Switch to `response.aread()` for conditionally reading streaming responses. (Pull #674)
- Switch to `response.aclose()` and `client.aclose()` for explicit closing. (Pull #674, #675)
- Switch to `response.anext()` for resolving the next redirect response. (Pull #676)

### Removed

- When using a client instance, the per-request usage of `verify`, `cert`, and `trust_env` have now escalated from raising a warning to raising an error. You should set these arguments on the client instead. (Pull #617)
- Removed the undocumented `request.read()`, since end users should not require it.

---

