## 0.7.2 (August 28, 2019)

- Enforce using `httpx.AsyncioBackend` for the synchronous client. (Pull #232)
- `httpx.ConnectionPool` will properly release a dropped connection. (Pull #230)
- Remove the `raise_app_exceptions` argument from `Client`. (Pull #238)
- `DecodeError` will no longer be raised for an empty body encoded with Brotli. (Pull #237)
- Added `http_versions` parameter to `Client`. (Pull #250)
- Only use HTTP/1.1 on short-lived connections like `httpx.get()`. (Pull #284)
- Convert `Client.cookies` and `Client.headers` when set as a property. (Pull #274)
- Setting `HTTPX_DEBUG=1` enables debug logging on all requests. (Pull #277)

