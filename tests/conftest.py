"""Shared pytest fixtures for AC Mitsubishi tests."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch

import pytest
import pytest_socket


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:  # noqa: ARG001
    """Silence noisy DEBUG/INFO loggers in test output.

    ``pytest-homeassistant-custom-component`` calls ``logging.basicConfig(level=INFO)`` at
    import time and, when invoked with ``-v``, bumps the root logger to ``DEBUG``. That
    floods the terminal with ``DEBUG:asyncio:Using proactor: IocpProactor`` (its autouse
    ``enable_event_loop_debug`` fixture flips ``loop.set_debug(True)`` for every test) and
    with the integration's own ``DEBUG`` / ``INFO`` chatter.

    ``trylast=True`` ensures this runs *after* the plugin's ``pytest_configure``, otherwise
    the plugin would re-raise the root logger to ``DEBUG`` on top of us.
    """
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("custom_components.ac_mitsubishi").setLevel(logging.WARNING)


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_fixture_setup(fixturedef, request):
    """Re-enable sockets before Home Assistant's event_loop fixture runs.

    pytest-homeassistant-custom-component calls pytest_socket.disable_socket() in
    pytest_runtest_setup; on Windows, ProactorEventLoop needs AF_INET socketpair()
    for its internal pipe (not covered by allow_unix_socket). Fixture setup runs
    after that hook, so we restore the real socket API immediately before the loop
    is created.
    """
    if fixturedef.argname == "event_loop":
        pytest_socket.enable_socket()
    yield


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
