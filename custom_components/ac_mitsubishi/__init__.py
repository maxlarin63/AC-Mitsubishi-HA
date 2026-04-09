"""
AC Mitsubishi – Home Assistant custom integration.

Connects to a Mitsubishi Electric AC unit via a Modbus RTU over TCP
adapter (e.g. Elfin EW11, USR-TCP232, or similar RS-485→Ethernet bridge).

Setup:
  1. Copy this folder to <config>/custom_components/ac_mitsubishi/
  2. Restart Home Assistant.
  3. Go to Settings → Integrations → Add Integration → "AC Mitsubishi".
  4. Enter the adapter's IP address and port (default 4001).
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import MitsubishiACCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SWITCH, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AC Mitsubishi from a config entry."""
    # Keep config entry titles stable (no version / no IP), so entity_ids don't churn.
    if entry.title.startswith("AC Mitsubishi v"):
        hass.config_entries.async_update_entry(entry, title="AC Mitsubishi")

    coordinator = MitsubishiACCoordinator(hass, entry)

    # Do the first refresh; raises ConfigEntryNotReady on failure
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
