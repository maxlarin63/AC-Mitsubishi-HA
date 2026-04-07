"""Tests for the raw Modbus RTU framing layer (modbus.py)."""

from __future__ import annotations

from custom_components.ac_mitsubishi.modbus import _build_read_frame, _build_write_frame, _crc16


def test_crc16_known_value():
    """CRC-16 of a known Modbus frame must match expected bytes."""
    # FC03, slave 1, read 1 register from address 0x0001
    frame_body = bytes([0x01, 0x03, 0x00, 0x01, 0x00, 0x01])
    crc = _crc16(frame_body)
    assert crc == bytes([0xD5, 0xCA])


def test_build_read_frame_length():
    frame = _build_read_frame(slave=1, func=0x03, start=0x0001, count=1)
    assert len(frame) == 8  # 6 bytes body + 2 bytes CRC


def test_build_write_frame_length():
    frame = _build_write_frame(slave=1, reg=0x0001, value=210)
    assert len(frame) == 8


def test_build_read_frame_bytes():
    frame = _build_read_frame(slave=1, func=0x03, start=0x0000, count=1)
    assert frame[0] == 0x01   # slave
    assert frame[1] == 0x03   # FC03
    assert frame[2] == 0x00   # address high
    assert frame[3] == 0x00   # address low
    assert frame[4] == 0x00   # count high
    assert frame[5] == 0x01   # count low
