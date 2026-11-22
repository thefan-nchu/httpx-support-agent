## 0.13.2 (May 27th, 2020)

### Fixed

* Include explicit "Content-Length: 0" on POST, PUT, PATCH if no request body is used. (Pull #995)
* Add `http2` option to `httpx.Client`. (Pull #982)
* Tighten up API typing in places. (Pull #992, #999)

