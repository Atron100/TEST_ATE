from __future__ import annotations

import socket
import threading
import time
from dataclasses import dataclass


@dataclass(slots=True)
class GenesysStatus:
    voltage_set: float
    current_set: float
    voltage_measured: float
    current_measured: float
    output_on: bool
    mode: str
    last_error: str


class Gen20_38TcpDriver:
    MAX_VOLTAGE = 20.0
    MAX_CURRENT = 38.0
    MAX_POWER = 760.0
    MAX_COMMANDS_BEFORE_QUERY = 20

    def __init__(self, ip_address: str, port: int = 8003, timeout_ms: int = 2000) -> None:
        if not ip_address or not ip_address.strip():
            raise ValueError("IP address must not be empty.")
        if port <= 0 or port > 65535:
            raise ValueError("Port must be in range 1..65535.")
        if timeout_ms < 100:
            raise ValueError("Timeout must be at least 100 ms.")

        self._ip_address = ip_address.strip()
        self._port = port
        self._timeout_ms = timeout_ms

        self._socket: socket.socket | None = None
        self._reader = None
        self._lock = threading.Lock()
        self._commands_since_query = 0

    @property
    def is_connected(self) -> bool:
        return self._socket is not None and self._reader is not None

    def connect(self) -> None:
        if self.is_connected:
            return

        sock = socket.create_connection(
            (self._ip_address, self._port),
            timeout=self._timeout_ms / 1000.0,
        )
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.settimeout(self._timeout_ms / 1000.0)

        self._socket = sock
        self._reader = sock.makefile("r", encoding="ascii", newline="\n")
        self._commands_since_query = 0

    def disconnect(self) -> None:
        with self._lock:
            if self._reader is not None:
                try:
                    self._reader.close()
                except OSError:
                    pass
            if self._socket is not None:
                try:
                    self._socket.close()
                except OSError:
                    pass

            self._reader = None
            self._socket = None
            self._commands_since_query = 0

    def close(self) -> None:
        self.disconnect()

    def __enter__(self) -> "Gen20_38TcpDriver":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()

    def _ensure_connected(self) -> None:
        if not self.is_connected:
            raise RuntimeError("Power supply is not connected.")

    @staticmethod
    def _format_number(value: float) -> str:
        return f"{value:.3f}".rstrip("0").rstrip(".")

    @staticmethod
    def _parse_float(text: str) -> float:
        if not text or not text.strip():
            raise ValueError("Empty numeric response.")

        stripped = text.strip()
        try:
            return float(stripped)
        except ValueError:
            parts = stripped.rsplit(" ", 1)
            if len(parts) == 2:
                return float(parts[1].strip())
            raise ValueError(f"Cannot parse numeric response: {text}")

    @classmethod
    def _validate_voltage(cls, volts: float) -> None:
        if volts < 0 or volts > cls.MAX_VOLTAGE:
            raise ValueError(f"Voltage must be in range 0..{cls.MAX_VOLTAGE} V.")

    @classmethod
    def _validate_current(cls, amps: float) -> None:
        if amps < 0 or amps > cls.MAX_CURRENT:
            raise ValueError(f"Current must be in range 0..{cls.MAX_CURRENT} A.")

    @classmethod
    def _clamp_current_by_power(cls, volts: float, amps: float) -> float:
        if volts <= 0:
            return amps

        max_allowed = min(cls.MAX_POWER / volts, cls.MAX_CURRENT)
        return min(amps, max_allowed)

    def write(self, command: str) -> None:
        if not command or not command.strip():
            raise ValueError("Command must not be empty.")

        self._ensure_connected()

        with self._lock:
            if self._commands_since_query >= self.MAX_COMMANDS_BEFORE_QUERY:
                self.query("SYST:ERR?")

            self._send_line(command.strip())
            self._commands_since_query += 1

    def query(self, command: str) -> str:
        if not command or not command.strip():
            raise ValueError("Query must not be empty.")

        self._ensure_connected()

        with self._lock:
            self._send_line(command.strip())
            response = self._read_line()
            self._commands_since_query = 0
            return response

    def _send_line(self, command: str) -> None:
        assert self._socket is not None
        self._socket.sendall((command + "\n").encode("ascii"))

    def _read_line(self) -> str:
        assert self._reader is not None
        line = self._reader.readline()
        if line == "":
            raise RuntimeError("Socket closed by remote host.")
        return line.strip()

    def clear_status(self) -> None:
        self.write("*CLS")

    def get_idn(self) -> str:
        return self.query("*IDN?")    

    def read_system_error(self) -> str:
        return self.query("SYST:ERR?")

    def throw_if_system_error(self) -> None:
        error = self.read_system_error()
        normalized = error.lower()
        if error == "0" or normalized.startswith("0,") or "no error" in normalized:
            return
        raise RuntimeError(f"Power supply error: {error}")

    def set_voltage(self, volts: float) -> None:
        self._validate_voltage(volts)
        self.write(f"VOLT {self._format_number(volts)}")

    def get_voltage_setting(self) -> float:
        return self._parse_float(self.query("VOLT?"))

    def set_current(self, amps: float) -> None:
        self._validate_current(amps)
        self.write(f"CURR {self._format_number(amps)}")

    def get_current_setting(self) -> float:
        return self._parse_float(self.query("CURR?"))

    def set_output(self, on: bool) -> None:
        self.write(f"OUTP:STAT {'ON' if on else 'OFF'}")

    def get_output(self) -> bool:
        value = self.query("OUTP:STAT?").strip()
        return value == "1" or value.upper() == "ON"

    def measure_voltage(self) -> float:
        return self._parse_float(self.query("MEAS:VOLT?"))

    def measure_current(self) -> float:
        return self._parse_float(self.query("MEAS:CURR?"))

    def read_mode(self) -> str:
        return self.query("SOUR:MOD?").strip()

    def apply(self, volts: float, amps: float, output_on: bool, clamp_to_power: bool = True) -> None:
        self._validate_voltage(volts)
        self._validate_current(amps)

        if clamp_to_power:
            amps = self._clamp_current_by_power(volts, amps)

        self.set_voltage(volts)
        self.set_current(amps)
        self.set_output(output_on)

    def safe_off(self) -> None:
        self.set_output(False)
        self.set_voltage(0.0)
        self.set_current(0.0)

    def ramp_voltage(self, target_volts: float, step_volts: float, delay_ms: int) -> None:
        self._validate_voltage(target_volts)
        if step_volts <= 0:
            raise ValueError("step_volts must be greater than 0.")
        if delay_ms < 0:
            raise ValueError("delay_ms must be 0 or greater.")

        current = self.get_voltage_setting()
        direction = 1.0 if target_volts >= current else -1.0
        step = abs(step_volts) * direction

        while True:
            next_value = current + step
            if (direction > 0 and next_value >= target_volts) or (
                direction < 0 and next_value <= target_volts
            ):
                self.set_voltage(target_volts)
                break

            self.set_voltage(next_value)
            current = next_value

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    def read_status(self) -> GenesysStatus:
        return GenesysStatus(
            voltage_set=self.get_voltage_setting(),
            current_set=self.get_current_setting(),
            voltage_measured=self.measure_voltage(),
            current_measured=self.measure_current(),
            output_on=self.get_output(),
            mode=self.read_mode(),
            last_error=self.read_system_error(),
        )
