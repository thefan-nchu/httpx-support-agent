## 0.9.5 (December 20th, 2019)

### Fixed

- Fix Host header and HSTS rewrites when an explicit `:80` port is included in URL. (Pull #649)
- Query Params on the URL string are merged with any `params=...` argument. (Pull #653)
- More robust behavior when closing connections. (Pull #640)
- More robust behavior when handling HTTP/2 headers with trailing whitespace. (Pull #637)
- Allow any explicit `Content-Type` header to take precedence over the encoding default. (Pull #633)

