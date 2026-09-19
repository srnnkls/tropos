---
paths: "**/*.py"
---

# Networking spec

Requirements for services that talk to other services.

## Timeouts

Outbound HTTP requests MUST configure an explicit timeout.

Async code MUST NOT call blocking I/O such as `requests.get()` or `time.sleep()`.

## Failure handling

Callers MUST NOT swallow exceptions from network calls; log or re-raise them.

Callers SHOULD NOT catch an exception only to re-wrap it without adding context.

## Secrets

Code MUST NOT log credentials, tokens or other secrets.
