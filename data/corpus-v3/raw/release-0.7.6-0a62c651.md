## 0.7.6 (November 2, 2019)

### Removed

- Drop `proxies` parameter from the high-level API. (Pull #485)

### Fixed

- Tweak multipart files: omit null filenames, add support for `str` file contents. (Pull #482)
- Cache NETRC authentication per-client. (Pull #400)
- Rely on `getproxies` for all proxy environment variables. (Pull #470)
- Wait for the `asyncio` stream to close when closing a connection. (Pull #494)

