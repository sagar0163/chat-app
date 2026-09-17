# Implementation Plan: Issue 1

- [x] Create `uploads` directory and mount it as StaticFiles in FastAPI for serving.
- [x] Add `UploadFile` endpoint `/upload` handling `image` and `file` types, including file size and type validation.
- [x] Add tests for upload endpoint (valid upload, type validation, size validation, auth, path traversal)
- [x] Harden endpoint: safe extension from content-type, chunked size checks, UPLOAD_DIR config
- [x] Run tests and verify everything passes
- [x] Document endpoint in README/.env.example
- [ ] Remove plan file and final commit, push branch
