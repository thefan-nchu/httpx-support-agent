## 0.14.0 (August 7th, 2020)

The 0.14 release includes a range of improvements to the public API, intended on preparing for our upcoming 1.0 release.

* Our HTTP/2 support is now fully optional. **You now need to use `pip install httpx[http2]` if you want to include the HTTP/2 dependencies.**
* Our HSTS support has now been removed. Rewriting URLs from `http` to `https` if the host is on the HSTS list can be beneficial in avoiding roundtrips to incorrectly formed URLs, but on balance we've decided to remove this feature, on the principle of least surprise. Most programmatic clients do not include HSTS support, and for now we're opting to remove our support for it.
* Our exception hierarchy has been overhauled. Most users will want to stick with their existing `httpx.HTTPError` usage, but we've got a clearer overall structure now. See https://www.python-httpx.org/exceptions/ for more details.

When upgrading you should be aware of the following public API changes. Note that deprecated usages will currently continue to function, but will issue warnings.

* You should now use `httpx.codes` consistently instead of `httpx.StatusCodes`.
* Usage of `httpx.Timeout()` should now always include an explicit default. Eg. `httpx.Timeout(None, pool=5.0)`.
* When using `httpx.Timeout()`, we now have more concisely named keyword arguments. Eg. `read=5.0`, instead of `read_timeout=5.0`.
* Use `httpx.Limits()` instead of `httpx.PoolLimits()`, and `limits=...` instead of `pool_limits=...`.
* The `httpx.Limits(max_keepalive=...)` argument is now deprecated in favour of a more explicit `httpx.Limits(max_keepalive_connections=...)`.
* Keys used with `Client(proxies={...})` should now be in the style of `{"http://": ...}`, rather than `{"http": ...}`.
* The multidict methods `Headers.getlist()` and `QueryParams.getlist()` are deprecated in favour of more consistent `.get_list()` variants.
* The `URL.is_ssl` property is deprecated in favour of `URL.scheme == "https"`.
* The `URL.join(relative_url=...)` method is now `URL.join(url=...)`. This change does not support warnings for the deprecated usage style.

One notable aspect of the 0.14.0 release is that it tightens up the public API for `httpx`, by ensuring that several internal attributes and methods have now become strictly private.

The following previously had nominally public names on the client, but were all undocumented and intended solely for internal usage. They are all now replaced with underscored names, and should not be relied on or accessed.

These changes should not affect users who have been working from the `httpx` documentation.

* `.merge_url()`, `.merge_headers()`, `.merge_cookies()`, `.merge_queryparams()`
* `.build_auth()`, `.build_redirect_request()`
* `.redirect_method()`, `.redirect_url()`, `.redirect_headers()`, `.redirect_stream()`
* `.send_handling_redirects()`, `.send_handling_auth()`, `.send_single_request()`
* `.init_transport()`, `.init_proxy_transport()`
* `.proxies`, `.transport`, `.netrc`, `.get_proxy_map()`

See pull requests #997, #1065, #1071.

Some areas of API which were already on the deprecation path, and were raising warnings or errors in 0.13.x have now been escalated to being fully removed.

* Drop `ASGIDispatch`, `WSGIDispatch`, which have been replaced by `ASGITransport`, `WSGITransport`.
* Drop `dispatch=...`` on client, which has been replaced by `transport=...``
* Drop `soft_limit`, `hard_limit`, which have been replaced by `max_keepalive` and `max_connections`.
* Drop `Response.stream` and` `Response.raw`, which have been replaced by ``.aiter_bytes` and `.aiter_raw`.
* Drop `proxies=<transport instance>` in favor of `proxies=httpx.Proxy(...)`.

See pull requests #1057, #1058.

### Added

* Added dedicated exception class `httpx.HTTPStatusError` for `.raise_for_status()` exceptions. (Pull #1072)
* Added `httpx.create_ssl_context()` helper function. (Pull #996)
* Support for proxy exclusions like `proxies={"https://www.example.com": None}`. (Pull #1099)
* Support `QueryParams(None)` and `client.params = None`. (Pull #1060)

### Changed

* Use `httpx.codes` consistently in favour of `httpx.StatusCodes` which is placed into deprecation. (Pull #1088)
* Usage of `httpx.Timeout()` should now always include an explicit default. Eg. `httpx.Timeout(None, pool=5.0)`. (Pull #1085)
* Switch to more concise `httpx.Timeout()` keyword arguments. Eg. `read=5.0`, instead of `read_timeout=5.0`. (Pull #1111)
* Use `httpx.Limits()` instead of `httpx.PoolLimits()`, and `limits=...` instead of `pool_limits=...`. (Pull #1113)
* Keys used with `Client(proxies={...})` should now be in the style of `{"http://": ...}`, rather than `{"http": ...}`. (Pull #1127)
* The multidict methods `Headers.getlist` and `QueryParams.getlist` are deprecated in favour of more consistent `.get_list()` variants. (Pull #1089)
* `URL.port` becomes `Optional[int]`. Now only returns a port if one is explicitly included in the URL string. (Pull #1080)
* The `URL(..., allow_relative=[bool])` parameter no longer exists. All URL instances may be relative. (Pull #1073)
* Drop unnecessary `url.full_path = ...` property setter. (Pull #1069)
* The `URL.join(relative_url=...)` method is now `URL.join(url=...)`. (Pull #1129)
* The `URL.is_ssl` property is deprecated in favour of `URL.scheme == "https"`. (Pull #1128)

### Fixed

* Add missing `Response.next()` method. (Pull #1055)
* Ensure all exception classes are exposed as public API. (Pull #1045)
* Support multiple items with an identical field name in multipart encodings. (Pull #777)
* Skip HSTS preloading on single-label domains. (Pull #1074)
* Fixes for `Response.iter_lines()`. (Pull #1033, #1075)
* Ignore permission errors when accessing `.netrc` files. (Pull #1104)
* Allow bare hostnames in `HTTP_PROXY` etc... environment variables. (Pull #1120)
* Settings `app=...` or `transport=...` bypasses any environment based proxy defaults. (Pull #1122)
* Fix handling of `.base_url` when a path component is included in the base URL. (Pull #1130)

---

