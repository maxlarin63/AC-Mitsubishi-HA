"""Shared pytest fixtures for AC Mitsubishi tests."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_modbus_client():
    """Return a mock ModbusRTUClient with sensible default register values."""
    with patch(
        "custom_components.ac_mitsubishi.coordinator.ModbusRTUClient"
    ) as mock_cls:
        client = AsyncMock()
        client.connect = AsyncMock(return_value=True)
        client.close = AsyncMock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)

        # Default register values  (power=on, mode=cool, setpoint=21°C, etc.)
        client.read_register = AsyncMock(
            side_effect=lambda func, reg: {
                (0x03, 0x0007): 1,    # power ON
                (0x03, 0x0000): 3,    # mode: cool
                (0x03, 0x0001): 210,  # setpoint: 21.0 °C
                (0x03, 0x0002): 0,    # fan: auto
                (0x03, 0x0003): 0,    # vane: auto
                (0x04, 0x0000): 235,  # room temp: 23.5 °C
            }.get((func, reg))
        )
        client.write_register = AsyncMock(return_value=True)

        mock_cls.return_value = client
        yield client
