## 0.18.2 (17th June, 2021)

### Added

* Support for Python 3.10. (Pull #1687)
* Expose `httpx.USE_CLIENT_DEFAULT`, used as the default to `auth` and `timeout` parameters in request methods. (Pull #1634)
* Support [HTTP/2 "prior knowledge"](https://python-hyper.org/projects/hyper-h2/en/v2.3.1/negotiating-http2.html#prior-knowledge), using `httpx.Client(http1=False, http2=True)`. (Pull #1624)

### Fixed

* Clean up some cases where warnings were being issued. (Pull #1687)
* Prefer Content-Length over Transfer-Encoding: chunked for content=<file-like> cases. (Pull #1619)

