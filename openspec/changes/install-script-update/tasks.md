## 1. Installer Script Update

- [x] 1.1 Add `UPDATE_MODE` check and update installation header/messages conditionally
- [x] 1.2 Implement safe repository updating (git pull / git fetch fallback, warn on errors instead of crashing)
- [x] 1.3 Implement `.env` configuration preservation logic (skip configuration step if `.env` exists)

## 2. Verification

- [x] 2.1 Verify fresh installation behaves correctly
- [x] 2.2 Verify update installation behaves correctly, preserving existing `.env` file
- [x] 2.3 Verify update installation does not crash when git remote tracking or local status is divergent (simulate git pull error and verify script completes successfully)
