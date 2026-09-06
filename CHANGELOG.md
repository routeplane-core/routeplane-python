# Changelog

## 0.2.3 — 2026-09-06

### Fixed

- Correct legacy feedback serialization: existing `request_id`/`score` arguments
  now send `trace_id`/integer `value`. Only integer scores from −10 through 10
  are valid; integral floats are accepted without rescaling. Fractional,
  out-of-range, boolean, non-numeric and nonfinite scores fail before dispatch.
- Reject unsupported nonempty comments, including whitespace-only text, instead
  of sending them. Omitted, `None` and empty comments are omitted. Both client
  classes retain their synchronous feedback helper and `None` return shape.
