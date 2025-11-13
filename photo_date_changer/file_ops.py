"""Filesystem helpers (gather files, get original time, update timestamps)."""
import os
from datetime import datetime
from typing import List
from .exif_utils import ExifHandler

class FileTimestampManager:
    """Filesystem helpers (gather files, get original time, update timestamp)."""

    @staticmethod
    def gather_files(folder: str, recursive: bool) -> List[str]:
        files = []
        if recursive:
            for root, _, filenames in os.walk(folder):
                for fn in filenames:
                    files.append(os.path.join(root, fn))
        else:
            for fn in os.listdir(folder):
                path = os.path.join(folder, fn)
                if os.path.isfile(path):
                    files.append(path)
        return files

    @staticmethod
    def get_original_time(file_path: str) -> datetime:
        lower = file_path.lower()
        if lower.endswith((".jpg", ".jpeg")):
            exif_dt = ExifHandler.get_exif_datetime(file_path)
            if exif_dt:
                return exif_dt
        return datetime.fromtimestamp(os.path.getmtime(file_path))

    @staticmethod
    def update_file_timestamp(file_path: str, dt: datetime, dry_run: bool=False, log_fn=print):
        if dry_run:
            log_fn(f"🔍 [Dry-run] Would set timestamp for {os.path.basename(file_path)} -> {dt}")
            return
        try:
            mod_time = dt.timestamp()
            os.utime(file_path, (mod_time, mod_time))
            log_fn(f"🕒 Timestamp updated: {os.path.basename(file_path)} -> {dt}")
        except Exception as e:
            log_fn(f"❌ Timestamp error {os.path.basename(file_path)}: {e}")
