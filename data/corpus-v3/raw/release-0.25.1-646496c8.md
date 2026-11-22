## 0.25.1 (3rd November, 2023)

### Added

* Add support for Python 3.12. (#2854)
* Add support for httpcore 1.0 (#2885)

### Fixed

* Raise `ValueError` on `Response.encoding` being set after `Response.text` has been accessed. (#2852)

