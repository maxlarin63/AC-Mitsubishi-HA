"""Sensor platform for AC Mitsubishi."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MitsubishiACCoordinator


def _drive_mode_label(raw: int | None) -> str | None:
    """Return a human-friendly label for the A1M Drive Mode register (ATA §11.1)."""
    if raw is None:
        return None
    return {
        1: "heat",
        2: "dry",
        3: "cool",
        7: "fan",
        8: "auto",
        9: "i-see heat",
        10: "i-see dry",
        11: "i-see cool",
    }.get(raw, f"unknown ({raw})")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities for this config entry."""
    coordinator: MitsubishiACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MitsubishiACDriveModeSensor(coordinator, entry)])


class MitsubishiACDriveModeSensor(
    CoordinatorEntity[MitsubishiACCoordinator], SensorEntity
):
    """Drive mode status, including i-see modes 9/10/11 (read-only on A1M)."""

    _attr_has_entity_name = True
    _attr_translation_key = "drive_mode"
    _attr_icon = "mdi:information-outline"

    def __init__(
        self,
        coordinator: MitsubishiACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        host = entry.data[CONF_HOST]

        # Separate "status" child device linked to the main AC device.
        self._attr_unique_id = f"{entry.entry_id}_drive_mode"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry.entry_id}_status")},
            "name": f"AC Mitsubishi Status ({host})",
            "via_device": (DOMAIN, entry.entry_id),
            "manufacturer": "Mitsubishi Electric",
            "model": "MelcoBEMS MINI (A1M)",
            "configuration_url": f"http://{host}",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def native_value(self) -> str | None:
        state = self.coordinator.data
        if state is None:
            return None
        return _drive_mode_label(state.mode)

