# TEST_ATE

`TEST_ATE` is a PySide6 desktop application for an ATE workflow. It starts with a login form, validates user credentials against the `TEST_DB` SQL Server database, and then opens the main operator window built from the Qt Designer UI template.

## Project Overview

- Framework: `PySide6`
- Entry point: [main.py](/D:/Work/TEST_ATE/main.py)
- Main UI template: [MAIN_ATE.ui](/D:/Work/TEST_ATE/MAIN_ATE.ui)
- Database config: [db_config.ini](/D:/Work/TEST_ATE/db_config.ini)
- Tools config: [tools_config.ini](/D:/Work/TEST_ATE/tools_config.ini)
- Authentication source: `TEST_DB.dbo.logins`

The application currently includes:

- A login screen for username and password entry
- SQL Server credential validation using the values from `db_config.ini`
- A main window loaded from the `.ui` template
- A DB Config dialog that displays the active database settings
- A Tools Config dialog that displays configured hardware resources
- A real-time date and time label on the main window

## Forms

### Login Form

File: [ate_app/login_window.py](/D:/Work/TEST_ATE/ate_app/login_window.py)

Purpose:
- Collects username and password from the user
- Performs keyboard-friendly navigation
- Sends the login request to the application controller

Behavior:
- `Enter` in the username field moves focus to the password field
- `Enter` in the password field moves focus to the login button
- `Enter` on the login button runs the login check
- Invalid or missing credentials show an error message

### Main Window

Files:
- [ate_app/main_window.py](/D:/Work/TEST_ATE/ate_app/main_window.py)
- [MAIN_ATE.ui](/D:/Work/TEST_ATE/MAIN_ATE.ui)

Purpose:
- Displays the main ATE operator interface after successful login
- Uses the Qt Designer `.ui` file as the visual layout source

Current behavior:
- Opens after successful credential validation
- Shows the logged-in user in the status bar
- Displays a live date/time label above the `DB CONFIG` button
- Uses the format `dd/MM/yyyy HH:mm:ss`
- `EXIT` closes the main window
- `DB CONFIG` opens the DB Config form
- `TOOLS CONFIG` opens the hardware resources form

### DB Config Form

File: [ate_app/db_config_window.py](/D:/Work/TEST_ATE/ate_app/db_config_window.py)

Purpose:
- Displays database connection settings read from `db_config.ini`

Displayed fields:
- Database name
- Login
- Server

Behavior:
- Opens from the `DB CONFIG` button in the main window
- Includes a `Close` button to close the dialog

### Tools Config Form

Files:
- [ate_app/tools_config_window.py](/D:/Work/TEST_ATE/ate_app/tools_config_window.py)
- [ate_app/tools_config.py](/D:/Work/TEST_ATE/ate_app/tools_config.py)
- [tools_config.ini](/D:/Work/TEST_ATE/tools_config.ini)

Purpose:
- Displays hardware resource settings read from `tools_config.ini`

Displayed fields:
- PS Main
- PS Second
- Serial COM Port
- SSH
- Network Analyzer
- VNA

Behavior:
- Opens from the `TOOLS CONFIG` button in the main window
- Includes a `Close` button to close the dialog
- Shows a warning message if `tools_config.ini` is missing or incomplete

## Main Modules

- [ate_app/application.py](/D:/Work/TEST_ATE/ate_app/application.py)
  Handles application startup, login flow, and main window creation.

- [ate_app/database.py](/D:/Work/TEST_ATE/ate_app/database.py)
  Reads `db_config.ini`, validates login credentials, and retrieves user status from SQL Server.

- [ate_app/tools_config.py](/D:/Work/TEST_ATE/ate_app/tools_config.py)
  Reads `tools_config.ini` and validates the hardware resource entries for the tools dialog.

## Run

Example command:

```powershell
& "C:\Users\Alexey\AppData\Local\Programs\Python\Python313\python.exe" .\main.py
```
