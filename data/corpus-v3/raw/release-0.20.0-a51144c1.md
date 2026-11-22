## 0.20.0 (13th October, 2021)

The 0.20.0 release adds an integrated command-line client, and also includes some
design changes. The most notable of these is that redirect responses are no longer
automatically followed, unless specifically requested.

This design decision prioritises a more explicit approach to redirects, in order
to avoid code that unintentionally issues multiple requests as a result of
misconfigured URLs.

For example, previously a client configured to send requests to `http://api.github.com/`
would end up sending every API request twice, as each request would be redirected to `https://api.github.com/`.

If you do want auto-redirect behaviour, you can enable this either by configuring
the client instance with `Client(follow_redirects=True)`, or on a per-request
basis, with `.get(..., follow_redirects=True)`.

This change is a classic trade-off between convenience and precision, with no "right"
answer. See [discussion #1785](https://github.com/encode/httpx/discussions/1785) for more
context.

The other major design change is an update to the Transport API, which is the low-level
interface against which requests are sent. Previously this interface used only primitive
datastructures, like so...

```python
(status_code, headers, stream, extensions) = transport.handle_request(method, url, headers, stream, extensions)
try
    ...
finally:
    stream.close()
```

Now the interface is much simpler...

```python
response = transport.handle_request(request)
try
    ...
finally:
    response.close()
```

### Changed

* The `allow_redirects` flag is now `follow_redirects` and defaults to `False`.
* The `raise_for_status()` method will now raise an exception for any responses
  except those with 2xx status codes. Previously only 4xx and 5xx status codes
  would result in an exception.
* The low-level transport API changes to the much simpler `response = transport.handle_request(request)`.
* The `client.send()` method no longer accepts a `timeout=...` argument, but the
  `client.build_request()` does. This required by the signature change of the
  Transport API. The request timeout configuration is now stored on the request
  instance, as `request.extensions['timeout']`.

### Added

* Added the `httpx` command-line client.
* Response instances now include `.is_informational`, `.is_success`, `.is_redirect`, `.is_client_error`, and `.is_server_error`
  properties for checking 1xx, 2xx, 3xx, 4xx, and 5xx response types. Note that the behaviour of `.is_redirect` is slightly different in that it now returns True for all 3xx responses, in order to allow for a consistent set of properties onto the different HTTP status code types. The `response.has_redirect_location` location may be used to determine responses with properly formed URL redirects.

### Fixed

* `response.iter_bytes()` no longer raises a ValueError when called on a response with no content. (Pull #1827)
* The `'wsgi.error'` configuration now defaults to `sys.stderr`, and is corrected to be a `TextIO` interface, not a `BytesIO` interface. Additionally, the WSGITransport now accepts a `wsgi_error` configuration. (Pull #1828)
* Follow the WSGI spec by properly closing the iterable returned by the application. (Pull #1830)

