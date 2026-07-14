# Security

## Design boundary

Coding Control Tower is a read-only, localhost-only viewer. It binds to `127.0.0.1`, rejects
path traversal, applies a restrictive Content Security Policy, writes snapshots atomically,
and redacts common credential formats.

Project paths and task titles are intentionally displayed locally. Do not expose the server
through a public proxy.

## Report a vulnerability

Open a private GitHub security advisory for this repository. Do not include live credentials,
private task text, or proprietary source code in a public issue.

