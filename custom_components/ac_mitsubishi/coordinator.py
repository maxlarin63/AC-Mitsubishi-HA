"""
DataUpdateCoordinator for AC Mitsubishi.

Polls all six Modbus registers in a single TCP session every
DEFAULT_SCAN_INTERVAL seconds and exposes the results as a typed dataclass.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FC_READ_HOLDING,
    FC_READ_INPUT,
    REG_FAN,
    REG_MODE,
    REG_POWER,
    REG_ROOM_TEMP,
    REG_SETPOINT,
    REG_VANE,
)
from .modbus import ModbusRTUClient

_LOGGER = logging.getLogger(__name__)


@dataclass
class ACState:
    """Snapshot of all AC registers after a single poll cycle."""

    power: Optional[int]           # 0 = off, 1 = on
    mode: Optional[int]            # raw mode register value
    setpoint_raw: Optional[int]    # setpoint * 10  (e.g. 210 → 21.0 °C)
    fan: Optional[int]             # raw fan register value
    vane: Optional[int]            # raw vane register value
    room_temp_raw: Optional[int]   # room temp * 10

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def setpoint(self) -> Optional[float]:
        return self.setpoint_raw / 10.0 if self.setpoint_raw is not None else None

    @property
    def room_temp(self) -> Optional[float]:
        return self.room_temp_raw / 10.0 if self.room_temp_raw is not None else None

    @property
    def is_on(self) -> bool:
        return self.power == 1


class MitsubishiACCoordinator(DataUpdateCoordinator[ACState]):
    """Polls the AC unit and distributes state to all platform entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.host: str = entry.data[CONF_HOST]
        self.port: int = entry.data[CONF_PORT]
        self.entry = entry

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.host}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> ACState:
        """
        Open one TCP connection, read all registers sequentially, close.

        Raises UpdateFailed on connection error so HA marks the entity
        as unavailable rather than crashing.
        """
        client = ModbusRTUClient(self.host, self.port)
        if not await client.connect():
            raise UpdateFailed(
                f"Cannot connect to AC unit at {self.host}:{self.port}"
            )

        try:
            power        = await client.read_register(FC_READ_HOLDING, REG_POWER)
            mode         = await client.read_register(FC_READ_HOLDING, REG_MODE)
            setpoint_raw = await client.read_register(FC_READ_HOLDING, REG_SETPOINT)
            fan          = await client.read_register(FC_READ_HOLDING, REG_FAN)
            vane         = await client.read_register(FC_READ_HOLDING, REG_VANE)
            room_raw     = await client.read_register(FC_READ_INPUT,   REG_ROOM_TEMP)
        finally:
            await client.close()

        state = ACState(
            power=power,
            mode=mode,
            setpoint_raw=setpoint_raw,
            fan=fan,
            vane=vane,
            room_temp_raw=room_raw,
        )
        _LOGGER.debug("Polled state: %s", state)
        return state

    # ── Write helpers (used by the climate entity) ────────────────────────────

    async def async_write_register(self, reg: int, value: int) -> bool:
        """
        Write a single register and immediately reschedule a coordinator
        refresh so the UI reflects the new state quickly.
        """
        client = ModbusRTUClient(self.host, self.port)
        if not await client.connect():
            _LOGGER.error("Write failed: cannot connect to %s:%s", self.host, self.port)
            return False
        try:
            success = await client.write_register(reg, value)
        finally:
            await client.close()

        if success:
            # Trigger a fresh poll so entities reflect the written value
            await self.async_request_refresh()
        return success
