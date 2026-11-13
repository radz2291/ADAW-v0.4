# Dependency rules

Studio depends on HTTP v1. HTTP and CLI depend on the application service.
Production workflows call service methods and quality measurement. The project
core validates and compiles source without importing Studio or native DawDreamer.
Only the worker imports the native engine. The service owns SQLite writes.

The frontend-absent test starts an API-only instance and uses a standalone HTTP
client plus the CLI to create and edit canonical source, render audio, analyze it
and export WAV. Run it with `python -m pytest tests/test_studio_api.py`.

HTTP is local to the exact loopback origin and uses a per-process mutation token.
Versioned routes, command envelopes, revision IDs and parameter identities remain
independent of display. Source dependencies and token checks belong to the
service. Native workers run under the local Windows user account.
