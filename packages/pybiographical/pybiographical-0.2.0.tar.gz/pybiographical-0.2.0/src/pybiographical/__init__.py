"""
PyBiographical - Python library for biographical data management.

Utilities for managing person metadata, location data, and biographical information.
"""

__version__ = "0.2.0"

from .ramdisk import RAMDisk, RAMDiskContext, get_ramdisk_stats, log_ramdisk_info

__all__ = [
    # RAMDisk utilities
    "RAMDisk",
    "RAMDiskContext",
    "get_ramdisk_stats",
    "log_ramdisk_info",
]
