## 0.26.0 (20th December, 2023)

### Added

* The `proxy` argument was added. You should use the `proxy` argument instead of the deprecated `proxies`, or use `mounts=` for more complex configurations. (#2879)

### Deprecated

* The `proxies` argument is now deprecated. It will still continue to work, but it will be removed in the future. (#2879)

### Fixed

* Fix cases of double escaping of URL path components. Allow / as a safe character in the query portion. (#2990)
* Handle `NO_PROXY` envvar cases when a fully qualified URL is supplied as the value. (#2741)
* Allow URLs where username or password contains unescaped '@'. (#2986)
* Ensure ASGI `raw_path` does not include URL query component. (#2999)
* Ensure `Response.iter_text()` cannot yield empty strings. (#2998)

