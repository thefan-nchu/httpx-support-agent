## 0.7.3 (September 20, 2019)

### Added

- HTTP Proxy support. (Pulls #259, #353)
- Add Digest authentication. (Pull #332)
- Add `.build_request()` method to `Client` and `AsyncClient`. (Pull #319)
- Add `.elapsed` property on responses. (Pull #351)
- Add support for `SSLKEYLOGFILE` in Python 3.8b4+. (Pull #301)

### Removed

- Drop NPN support for HTTP version negotiation. (Pull #314)

### Fixed

- Fix distribution of type annotations for mypy (Pull #361).
- Set `Host` header when redirecting cross-origin. (Pull #321)
- Drop `Content-Length` headers on `GET` redirects. (Pull #310)
- Raise `KeyError` if header isn't found in `Headers`. (Pull #324)
- Raise `NotRedirectResponse` in `response.next()` if there is no redirection to perform. (Pull #297)
- Fix bug in calculating the HTTP/2 maximum frame size. (Pull #153)

