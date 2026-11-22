## 0.15.0 (September 22nd, 2020)

### Added

* Added support for curio. (Pull https://github.com/encode/httpcore/pull/168)
* Added support for event hooks. (Pull #1246)
* Added support for authentication flows which require either sync or async I/O. (Pull #1217)
* Added support for monitoring download progress with `response.num_bytes_downloaded`. (Pull #1268)
* Added `Request(content=...)` for byte content, instead of overloading `Request(data=...)` (Pull #1266)
* Added support for all URL components as parameter names when using `url.copy_with(...)`. (Pull #1285)
* Neater split between automatically populated headers on `Request` instances, vs default `client.headers`. (Pull #1248)
* Unclosed `AsyncClient` instances will now raise warnings if garbage collected. (Pull #1197)
* Support `Response(content=..., text=..., html=..., json=...)` for creating usable response instances in code. (Pull #1265, #1297)
* Support instantiating requests from the low-level transport API. (Pull #1293)
* Raise errors on invalid URL types. (Pull #1259)

### Changed

* Cleaned up expected behaviour for URL escaping. `url.path` is now URL escaped. (Pull #1285)
* Cleaned up expected behaviour for bytes vs str in URL components. `url.userinfo` and `url.query` are not URL escaped, and so return bytes. (Pull #1285)
* Drop `url.authority` property in favour of `url.netloc`, since "authority" was semantically incorrect. (Pull #1285)
* Drop `url.full_path` property in favour of `url.raw_path`, for better consistency with other parts of the API. (Pull #1285)
* No longer use the `chardet` library for auto-detecting charsets, instead defaulting to a simpler approach when no charset is specified. (#1269)

### Fixed

* Swapped ordering of redirects and authentication flow. (Pull #1267)
* `.netrc` lookups should use host, not host+port. (Pull #1298)

### Removed

* The `URLLib3Transport` class no longer exists. We've published it instead as an example of [a custom transport class](https://gist.github.com/florimondmanca/d56764d78d748eb9f73165da388e546e). (Pull #1182)
* Drop `request.timer` attribute, which was being used internally to set `response.elapsed`. (Pull #1249)
* Drop `response.decoder` attribute, which was being used internally. (Pull #1276)
* `Request.prepare()` is now a private method. (Pull #1284)
* The `Headers.getlist()` method had previously been deprecated in favour of `Headers.get_list()`. It is now fully removed.
* The `QueryParams.getlist()` method had previously been deprecated in favour of `QueryParams.get_list()`. It is now fully removed.
* The `URL.is_ssl` property had previously been deprecated in favour of `URL.scheme == "https"`. It is now fully removed.
* The `httpx.PoolLimits` class had previously been deprecated in favour of `httpx.Limits`. It is now fully removed.
* The `max_keepalive` setting had previously been deprecated in favour of the more explicit `max_keepalive_connections`. It is now fully removed.
* The verbose `httpx.Timeout(5.0, connect_timeout=60.0)` style had previously been deprecated in favour of `httpx.Timeout(5.0, connect=60.0)`. It is now fully removed.
* Support for instantiating a timeout config missing some defaults, such as `httpx.Timeout(connect=60.0)`, had previously been deprecated in favour of enforcing a more explicit style, such as `httpx.Timeout(5.0, connect=60.0)`. This is now strictly enforced.

