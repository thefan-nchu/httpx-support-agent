## 0.12.0 (March 9th, 2020)

The 0.12 release tightens up the API expectations for `httpx` by switching to private module names to enforce better clarity around public API.

All imports of `httpx` should import from the top-level package only, such as `from httpx import Request`, rather than importing from privately namespaced modules such as `from httpx._models import Request`.

### Added

* Support making response body available to auth classes with `.requires_response_body`. (Pull #803)
* Export `NetworkError` exception. (Pull #814)
* Add support for `NO_PROXY` environment variable. (Pull #835)

### Changed

* Switched to private module names. (Pull #785)
* Drop redirect looping detection and the `RedirectLoop` exception, instead using `TooManyRedirects`. (Pull #819)
* Drop `backend=...` parameter on `AsyncClient`, in favour of always autodetecting `trio`/`asyncio`. (Pull #791)

### Fixed

* Support basic auth credentials in proxy URLs. (Pull #780)
* Fix `httpx.Proxy(url, mode="FORWARD_ONLY")` configuration. (Pull #788)
* Fallback to setting headers as UTF-8 if no encoding is specified. (Pull #820)
* Close proxy dispatches classes on client close. (Pull #826)
* Support custom `cert` parameters even if `verify=False`. (Pull #796)
* Don't support invalid dict-of-dicts form data in `data=...`. (Pull #811)

---

