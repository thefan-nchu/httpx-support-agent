## 0.7.5 (October 10, 2019)

### Added

- Allow lists of values to be passed to `params`. (Pull #386)
- `ASGIDispatch`, `WSGIDispatch` are now available in the `httpx.dispatch` namespace. (Pull #407)
- `HTTPError` is now available in the `httpx` namespace.  (Pull #421)
- Add support for `start_tls()` to the Trio concurrency backend. (Pull #467)

### Fixed

- Username and password are no longer included in the `Host` header when basic authentication
  credentials are supplied via the URL. (Pull #417)

### Removed

- The `.delete()` function no longer has `json`, `data`, or `files` parameters
  to match the expected semantics of the `DELETE` method. (Pull #408)
- Removed the `trio` extra. Trio support is detected automatically. (Pull #390)

