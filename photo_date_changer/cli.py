"""CLI entrypoint and argument parsing."""
import argparse
from datetime import datetime
import tkinter as tk

from .runner import OperationRunner
from .gui import APP_VERSION

DEFAULT_FOLDER = "./"
DEFAULT_DATETIME_STR = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
DEFAULT_INCREMENT_SECONDS = 1
DEFAULT_SORT_BY = "name"
DEFAULT_MODE = "increment"

def parse_args():
    p = argparse.ArgumentParser(description="Update EXIF (JPEG) and filesystem timestamps (CLI + GUI).")
    p.add_argument("--folder", "-f", default=DEFAULT_FOLDER, help="Folder containing files")
    p.add_argument("--datetime", "-d", default=DEFAULT_DATETIME_STR, help='Base replacement datetime "YYYY:MM:DD HH:MM:SS"')
    p.add_argument("--increment-seconds", "-i", type=int, default=DEFAULT_INCREMENT_SECONDS, help="Seconds to increment per file")
    p.add_argument("--no-increment", action="store_true", help="Disable incremental offsets")
    p.add_argument("--recursive", "-r", action="store_true", help="Process files recursively")
    p.add_argument("--sort-by", choices=("name", "mtime"), default=DEFAULT_SORT_BY, help="Sort files by")
    p.add_argument("--mode", choices=("increment", "align-earliest"), default=DEFAULT_MODE, help="Run mode")
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    p.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    p.add_argument("--gui", action="store_true", help="Launch Tkinter GUI")
    return p.parse_args()

def main():
    args = parse_args()
    print("---------------------------------------------")
    print("Photo Metadata Date Changer | Version " + APP_VERSION)
    print("---------------------------------------------")
    if args.gui:
        # lazy import so CLI doesn't require Tk if not used
        from .gui import AppGUI
        root = tk.Tk()
        root.minsize(720, 620)
        AppGUI(root)
        root.mainloop()
        return

    try:
        replacement_datetime = datetime.strptime(args.datetime, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        print("Invalid datetime format. Use: YYYY:MM:DD HH:MM:SS")
        return

    runner = OperationRunner()
    runner.run(
        folder=args.folder,
        replacement_datetime=replacement_datetime,
        increment_seconds=args.increment_seconds,
        no_increment=args.no_increment,
        recursive=args.recursive,
        sort_by=args.sort_by,
        mode=args.mode,
        dry_run=args.dry_run,
        yes=args.yes,
        log_fn=print
    )
