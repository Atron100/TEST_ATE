# Code Review

Date: 2026-03-19
Scope: static review of the current project state only. No source files were modified as part of this review.

## Findings

### 1. High: the app can crash on startup or when opening DB config if `db_config.ini` is missing or malformed

- `ATEApplication` constructs `LoginRepository` during startup, and `LoginRepository` immediately parses `db_config.ini`. Any config error raises `AuthenticationServiceError` before the login window is even shown. There is no recovery path or user-facing error handling for that startup path.
- The same pattern exists when the operator opens the DB Config dialog from the main window: `DBConfigWindow` reparses the config in its constructor, and any parsing failure bubbles out of the click handler.

References:
- `ate_app/application.py:13-15`
- `ate_app/database.py:22-43`
- `ate_app/main_window.py:319-324`
- `ate_app/db_config_window.py:11-16`

Impact:
- A bad deployment or edited INI file turns into a hard crash instead of a recoverable configuration error.

### 2. High: sequence selection can crash because the config points to a missing JSON file and load errors are not handled

- `agile_config.ini` advertises an `RX` sequence file, but `RX_PCBA_12032026.json` is not present in the repository.
- `MainWindow._load_selected_sequence()` calls `SequenceLoader.load()` directly without checking file existence or handling `FileNotFoundError` / JSON parsing failures.

References:
- `agile_config.ini:1-4`
- `ate_app/main_window.py:97-111`
- `ate_app/main_window.py:134-145`
- `ate_app/sequence.py:47-48`

Impact:
- As soon as the user selects the missing sequence, the UI will raise an exception and likely terminate.

### 3. High: the test runner reports synthetic PASS/FAIL results without executing the sequence commands

- `_run_all_tests()` marks every checked test with the result returned by `_execute_test()`, but `_execute_test()` does not run any hardware command.
- `_calculate_measured_value()` returns `1` for `BOOL` tests and otherwise invents a midpoint between min/max limits. That means tests can pass even when the device is disconnected or the instrument command would fail.
- The sequence files already define real commands such as `CPLD_BURN`, `PS_MAIN_MEASURE_CURRENT`, `DMM_MEASURE_VOLTAGE`, and `READ_DIGITAL`, but none of them are dispatched by the application logic.

References:
- `ate_app/main_window.py:222-276`
- `DIG_PCBA_28012025.json:26-30`
- `DIG_PCBA_28012025.json:64-67`
- `TX_PCBA_13012025.json:27-30`
- `TX_PCBA_13012025.json:64-65`

Impact:
- Operators can get false PASS results, which is the highest-risk failure mode for an ATE application.

### 4. Medium: credentials are handled and stored in plaintext

- The SQL Server service credentials are stored directly in `db_config.ini`.
- User authentication is done by comparing the typed password directly against the `logins.password` column.

References:
- `db_config.ini:1-5`
- `ate_app/database.py:127-145`

Impact:
- Anyone with local file access can read the DB service password, and the login table design appears to require plaintext or reversibly stored user passwords.

### 5. Medium: user status is fetched but never used for authorization or UI restrictions

- Login status is retrieved from the database and passed into `MainWindow`.
- `MainWindow` stores `_status` but does not use it anywhere to gate actions or alter the UI.

References:
- `ate_app/application.py:31-45`
- `ate_app/main_window.py:22-24`

Impact:
- If `status` is intended to represent roles or permissions, the current implementation grants the same capabilities to every valid user.

## Testing / Review Notes

- This review was based on static inspection of the repository.
- I did not run tests or launch the UI, to avoid side effects and to keep the existing project state unchanged.

## Suggested Next Focus

1. Add error handling around config and sequence loading so the UI degrades gracefully instead of crashing.
2. Replace the synthetic test execution path with a real command-dispatch layer before using PASS/FAIL results operationally.
3. Rework authentication and secret handling so passwords are not stored or compared in plaintext.
