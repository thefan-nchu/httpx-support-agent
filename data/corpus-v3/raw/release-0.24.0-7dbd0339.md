## 0.24.0 (6th April, 2023)

### Changed

* The logging behaviour has been changed to be more in-line with other standard Python logging usages. We no longer have a custom `TRACE` log level, and we no longer use the `HTTPX_LOG_LEVEL` environment variable to auto-configure logging. We now have a significant amount of `DEBUG` logging available at the network level. Full documentation is available at https://www.python-httpx.org/logging/ (#2547, encode/httpcore#648)
* The `Response.iter_lines()` method now matches the stdlib behaviour and does not include the newline characters. It also resolves a performance issue. (#2423)
* Query parameter encoding switches from using + for spaces and %2F for forward slash, to instead using %20 for spaces and treating forward slash as a safe, unescaped character. This differs from `requests`, but is in line with browser behavior in Chrome, Safari, and Firefox. Both options are RFC valid. (#2543)
* NetRC authentication is no longer automatically handled, but is instead supported by an explicit `httpx.NetRCAuth()` authentication class. See the documentation at https://www.python-httpx.org/advanced/authentication/#netrc-authentication (#2525)

### Removed

* The `rfc3986` dependancy has been removed. (#2252)

