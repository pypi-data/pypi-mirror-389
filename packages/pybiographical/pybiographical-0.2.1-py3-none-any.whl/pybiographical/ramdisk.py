"""
RAM Disk utilities for performance optimization.

Provides utilities for using RAM disk (/Volumes/RAMDisk) to speed up I/O-heavy
operations, especially when working with Google Drive-synced data.

Usage:
    from pybiographical import RAMDiskContext
    
    with RAMDiskContext(copy_back_to=Path("output")) as ramdisk:
        if ramdisk.available:
            # Use ramdisk.temp_dir for temporary operations
            output_file = ramdisk.temp_dir / "output.json"
            # ... process ...
            # Files are automatically copied back on context exit
"""

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Optional, List
from contextlib import contextmanager


class RAMDisk:
    """Manages RAM disk usage for performance optimization."""
    
    RAMDISK_PATH = Path('/Volumes/RAMDisk')
    RAMDISK_SCRIPT = Path.home() / 'bin' / 'ramdisk.sh'
    
    def __init__(self, auto_create: bool = False):
        """Initialize RAM disk manager.
        
        Args:
            auto_create: If True, attempt to create RAM disk if not found
        """
        self.auto_create = auto_create
        self._available = None
    
    @property
    def available(self) -> bool:
        """Check if RAM disk is available."""
        if self._available is None:
            self._available = self.RAMDISK_PATH.exists()
            
            if not self._available and self.auto_create:
                self._available = self._try_create()
        
        return self._available
    
    def _try_create(self) -> bool:
        """Attempt to create RAM disk using ~/bin/ramdisk.sh."""
        if not self.RAMDISK_SCRIPT.exists():
            logging.warning(f"RAM disk creation script not found: {self.RAMDISK_SCRIPT}")
            return False
        
        try:
            logging.info(f"Creating RAM disk at {self.RAMDISK_PATH}...")
            os.system(f"{self.RAMDISK_SCRIPT} > /dev/null 2>&1")
            
            # Check if creation succeeded
            if self.RAMDISK_PATH.exists():
                logging.info("RAM disk created successfully")
                return True
            else:
                logging.warning("RAM disk creation failed")
                return False
        except Exception as e:
            logging.warning(f"Error creating RAM disk: {e}")
            return False
    
    def create_temp_dir(self, prefix: str = "pycommon") -> Path:
        """Create a temporary directory on RAM disk.
        
        Args:
            prefix: Prefix for temp directory name
            
        Returns:
            Path to temporary directory
            
        Raises:
            RuntimeError: If RAM disk is not available
        """
        if not self.available:
            raise RuntimeError("RAM disk not available")
        
        temp_dir = self.RAMDISK_PATH / f"{prefix}_{os.getpid()}_{int(time.time())}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Created RAM disk temp directory: {temp_dir}")
        
        return temp_dir
    
    def stage_files(self, files: List[Path], dest_dir: Path) -> List[Path]:
        """Copy files to RAM disk for faster processing.
        
        Args:
            files: List of source file paths
            dest_dir: Destination directory on RAM disk
            
        Returns:
            List of staged file paths on RAM disk
        """
        if not self.available:
            return files  # Return originals if RAM disk unavailable
        
        staged_files = []
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for source_file in files:
            if not source_file.exists():
                logging.warning(f"Source file not found: {source_file}")
                continue
            
            dest_file = dest_dir / source_file.name
            shutil.copy2(source_file, dest_file)
            staged_files.append(dest_file)
        
        logging.info(f"Staged {len(staged_files)} files to RAM disk")
        return staged_files
    
    def copy_back(self, source_dir: Path, dest_dir: Path, 
                  pattern: str = "*", clean_source: bool = True) -> int:
        """Copy files from RAM disk back to final destination.
        
        Args:
            source_dir: Source directory on RAM disk
            dest_dir: Final destination directory
            pattern: File pattern to match (default: all files)
            clean_source: If True, remove source directory after copy
            
        Returns:
            Number of files copied
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        files_copied = 0
        for source_file in source_dir.glob(pattern):
            if source_file.is_file():
                dest_file = dest_dir / source_file.name
                shutil.copy2(source_file, dest_file)
                files_copied += 1
        
        if clean_source and source_dir.exists():
            shutil.rmtree(source_dir)
            logging.debug(f"Cleaned up RAM disk directory: {source_dir}")
        
        logging.info(f"Copied {files_copied} files from RAM disk to {dest_dir}")
        return files_copied


@contextmanager
def RAMDiskContext(prefix: str = "pycommon", auto_create: bool = False,
                   copy_back_to: Optional[Path] = None, pattern: str = "*"):
    """Context manager for RAM disk operations.
    
    Args:
        prefix: Prefix for temp directory name
        auto_create: Attempt to create RAM disk if not found
        copy_back_to: If provided, copy files back to this directory on exit
        pattern: File pattern for copy back operation
        
    Yields:
        RAMDisk object with temp_dir attribute
        
    Example:
        with RAMDiskContext(copy_back_to=Path("output")) as ramdisk:
            if ramdisk.available:
                # Write to ramdisk.temp_dir
                output_file = ramdisk.temp_dir / "results.json"
                # Files automatically copied to "output/" on exit
    """
    ramdisk = RAMDisk(auto_create=auto_create)
    
    if ramdisk.available:
        temp_dir = ramdisk.create_temp_dir(prefix)
        ramdisk.temp_dir = temp_dir
        logging.info(f"Using RAM disk at {temp_dir}")
    else:
        ramdisk.temp_dir = None
        logging.info("RAM disk not available, using regular filesystem")
    
    try:
        yield ramdisk
    finally:
        # Copy back and cleanup if requested
        if ramdisk.available and copy_back_to and ramdisk.temp_dir:
            ramdisk.copy_back(ramdisk.temp_dir, copy_back_to, pattern=pattern)
        elif ramdisk.available and ramdisk.temp_dir:
            # Cleanup without copy back
            if ramdisk.temp_dir.exists():
                shutil.rmtree(ramdisk.temp_dir)
                logging.debug(f"Cleaned up RAM disk directory: {ramdisk.temp_dir}")


def get_ramdisk_stats() -> dict:
    """Get RAM disk statistics.
    
    Returns:
        Dictionary with available, path, and size info
    """
    stats = {
        'available': RAMDisk.RAMDISK_PATH.exists(),
        'path': str(RAMDisk.RAMDISK_PATH),
        'total_space_gb': None,
        'used_space_gb': None,
        'free_space_gb': None
    }
    
    if stats['available']:
        try:
            stat = os.statvfs(RAMDisk.RAMDISK_PATH)
            total = (stat.f_blocks * stat.f_frsize) / (1024**3)
            free = (stat.f_bavail * stat.f_frsize) / (1024**3)
            used = total - free
            
            stats['total_space_gb'] = round(total, 2)
            stats['used_space_gb'] = round(used, 2)
            stats['free_space_gb'] = round(free, 2)
        except Exception as e:
            logging.warning(f"Error getting RAM disk stats: {e}")
    
    return stats


def log_ramdisk_info():
    """Log RAM disk information to logger."""
    stats = get_ramdisk_stats()
    
    if stats['available']:
        logging.info(f"RAM disk available at {stats['path']}")
        if stats['total_space_gb']:
            logging.info(f"  Total: {stats['total_space_gb']} GB, "
                        f"Used: {stats['used_space_gb']} GB, "
                        f"Free: {stats['free_space_gb']} GB")
    else:
        logging.info(f"RAM disk not available at {stats['path']}")
        logging.info(f"  To create: {RAMDisk.RAMDISK_SCRIPT}")
