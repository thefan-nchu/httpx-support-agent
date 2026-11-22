## 0.14.3 (September 2nd, 2020)

### Added

* `http.Response()` may now be instantiated without a `request=...` parameter. Useful for some unit testing cases. (Pull #1238)
* Add `103 Early Hints` and `425 Too Early` status codes. (Pull #1244)

### Fixed

* `DigestAuth` now handles responses that include multiple 'WWW-Authenticate' headers. (Pull #1240)
* Call into transport `__enter__`/`__exit__` or `__aenter__`/`__aexit__` when client is used in a context manager style. (Pull #1218)

