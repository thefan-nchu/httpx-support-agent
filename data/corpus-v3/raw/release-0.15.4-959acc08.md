## 0.15.4 (September 25th, 2020)

### Added

* Support direct comparisons between `Headers` and dicts or lists of two-tuples. Eg. `assert response.headers == {"Content-Length": 24}` (Pull #1326)

### Fixed

* Fix automatic `.read()` when `Response` instances are created with `content=<str>` (Pull #1324)

