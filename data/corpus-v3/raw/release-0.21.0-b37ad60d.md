## 0.21.0 (15th November, 2021)

The 0.21.0 release integrates against a newly redesigned `httpcore` backend.

Both packages ought to automatically update to the required versions, but if you are
seeing any issues, you should ensure that you have `httpx==0.21.*` and `httpcore==0.14.*` installed.

### Added

* The command-line client will now display connection information when `-v/--verbose` is used.
* The command-line client will now display server certificate information when `-v/--verbose` is used.
* The command-line client is now able to properly detect if the outgoing request
should be formatted as HTTP/1.1 or HTTP/2, based on the result of the HTTP/2 negotiation.

### Removed

* Curio support is no longer currently included. Please get in touch if you require this, so that we can assess priorities.

