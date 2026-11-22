## 0.23.1 (18th November, 2022)

**Note**: The 0.23.1 release should have used a proper version bump, rather than a minor point release.
There are API surface area changes that may affect some users.
See the "Removed" section of these release notes for details.

### Added

* Support for Python 3.11. (#2420)
* Allow setting an explicit multipart boundary in `Content-Type` header. (#2278)
* Allow `tuple` or `list` for multipart values, not just `list`. (#2355)
* Allow `str` content for multipart upload files. (#2400)
* Support connection upgrades. See https://www.encode.io/httpcore/extensions/#upgrade-requests

### Fixed

* Don't drop empty query parameters. (#2354)

### Removed

* Upload files *must* always be opened in binary mode. (#2400)
* Drop `.read`/`.aread` from `SyncByteStream`/`AsyncByteStream`. (#2407)
* Drop `RawURL`. (#2241)

