"""Tests for the ClimateEntity state mapping (climate.py)."""

from __future__ import annotations

from homeassistant.components.climate import HVACMode

from custom_components.ac_mitsubishi.const import (
    FAN_MODE_TO_REG,
    HVAC_MODE_TO_REG,
    SWING_MODE_TO_REG,
)
from custom_components.ac_mitsubishi.coordinator import ACState


def make_state(**kwargs) -> ACState:
    defaults = {"power": 1, "mode": 3, "setpoint_raw": 210, "fan": 0, "vane": 0, "room_temp_raw": 235}
    defaults.update(kwargs)
    return ACState(**defaults)


def test_acstate_temperature_conversion():
    state = make_state(setpoint_raw=215, room_temp_raw=242)
    assert state.setpoint == 21.5
    assert state.room_temp == 24.2


def test_acstate_is_on():
    assert make_state(power=1).is_on is True
    assert make_state(power=0).is_on is False


def test_hvac_mode_map_covers_all_write_modes():
    """Every non-OFF HVACMode that HA can send must be in the register map."""
    for mode in [HVACMode.HEAT, HVACMode.COOL, HVACMode.DRY, HVACMode.FAN_ONLY, HVACMode.AUTO]:
        assert mode in HVAC_MODE_TO_REG, f"{mode} missing from HVAC_MODE_TO_REG"


def test_fan_mode_map_round_trip():
    from custom_components.ac_mitsubishi.const import REG_TO_FAN_MODE
    for name, reg in FAN_MODE_TO_REG.items():
        assert REG_TO_FAN_MODE[reg] == name


def test_swing_mode_map_round_trip():
    from custom_components.ac_mitsubishi.const import REG_TO_SWING_MODE
    for name, reg in SWING_MODE_TO_REG.items():
        assert REG_TO_SWING_MODE[reg] == name
