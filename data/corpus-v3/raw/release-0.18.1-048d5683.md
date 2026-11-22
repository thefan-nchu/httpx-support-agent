## 0.18.1 (29th April, 2021)

### Changed

* Update brotli support to use the `brotlicffi` package (Pull #1605)
* Ensure that `Request(..., stream=...)` does not auto-generate any headers on the request instance. (Pull #1607)

### Fixed

* Pass through `timeout=...` in top-level httpx.stream() function. (Pull #1613)
* Map httpcore transport close exceptions to httpx exceptions. (Pull #1606)

