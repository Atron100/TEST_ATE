from __future__ import annotations

import configparser
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


class AuthenticationServiceError(RuntimeError):
    """Raised when the app cannot validate credentials against the database."""


@dataclass(frozen=True)
class DatabaseConfig:
    server: str
    database: str
    username: str
    password: str

    @classmethod
    def from_ini(cls, config_path: Path) -> "DatabaseConfig":
        parser = configparser.ConfigParser()
        files_read = parser.read(config_path)
        if not files_read:
            raise AuthenticationServiceError(
                f"Database config file was not found: {config_path}"
            )

        section = "SQL_SERVER"
        if section not in parser:
            raise AuthenticationServiceError(
                f"Database config is missing the [{section}] section."
            )

        db_section = parser[section]
        required_keys = ("SERVER", "DBNAME", "LOGIN", "PASSWORD")
        missing_keys = [key for key in required_keys if not db_section.get(key)]
        if missing_keys:
            missing = ", ".join(missing_keys)
            raise AuthenticationServiceError(
                f"Database config is missing required keys: {missing}"
            )

        return cls(
            server=db_section["SERVER"],
            database=db_section["DBNAME"],
            username=db_section["LOGIN"],
            password=db_section["PASSWORD"],
        )


class LoginRepository:
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path
        self._db_config = DatabaseConfig.from_ini(config_path)

    def validate_credentials(self, username: str, password: str) -> bool:
        if not username.strip() or not password.strip():
            return False

        query = self._build_login_query(username, password)
        result = self._run_sqlcmd(query)
        output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return any(line == "1" for line in output_lines)

    def return_status(self, username: str) -> int:
        if not username.strip():
            raise AuthenticationServiceError("Username cannot be empty for status retrieval.")

        query = self._return_status_query(username)
        result = self._run_sqlcmd(query)
        output_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not output_lines:
            raise AuthenticationServiceError("Could not retrieve user status from the logins table.")

        try:
            return int(output_lines[0])
        except ValueError as exc:
            raise AuthenticationServiceError("User status in the database is not a valid integer.") from exc

    def _run_sqlcmd(self, query: str) -> subprocess.CompletedProcess[str]:
        sqlcmd_path = shutil.which("sqlcmd")
        if not sqlcmd_path:
            default_path = Path(
                r"C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE"
            )
            if default_path.exists():
                sqlcmd_path = str(default_path)

        if not sqlcmd_path:
            raise AuthenticationServiceError(
                "sqlcmd was not found. Install SQL Server command-line tools to enable login checks."
            )

        completed = subprocess.run(
            [
                sqlcmd_path,
                "-S",
                self._db_config.server,
                "-d",
                self._db_config.database,
                "-U",
                self._db_config.username,
                "-P",
                self._db_config.password,
                "-h",
                "-1",
                "-W",
                "-Q",
                query,
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        if completed.returncode != 0:
            details = completed.stderr.strip() or completed.stdout.strip()
            raise AuthenticationServiceError(
                f"Database login check failed. {details or 'sqlcmd returned an unknown error.'}"
            )

        return completed

    @staticmethod
    def _build_login_query(username: str, password: str) -> str:
        safe_username = username.replace("'", "''")
        safe_password = password.replace("'", "''")
        return (
            "SET NOCOUNT ON; "
            "SELECT TOP 1 1 "
            "FROM logins "
            f"WHERE username = '{safe_username}' "
            f"AND password = '{safe_password}';"
        )

    @staticmethod
    def _return_status_query(username: str) -> str:
        safe_username = username.replace("'", "''")
        return (
            "SET NOCOUNT ON; "
            "SELECT TOP 1 status "
            "FROM logins "
            f"WHERE username = '{safe_username}';"
        )
