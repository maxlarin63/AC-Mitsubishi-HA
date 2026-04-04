"""
Async Modbus RTU over TCP client.

The Mitsubishi AC adapter speaks plain Modbus RTU framing (slave address +
function code + data + CRC-16) tunnelled over a raw TCP socket – not the
standard Modbus TCP/IP variant that prepends a 6-byte MBAP header.
This module replicates that behaviour using asyncio streams.
"""

from __future__ import annotations

import asyncio
import logging
import struct
from typing import Optional

_LOGGER = logging.getLogger(__name__)

TIMEOUT = 5.0  # seconds per operation


# ── CRC-16 (Modbus) ───────────────────────────────────────────────────────────

def _crc16(data: bytes) -> bytes:
    """Return the 2-byte Modbus CRC-16 (little-endian)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack("<H", crc)


# ── Frame builders ────────────────────────────────────────────────────────────

def _build_read_frame(slave: int, func: int, start: int, count: int) -> bytes:
    """Build a Modbus RTU read request frame."""
    body = struct.pack(">BBHH", slave, func, start, count)
    return body + _crc16(body)


def _build_write_frame(slave: int, reg: int, value: int) -> bytes:
    """Build a Modbus RTU FC06 (Write Single Register) frame."""
    body = struct.pack(">BBHH", slave, 0x06, reg, value)
    return body + _crc16(body)


# ── Client ────────────────────────────────────────────────────────────────────

class ModbusRTUClient:
    """
    Async Modbus RTU over TCP client.

    A single TCP connection is opened per *session* (e.g. one full poll
    cycle) and closed afterwards.  Each read/write within that session
    reuses the open socket, mirroring the original FIBARO QA behaviour.
    """

    def __init__(self, host: str, port: int, slave: int = 0x01) -> None:
        self.host = host
        self.port = port
        self.slave = slave
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    # ── Connection management ─────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Open the TCP connection.  Returns True on success."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=TIMEOUT,
            )
            _LOGGER.debug("Connected to %s:%s", self.host, self.port)
            return True
        except (OSError, asyncio.TimeoutError) as exc:
            _LOGGER.error("Connection to %s:%s failed: %s", self.host, self.port, exc)
            return False

    async def close(self) -> None:
        """Close the TCP connection gracefully."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
            finally:
                self._reader = None
                self._writer = None
        _LOGGER.debug("Disconnected from %s:%s", self.host, self.port)

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    # ── Modbus operations ─────────────────────────────────────────────────────

    async def read_register(self, func: int, reg: int) -> Optional[int]:
        """
        Read a single register.

        Args:
            func: Modbus function code (0x03 = holding, 0x04 = input).
            reg:  Register address.

        Returns:
            Integer register value, or None on error.
        """
        if not self.connected:
            _LOGGER.error("read_register called while not connected")
            return None
        try:
            frame = _build_read_frame(self.slave, func, reg, 1)
            _LOGGER.debug("TX: %s", frame.hex(" ").upper())
            self._writer.write(frame)
            await self._writer.drain()

            data = await asyncio.wait_for(self._reader.read(256), timeout=TIMEOUT)
            _LOGGER.debug("RX: %s", data.hex(" ").upper())

            if len(data) >= 5:
                return (data[3] << 8) | data[4]

            _LOGGER.warning("Short response for FC%02X reg %04X: %s", func, reg, data.hex())
            return None

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout reading FC%02X reg %04X", func, reg)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("Error reading FC%02X reg %04X: %s", func, reg, exc)
        return None

    async def write_register(self, reg: int, value: int) -> bool:
        """
        Write a single holding register (FC06).

        Returns True on success.
        """
        if not self.connected:
            _LOGGER.error("write_register called while not connected")
            return False
        try:
            frame = _build_write_frame(self.slave, reg, value)
            _LOGGER.debug("TX: %s", frame.hex(" ").upper())
            self._writer.write(frame)
            await self._writer.drain()

            data = await asyncio.wait_for(self._reader.read(256), timeout=TIMEOUT)
            _LOGGER.debug("RX: %s", data.hex(" ").upper())
            return True

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout writing reg %04X value %d", reg, value)
        except Exception as exc:  # noqa: BLE001
            _LOGGER.error("Error writing reg %04X value %d: %s", reg, value, exc)
        return False

    # ── Context manager support ───────────────────────────────────────────────

    async def __aenter__(self) -> "ModbusRTUClient":
        await self.connect()
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
