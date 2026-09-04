# Files and artifacts

Kokoro exposes three related projections without making them interchangeable:

- Session `files` describe workspace files by path, MIME type, and byte count.
- Session `deliveries` describe produced outputs with content hash, path, title, MIME type, size, run ID, and creation time.
- Library items are a storage-backed product projection returned by `GET /v1/library`.

Treat returned paths and URLs as opaque service projections. Do not derive an internal object-store key or owner endpoint from them.

## Project resource intake

The project resource operation currently accepts one or more multipart `files` and returns the generic success envelope. It does not yet expose a public resource ID, scan status, processing state, or polling operation. The [upload lifecycle guide](../guides/upload-lifecycle) explains this beta boundary.
