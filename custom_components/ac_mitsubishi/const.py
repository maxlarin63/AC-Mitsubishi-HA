"""Constants for the AC Mitsubishi (Modbus RTU over TCP) integration."""

from homeassistant.components.climate import HVACMode

DOMAIN = "ac_mitsubishi"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"

# Defaults
DEFAULT_PORT = 4001
DEFAULT_SCAN_INTERVAL = 60  # seconds

# Modbus slave / unit ID
MODBUS_SLAVE = 0x01

# Function codes
FC_READ_HOLDING = 0x03   # Read Holding Registers (mode, setpoint, fan, vane, power)
FC_READ_INPUT   = 0x04   # Read Input Registers  (room temperature)
FC_WRITE_SINGLE = 0x06   # Write Single Register

# Register addresses
REG_MODE      = 0x0000   # FC03 – HVAC operating mode
REG_SETPOINT  = 0x0001   # FC03 – Target temperature (raw / 10 = °C)
REG_FAN       = 0x0002   # FC03 – Fan speed
REG_VANE      = 0x0003   # FC03 – Vane / swing position
REG_POWER     = 0x0007   # FC03 – Power on/off
REG_ROOM_TEMP = 0x0000   # FC04 – Current room temperature (raw / 10 = °C)

# ── HVAC mode map  (HA mode → register value) ─────────────────────────────────
HVAC_MODE_TO_REG: dict[HVACMode, int] = {
    HVACMode.HEAT:     1,
    HVACMode.DRY:      2,
    HVACMode.COOL:     3,
    HVACMode.FAN_ONLY: 7,
    HVACMode.AUTO:     8,
}
REG_TO_HVAC_MODE: dict[int, HVACMode] = {v: k for k, v in HVAC_MODE_TO_REG.items()}

SUPPORTED_HVAC_MODES: list[HVACMode] = [
    HVACMode.OFF,
    HVACMode.HEAT,
    HVACMode.COOL,
    HVACMode.DRY,
    HVACMode.FAN_ONLY,
    HVACMode.AUTO,
]

# ── Fan speed map  (HA fan mode → register value) ─────────────────────────────
FAN_MODE_AUTO        = "auto"
FAN_MODE_QUIET       = "quiet"
FAN_MODE_WEAK        = "weak"
FAN_MODE_STRONG      = "strong"
FAN_MODE_VERY_STRONG = "very_strong"

FAN_MODE_TO_REG: dict[str, int] = {
    FAN_MODE_AUTO:        0,
    FAN_MODE_QUIET:       2,
    FAN_MODE_WEAK:        3,
    FAN_MODE_STRONG:      5,
    FAN_MODE_VERY_STRONG: 6,
}
REG_TO_FAN_MODE: dict[int, str] = {v: k for k, v in FAN_MODE_TO_REG.items()}

SUPPORTED_FAN_MODES: list[str] = list(FAN_MODE_TO_REG)

# ── Vane / swing map  (HA swing mode → register value) ────────────────────────
SWING_AUTO  = "auto"
SWING_POS_1 = "position_1"
SWING_POS_2 = "position_2"
SWING_POS_3 = "position_3"
SWING_POS_4 = "position_4"
SWING_POS_5 = "position_5"
SWING_SWING = "swing"

SWING_MODE_TO_REG: dict[str, int] = {
    SWING_AUTO:  0,
    SWING_POS_1: 1,
    SWING_POS_2: 2,
    SWING_POS_3: 3,
    SWING_POS_4: 4,
    SWING_POS_5: 5,
    SWING_SWING: 7,
}
REG_TO_SWING_MODE: dict[int, str] = {v: k for k, v in SWING_MODE_TO_REG.items()}

SUPPORTED_SWING_MODES: list[str] = list(SWING_MODE_TO_REG)

# Temperature limits (°C)
MIN_TEMP = 16.0
MAX_TEMP = 31.0
TEMP_STEP = 0.5
