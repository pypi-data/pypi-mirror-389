## 0.2.1 – 2025‑11‑06

### Added
- Optional `select_fields` parameters to list retrieval methods for more efficient queries.
- New public API methods:
  - `SharePointAPI.get_group_users` – fetch users of a SharePoint group.
- Improved error handling with explicit `TypeError` exceptions.
- Detailed docstrings for core classes and methods (enhances IDE support).

### Changed
- HTTP header handling unified; corrected `X‑HTTP‑Method: PUT` for full updates.
- Error handling improved: generic `sys.exit(1)` replaced with explicit `TypeError`/`ConnectionError` exceptions.

### Fixed
- Fixed incorrect PUT header that previously sent a MERGE header.
- Minor docstring formatting issues.

### Security
- Enforced NTLM authentication across all request helpers.