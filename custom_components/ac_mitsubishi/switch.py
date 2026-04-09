"""Switch platform: AC unit power on/off."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_POWER
from .coordinator import MitsubishiACCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities for this config entry."""
    coordinator: MitsubishiACCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MitsubishiACPowerSwitch(coordinator, entry)])


class MitsubishiACPowerSwitch(
    CoordinatorEntity[MitsubishiACCoordinator], SwitchEntity
):
    """Switch to turn the AC unit power on or off (Modbus REG_POWER)."""

    _attr_has_entity_name = True
    _attr_translation_key = "power"

    def __init__(
        self,
        coordinator: MitsubishiACCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        host = entry.data[CONF_HOST]

        self._attr_unique_id = f"{entry.entry_id}_power"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Mitsubishi Electric",
            "model": "Modbus RTU over TCP",
            "configuration_url": f"http://{host}",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def is_on(self) -> bool | None:
        state = self.coordinator.data
        if state is None:
            return None
        return state.is_on

    @property
    def icon(self) -> str:
        return "mdi:air-conditioner"

    async def async_turn_on(self) -> None:
        await self.coordinator.async_write_register(REG_POWER, 1)

    async def async_turn_off(self) -> None:
        await self.coordinator.async_write_register(REG_POWER, 0)
