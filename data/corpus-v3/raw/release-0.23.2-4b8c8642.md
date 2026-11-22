## 0.23.2 (2nd January, 2023)

### Added

* Support digest auth nonce counting to avoid multiple auth requests. (#2463)

### Fixed

* Multipart file uploads where the file length cannot be determine now use chunked transfer encoding, rather than loading the entire file into memory in order to determine the `Content-Length`. (#2382)
* Raise `TypeError` if content is passed a dict-instance. (#2495)
* Partially revert the API breaking change in 0.23.1, which removed `RawURL`. We continue to expose a `url.raw` property which is now a plain named-tuple. This API is still expected to be deprecated, but we will do so with a major version bump. (#2481)

