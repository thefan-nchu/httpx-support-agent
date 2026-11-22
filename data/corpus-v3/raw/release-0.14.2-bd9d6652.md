## 0.14.2 (August 24th, 2020)

### Added

* Support `client.get(..., auth=None)` to bypass the default authentication on a clients. (Pull #1115)
* Support `client.auth = ...` property setter. (Pull #1185)
* Support `httpx.get(..., proxies=...)` on top-level request functions. (Pull #1198)
* Display instances with nicer import styles. (Eg. <httpx.ReadTimeout ...>) (Pull #1155)
* Support `cookies=[(key, value)]` list-of-two-tuples style usage. (Pull #1211)

### Fixed

* Ensure that automatically included headers on a request may be modified. (Pull #1205)
* Allow explicit `Content-Length` header on streaming requests. (Pull #1170)
* Handle URL quoted usernames and passwords properly. (Pull #1159)
* Use more consistent default for `HEAD` requests, setting `allow_redirects=True`. (Pull #1183)
* If a transport error occurs while streaming the response, raise an `httpx` exception, not the underlying `httpcore` exception. (Pull #1190)
* Include the underlying `httpcore` traceback, when transport exceptions occur. (Pull #1199)

