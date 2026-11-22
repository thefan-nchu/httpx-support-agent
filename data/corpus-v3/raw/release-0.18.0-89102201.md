## 0.18.0 (27th April, 2021)

The 0.18.x release series formalises our low-level Transport API, introducing the base classes `httpx.BaseTransport` and `httpx.AsyncBaseTransport`.

See the "[Custom transports](https://www.python-httpx.org/advanced/transports/#custom-transports)" documentation and the [`httpx.BaseTransport.handle_request()`](https://github.com/encode/httpx/blob/397aad98fdc8b7580a5fc3e88f1578b4302c6382/httpx/_transports/base.py#L77-L147) docstring for more complete details on implementing custom transports.

Pull request #1522 includes a checklist of differences from the previous `httpcore` transport API, for developers implementing custom transports.

The following API changes have been issuing deprecation warnings since 0.17.0 onwards, and are now fully deprecated...

* You should now use httpx.codes consistently instead of httpx.StatusCodes.
* Use limits=... instead of pool_limits=....
* Use proxies={"http://": ...} instead of proxies={"http": ...} for scheme-specific mounting.

### Changed

* Transport instances now inherit from `httpx.BaseTransport` or `httpx.AsyncBaseTransport`,
  and should implement either the `handle_request` method or `handle_async_request` method. (Pull #1522, #1550)
* The `response.ext` property and `Response(ext=...)` argument are now named `extensions`. (Pull #1522)
* The recommendation to not use `data=<bytes|str|bytes (a)iterator>` in favour of `content=<bytes|str|bytes (a)iterator>` has now been escalated to a deprecation warning. (Pull #1573)
* Drop `Response(on_close=...)` from API, since it was a bit of leaking implementation detail. (Pull #1572)
* When using a client instance, cookies should always be set on the client, rather than on a per-request basis. We prefer enforcing a stricter API here because it provides clearer expectations around cookie persistence, particularly when redirects occur. (Pull #1574)
* The runtime exception `httpx.ResponseClosed` is now named `httpx.StreamClosed`. (#1584)
* The `httpx.QueryParams` model now presents an immutable interface. There is a discussion on [the design and motivation here](https://github.com/encode/httpx/discussions/1599). Use `client.params = client.params.merge(...)` instead of `client.params.update(...)`. The basic query manipulation methods are `query.set(...)`, `query.add(...)`, and `query.remove()`. (#1600)

### Added

* The `Request` and `Response` classes can now be serialized using pickle. (#1579)
* Handle `data={"key": [None|int|float|bool]}` cases. (Pull #1539)
* Support `httpx.URL(**kwargs)`, for example `httpx.URL(scheme="https", host="www.example.com", path="/')`, or `httpx.URL("https://www.example.com/", username="tom@gmail.com", password="123 456")`. (Pull #1601)
* Support `url.copy_with(params=...)`. (Pull #1601)
* Add `url.params` parameter, returning an immutable `QueryParams` instance. (Pull #1601)
* Support query manipulation methods on the URL class. These are `url.copy_set_param()`, `url.copy_add_param()`, `url.copy_remove_param()`, `url.copy_merge_params()`. (Pull #1601)
* The `httpx.URL` class now performs port normalization, so `:80` ports are stripped from `http` URLs and `:443` ports are stripped from `https` URLs. (Pull #1603)
* The `URL.host` property returns unicode strings for internationalized domain names. The `URL.raw_host` property returns byte strings with IDNA escaping applied. (Pull #1590)

### Fixed

* Fix Content-Length for cases of `files=...` where unicode string is used as the file content. (Pull #1537)
* Fix some cases of merging relative URLs against `Client(base_url=...)`. (Pull #1532)
* The `request.content` attribute is now always available except for streaming content, which requires an explicit `.read()`. (Pull #1583)

