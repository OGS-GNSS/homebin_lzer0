"""Shared configuration loader for lzer0 Python scripts."""

from __future__ import annotations

import os
import re
from pathlib import Path


def _expand(value: str, values: dict[str, str]) -> str:
    pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return values.get(key, os.environ.get(key, ""))

    previous = None
    expanded = value
    while previous != expanded:
        previous = expanded
        expanded = pattern.sub(replace, expanded)
    return expanded


def load_config(script_file: str | None = None) -> dict[str, str]:
    script_dir = Path(script_file).resolve().parent if script_file else Path(__file__).resolve().parent
    env_file = Path(os.environ.get("LZERO_ENV_FILE", Path.home() / "cfg" / "lzer0.env"))
    if not env_file.is_file():
        local_env_file = script_dir / "lzer0.env"
        env_file = local_env_file if local_env_file.is_file() else env_file

    values = dict(os.environ)
    if env_file.is_file():
        for raw_line in env_file.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            values[key] = _expand(value, values)

    values.setdefault("LZERO_HOME", "/home/lzer0")
    values.setdefault("LZERO_BIN_DIR", f"{values['LZERO_HOME']}/bin")
    values.setdefault("LZERO_CONFIG_DIR", f"{values['LZERO_HOME']}/cfg")
    values.setdefault("LZERO_LOG_DIR", f"{values['LZERO_HOME']}/log")
    values.setdefault("LZERO_VAR_DIR", f"{values['LZERO_HOME']}/var")
    values.setdefault("LZERO_TMP_DIR", f"{values['LZERO_HOME']}/tmp/tmp.lzer0")
    values.setdefault("LZERO_STORAGE_MOUNT", "/mnt/hd")
    values.setdefault("LZERO_GNSS_DIR", f"{values['LZERO_STORAGE_MOUNT']}/gnss")
    values.setdefault("LZERO_SITE_CONFIG", f"{values['LZERO_CONFIG_DIR']}/sites.cfg")
    values.setdefault("LZERO_RTKRCV_CONFIG", f"{values['LZERO_CONFIG_DIR']}/rtkrcv.curr.conf")
    values.setdefault("LZERO_RNX2RTKP_CONFIG", f"{values['LZERO_CONFIG_DIR']}/rnx2rtkp.curr.conf")
    values.setdefault("LZERO_STATION_POS_FILE", f"{values['LZERO_HOME']}/tab/station.pos")
    values.setdefault("LZERO_RTKRCV_TELNET_PORT", "2950")
    values.setdefault("LZERO_RAW_TCP_PORT", "2222")
    values.setdefault("LZERO_RTCM_TCP_PORT", "3333")
    values.setdefault("LZERO_POS_TCP_PORT", "5754")
    values.setdefault("LZERO_SERIAL_USB_DEVICE", "ttyACM0")
    values.setdefault("LZERO_SERIAL_UART_DEVICE", "ttyS0")
    values.setdefault("LZERO_STORAGE_USE_LIMIT", "90")
    values.setdefault("LZERO_CLEANUP_MIN_FREE_GB", "15")
    return values
