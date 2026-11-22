## 0.16.0 (October 6th, 2020)

### Changed

* Preserve HTTP header casing. (Pull #1338, encode/httpcore#216, python-hyper/h11#104)
* Drop `response.next()` and `response.anext()` methods in favour of `response.next_request` attribute. (Pull #1339)
* Closed clients now raise a runtime error if attempting to send a request. (Pull #1346)

### Added

* Add Python 3.9 to officially supported versions.
* Type annotate `__enter__`/`__exit__`/`__aenter__`/`__aexit__` in a way that supports subclasses of `Client` and `AsyncClient`. (Pull #1336)

