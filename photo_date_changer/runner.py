"""OperationRunner: encapsulates the run logic used by CLI and GUI."""
import os
import threading
from datetime import timedelta
from typing import Callable, Optional
from .file_ops import FileTimestampManager
from .exif_utils import ExifHandler

class OperationRunner:
    def __init__(self, file_mgr: FileTimestampManager = None, exif: ExifHandler = None):
        self.file_mgr = file_mgr or FileTimestampManager()
        self.exif = exif or ExifHandler()

    def run(
        self,
        folder: str,
        replacement_datetime,
        increment_seconds: int = 1,
        no_increment: bool = False,
        recursive: bool = False,
        sort_by: str = "name",
        mode: str = "increment",
        dry_run: bool = False,
        yes: bool = False,
        log_fn: Callable = print,
        confirm_fn: Callable = None,
        progress_fn: Callable = None,
        cancel_event: Optional[threading.Event] = None,  # <-- supports cooperative cancellation
    ):
        """
        Perform the operation. If cancel_event is provided and set at any time,
        the runner will stop cleanly between files.
        """
        if not os.path.isdir(folder):
            log_fn(f"❌ Folder not found: {folder}")
            return

        files = self.file_mgr.gather_files(folder, recursive)
        files = [f for f in files if os.path.isfile(f)]
        if not files:
            log_fn(f"No files found in {folder}")
            return

        # sorting
        if mode == "increment":
            if sort_by == "name":
                files.sort(key=lambda p: os.path.basename(p).lower())
            else:
                files.sort(key=lambda p: os.path.getmtime(p))
        else:
            files.sort(key=lambda p: self.file_mgr.get_original_time(p))

        log_fn(f"Found {len(files)} file(s) in `{folder}` (recursive={recursive}).")
        log_fn("First 10 files:")
        for p in files[:10]:
            log_fn("  - " + os.path.relpath(p, folder))

        if not yes:
            if confirm_fn:
                proceed = confirm_fn(f"Mode: {mode}. Apply datetime = {replacement_datetime}?")
                if not proceed:
                    log_fn("Operation canceled.")
                    return
            else:
                resp = input(f"\nMode: {mode}. Apply datetime = {replacement_datetime}? (y/n): ").strip().lower()
                if resp != "y":
                    log_fn("Operation canceled.")
                    return

        # check cancellation before starting heavy work
        if cancel_event and cancel_event.is_set():
            log_fn("🛑 Operation canceled before start.")
            return

        # apply updates
        if mode == "align-earliest":
            orig_times = {f: self.file_mgr.get_original_time(f) for f in files}
            earliest_file, earliest_time = min(orig_times.items(), key=lambda kv: kv[1])
            offset = replacement_datetime - earliest_time
            log_fn(f"Earliest file: {os.path.relpath(earliest_file, folder)} (original: {earliest_time})")
            log_fn(f"Applying offset of {offset} to all files.\n")
            for idx, f in enumerate(files):
                # cooperative cancellation check
                if cancel_event and cancel_event.is_set():
                    log_fn("🛑 Operation canceled by user.")
                    return
                orig = orig_times[f]
                new_dt = orig + offset
                if f.lower().endswith((".jpg", ".jpeg")):
                    self.exif.update_exif_date(f, new_dt, dry_run=dry_run, log_fn=log_fn)
                self.file_mgr.update_file_timestamp(f, new_dt, dry_run=dry_run, log_fn=log_fn)
                if progress_fn:
                    progress_fn(idx + 1, len(files))
        else:
            for idx, filepath in enumerate(files):
                # cooperative cancellation check
                if cancel_event and cancel_event.is_set():
                    log_fn("🛑 Operation canceled by user.")
                    return
                dt = replacement_datetime if no_increment else replacement_datetime + timedelta(seconds=(idx * increment_seconds))
                if filepath.lower().endswith((".jpg", ".jpeg")):
                    self.exif.update_exif_date(filepath, dt, dry_run=dry_run, log_fn=log_fn)
                self.file_mgr.update_file_timestamp(filepath, dt, dry_run=dry_run, log_fn=log_fn)
                if progress_fn:
                    progress_fn(idx + 1, len(files))

        log_fn("\n✅ Done." if not dry_run else "\n🔍 Dry-run complete. No files modified.")
