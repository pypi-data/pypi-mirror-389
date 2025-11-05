"""Alarm processor for handling dynamic alarm allocation with hash lookup."""

import logging
from typing import Callable, Dict

from ..constants import SEVERITY_MIN, SEVERITY_MAX
from ..utils import parse_int


def crc16(data: str) -> int:
    """
    Calculate CRC16 hash of a string.
    
    Args:
        data: String to hash
        
    Returns:
        16-bit CRC hash value (0-65535)
    """
    crc = 0xFFFF
    for byte in data.encode('utf-8'):
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


class AlarmProcessor:
    """Processes alarm data with dynamic slot allocation."""
    
    def __init__(
        self,
        write_uint16: Callable[[int, int], None],
        alarm_region_start: int,
        alarm_region_size: int,
        shared_hash_start: int,
    ):
        """
        Initialize alarm processor.
        
        Args:
            write_uint16: Function to write unsigned 16-bit value to register
            alarm_region_start: Start address of alarm region (relative to cubicle base)
            alarm_region_size: Total number of alarm slots (100)
            shared_hash_start: Absolute address of shared hash lookup table
        """
        self.write_uint16 = write_uint16
        self.alarm_region_start = alarm_region_start
        self.alarm_region_size = alarm_region_size
        self.shared_hash_start = shared_hash_start
        
        # Flat alarm key → slot mapping (no categories/bands)
        self.alarm_key_to_slot: Dict[str, int] = {}
        self.next_slot = 0
    
    def ensure_alarm_slot(self, key: str) -> int:
        """
        Allocate a flat slot for an alarm key (no category grouping).
        
        Args:
            key: Alarm identifier string
            
        Returns:
            Slot number (0-99) or None if region is full
        """
        if key in self.alarm_key_to_slot:
            return self.alarm_key_to_slot[key]
        
        if self.next_slot >= self.alarm_region_size:
            logging.warning(
                "Alarm region full (%d slots). Alarm '%s' ignored.",
                self.alarm_region_size, key
            )
            return None
        
        slot = self.next_slot
        self.next_slot += 1
        self.alarm_key_to_slot[key] = slot
        
        # Write hash to SHARED lookup table
        alarm_hash = crc16(key)
        hash_table_addr = self.shared_hash_start + slot
        self.write_uint16(hash_table_addr, alarm_hash)
        
        logging.info(
            "Assigned slot %d for alarm '%s' (shared_hash_addr=%d, hash=0x%04X)",
            slot, key, hash_table_addr, alarm_hash
        )
        return slot
    
    def process_alarms(self, idx: int, block_size: int, cubicle_base_offset: int, alarms: dict):
        """
        Process alarm data for a cubicle.
        
        Args:
            idx: Cubicle index
            block_size: Size of register block per cubicle
            cubicle_base_offset: Offset where cubicle data starts (after hash table)
            alarms: Alarms dictionary from MQTT payload (nested by category)
        """
        if not isinstance(alarms, dict):
            return
        
        base = cubicle_base_offset + (idx * block_size)
        
        for category, alarm_data in alarms.items():
            if not isinstance(alarm_data, dict):
                continue
            
            for key, severity_raw in alarm_data.items():
                key = str(key)
                if len(key) > 50:
                    logging.warning("Alarm key too long (>50 chars): %r", key)
                    continue
                
                slot = self.ensure_alarm_slot(key)
                if slot is None:
                    continue
                
                severity = parse_int(severity_raw)
                if severity is None:
                    logging.warning(
                        "Non-numeric severity for %s: %r",
                        key, severity_raw
                    )
                    continue
                
                # Clamp severity to valid range
                severity = max(SEVERITY_MIN, min(SEVERITY_MAX, severity))
                
                # Calculate register address (flat slot, no band calculation)
                addr = base + self.alarm_region_start + slot
                
                self.write_uint16(addr, severity)
