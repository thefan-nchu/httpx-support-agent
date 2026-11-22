## 0.27.1 (27th August, 2024)

### Added

* Support for `zstd` content decoding using the python `zstandard` package is added. Installable using `httpx[zstd]`. (#3139)

### Fixed

* Improved error messaging for `InvalidURL` exceptions. (#3250)
* Fix `app` type signature in `ASGITransport`. (#3109)

