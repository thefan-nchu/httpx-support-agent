## 0.14.1 (August 11th, 2020)

### Added

* The `httpx.URL(...)` class now raises `httpx.InvalidURL` on invalid URLs, rather than exposing the underlying `rfc3986` exception. If a redirect response includes an invalid 'Location' header, then a `RemoteProtocolError` exception is raised, which will be associated with the request that caused it. (Pull #1163)

### Fixed

* Handling multiple `Set-Cookie` headers became broken in the 0.14.0 release, and is now resolved. (Pull #1156)

