---
description: How to run tests safely without affecting production data
---

To prevent accidental data loss in the production database (`accessories.db`), always use the safe test runner.

### Steps
1. **Always use the safe runner**: Instead of `pytest`, run:
   ```bash
   python3 run_safe_tests.py
   ```
2. **Automated Protection**:
   - The script automatically copies `accessories.db` to `accessories.db.test_backup` before starting.
   - It runs the full test suite via `pytest`.
   - After tests complete (even if they fail), it restores `accessories.db` from the backup.
3. **Environment Isolation**:
   - Tests are configured to use temporary database files (e.g., `test_*.db`), but the runner provides a second layer of defense.
