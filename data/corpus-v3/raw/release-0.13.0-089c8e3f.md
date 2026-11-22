## 0.13.0.dev1 (May 6th, 2020)

The 0.13.0.dev1 is a *pre-release* version. To install it, use `pip install httpx --pre`.

### Fixed

* Passing `http2` flag to proxy dispatchers. (Pull #934)
* Use [`httpcore` v0.8.3](https://github.com/encode/httpcore/releases/tag/0.8.3)
which addresses problems in handling of headers when using proxies.

