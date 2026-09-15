# Plan for Issue #5

- [x] Modify FastAPI backend WebSocket endpoint to read the token from the `Authorization` header instead of the URL path, removing `{token}` from the route.
- [x] Update iOS client `Managers.swift` to connect to the new `/ws` URL and send the token via the `Authorization` header.
- [x] Update Android client `Repository.kt` to connect to the new `/ws` URL and send the token via the `Authorization` header.
- [x] Update README documentation.
