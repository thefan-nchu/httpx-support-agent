## 0.7.4 (September 25, 2019)

### Added

- Add Trio concurrency backend. (Pull #276)
- Add `params` parameter to `Client` for setting default query parameters. (Pull #372)
- Add support for `SSL_CERT_FILE` and `SSL_CERT_DIR` environment variables. (Pull #307)
- Add debug logging to calls into ASGI apps. (Pull #371)
- Add debug logging to SSL configuration. (Pull #378)

### Fixed

- Fix a bug when using `Client` without timeouts in Python 3.6. (Pull #383)
- Propagate `Client` configuration to HTTP proxies. (Pull #377)

