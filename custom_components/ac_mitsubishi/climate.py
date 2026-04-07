"""
Climate platform for AC Mitsubishi (Modbus RTU over TCP).

Maps all FIBARO QA capabilities to the standard HA ClimateEntity interface:
  - HVAC modes : off / heat / cool / dry / fan_only / auto
  - Fan modes  : auto / quiet / weak / strong / very_strong
  - Swing modes: auto / position_1 / position_2 / position_3 /
                 position_4 / position_5 / swing
  - Temperature: current room temp + settable target (16–31 °C, step 0.5)
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FAN_MODE_TO_REG,
    HVAC_MODE_TO_REG,
    MAX_TEMP,
    MIN_TEMP,
    REG_FAN,
    REG_MODE,
    REG_POWER,
    REG_SETPOINT,
    REG_TO_FAN_MODE,
    REG_TO_HVAC_MODE,
    REG_TO_SWING_MODE,
    REG_VANE,
    SUPPORTED_FAN_MODES,
    SUPPORTED_HVAC_MODES,
    SUPPORTED_SWING_MODES,
    SWING_MODE_TO_REG,
    TEMP_STEP,
)
from .coordinator import MitsubishiACCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Mitsubishi AC climate entity from a config entry."""
    coordinator: MitsubishiACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MitsubishiACClimate(coordinator, entry)])


class MitsubishiACClimate(CoordinatorEntity[MitsubishiACCoordinator], ClimateEntity):
    """
    Representation of the Mitsubishi AC as a Home Assistant Climate entity.

    State is driven by the coordinator (polled every 60 s).  Write operations
    send a single Modbus register write and immediately trigger a refresh.
    """

    _attr_has_entity_name = True
    _attr_name = None  # uses device name

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = SUPPORTED_HVAC_MODES
    _attr_fan_modes = SUPPORTED_FAN_MODES
    _attr_swing_modes = SUPPORTED_SWING_MODES
    _attr_min_temp = MIN_TEMP
    _attr_max_temp = MAX_TEMP
    _attr_target_temperature_step = TEMP_STEP
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
    )

    def __init__(
        self,
        coordinator: MitsubishiACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        host = entry.data[CONF_HOST]

        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"AC Mitsubishi ({host})",
            "manufacturer": "Mitsubishi Electric",
            "model": "Modbus RTU over TCP",
            "configuration_url": f"http://{host}",
        }

    # ── State properties (read from coordinator data) ─────────────────────────

    @property
    def available(self) -> bool:
        """Entity is unavailable when the last poll failed."""
        return self.coordinator.last_update_success

    @property
    def hvac_mode(self) -> HVACMode:
        state = self.coordinator.data
        if state is None or not state.is_on:
            return HVACMode.OFF
        return REG_TO_HVAC_MODE.get(state.mode, HVACMode.AUTO)

    @property
    def current_temperature(self) -> float | None:
        state = self.coordinator.data
        return state.room_temp if state else None

    @property
    def target_temperature(self) -> float | None:
        state = self.coordinator.data
        return state.setpoint if state else None

    @property
    def fan_mode(self) -> str | None:
        state = self.coordinator.data
        if state is None or state.fan is None:
            return None
        return REG_TO_FAN_MODE.get(state.fan)

    @property
    def swing_mode(self) -> str | None:
        state = self.coordinator.data
        if state is None or state.vane is None:
            return None
        return REG_TO_SWING_MODE.get(state.vane)

    # ── Service call handlers (write to device) ───────────────────────────────

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """
        Turn off, or switch to a new operating mode.

        Turning ON:  write power=1 first, then write mode register.
        Turning OFF: write power=0.
        """
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write_register(REG_POWER, 0)
            return

        # Ensure unit is powered on
        state = self.coordinator.data
        if state is None or not state.is_on:
            await self.coordinator.async_write_register(REG_POWER, 1)

        mode_value = HVAC_MODE_TO_REG.get(hvac_mode)
        if mode_value is None:
            _LOGGER.warning("Unsupported HVAC mode requested: %s", hvac_mode)
            return

        await self.coordinator.async_write_register(REG_MODE, mode_value)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature (resolution: 0.5 °C)."""
        temp: float | None = kwargs.get("temperature")
        if temp is None:
            return
        raw = round(temp * 10)  # e.g. 21.5 → 215
        await self.coordinator.async_write_register(REG_SETPOINT, raw)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set fan speed."""
        value = FAN_MODE_TO_REG.get(fan_mode)
        if value is None:
            _LOGGER.warning("Unsupported fan mode: %s", fan_mode)
            return
        await self.coordinator.async_write_register(REG_FAN, value)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set vane / swing position."""
        value = SWING_MODE_TO_REG.get(swing_mode)
        if value is None:
            _LOGGER.warning("Unsupported swing mode: %s", swing_mode)
            return
        await self.coordinator.async_write_register(REG_VANE, value)
