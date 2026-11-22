## 0.23.0 (23rd May, 2022)

### Changed

* Drop support for Python 3.6. (#2097)
* Use `utf-8` as the default character set, instead of falling back to `charset-normalizer` for auto-detection. To enable automatic character set detection, see [the documentation](https://www.python-httpx.org/advanced/text-encodings/#using-auto-detection). (#2165)

### Fixed

* Fix `URL.copy_with` for some oddly formed URL cases. (#2185)
* Digest authentication should use case-insensitive comparison for determining which algorithm is being used. (#2204)
* Fix console markup escaping in command line client. (#1866)
* When files are used in multipart upload, ensure we always seek to the start of the file. (#2065)
* Ensure that `iter_bytes` never yields zero-length chunks. (#2068)
* Preserve `Authorization` header for redirects that are to the same origin, but are an `http`-to-`https` upgrade. (#2074)
* When responses have binary output, don't print the output to the console in the command line client. Use output like `<16086 bytes of binary data>` instead. (#2076)
* Fix display of `--proxies` argument in the command line client help. (#2125)
* Close responses when task cancellations occur during stream reading. (#2156)
* Fix type error on accessing `.request` on `HTTPError` exceptions. (#2158)

