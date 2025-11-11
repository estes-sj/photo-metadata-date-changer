import os
import time
import argparse
from datetime import datetime, timedelta
from PIL import Image
import piexif

######### START CONFIG (defaults can be overridden with CLI args) ###########

FOLDER_PATH = r"C:\Path\To\Your\Photos"
DEFAULT_REPLACEMENT_DATETIME_STR = "2025:11:03 11:45:00"
DEFAULT_INCREMENT_SECONDS = 1
DEFAULT_SORT_BY = "name"

########## END CONFIG ############


def parse_args():
    p = argparse.ArgumentParser(description="Update EXIF (JPEG) and filesystem timestamps.")
    p.add_argument("--folder", "-f", default=FOLDER_PATH, help="Folder containing files")
    p.add_argument(
        "--datetime",
        "-d",
        default=DEFAULT_REPLACEMENT_DATETIME_STR,
        help='Base replacement datetime in format "YYYY:MM:DD HH:MM:SS" (default: %(default)s)',
    )
    p.add_argument(
        "--increment-seconds",
        "-i",
        type=int,
        default=DEFAULT_INCREMENT_SECONDS,
        help="Seconds to increment per file (used in increment mode) (default: %(default)s)",
    )
    p.add_argument(
        "--no-increment",
        action="store_true",
        help="Disable incremental offsets in increment mode; use same datetime for all files",
    )
    p.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Process files in subdirectories recursively",
    )
    p.add_argument(
        "--sort-by",
        choices=("name", "mtime"),
        default=DEFAULT_SORT_BY,
        help="Sort files by 'name' or 'mtime' before applying increments (increment mode only)",
    )
    p.add_argument(
        "--mode",
        choices=("increment", "align-earliest"),
        default="increment",
        help="Run mode: 'increment' or 'align-earliest'.",
    )
    p.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    p.add_argument("--dry-run", action="store_true", help="Show changes without modifying files")
    return p.parse_args()


def gather_files(folder, recursive):
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


def parse_exif_datetime_str(dt_str):
    return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")


def get_original_time(file_path):
    """Return the original datetime (EXIF DateTimeOriginal if available, else mtime)."""
    lower = file_path.lower()
    if lower.endswith((".jpg", ".jpeg")):
        try:
            img = Image.open(file_path)
            exif_bytes = img.info.get("exif", b"")
            if exif_bytes:
                exif = piexif.load(exif_bytes)
                dto_tag = piexif.ExifIFD.DateTimeOriginal
                dto_val = exif.get("Exif", {}).get(dto_tag)
                if dto_val:
                    if isinstance(dto_val, (bytes, bytearray)):
                        dto_val = dto_val.decode("utf-8", errors="ignore")
                    return parse_exif_datetime_str(dto_val)
        except Exception:
            pass
    return datetime.fromtimestamp(os.path.getmtime(file_path))


def update_exif_date(image_path, dt, dry_run=False):
    """Update EXIF timestamps for a single JPEG image to datetime dt."""
    if dry_run:
        print(f"🔍 [Dry-run] Would update EXIF for {os.path.basename(image_path)} -> {dt}")
        return
    try:
        img = Image.open(image_path)
        exif_dict = piexif.load(img.info.get("exif", b""))
        exif_dict.setdefault("Exif", {})
        exif_dict.setdefault("0th", {})
        exif_time_str = dt.strftime("%Y:%m:%d %H:%M:%S").encode("utf-8")
        for tag in ("DateTimeOriginal", "DateTimeDigitized"):
            tag_id = piexif.ExifIFD.__dict__[tag]
            exif_dict["Exif"][tag_id] = exif_time_str
        dt_tag = piexif.ImageIFD.DateTime
        exif_dict["0th"][dt_tag] = exif_time_str
        exif_bytes = piexif.dump(exif_dict)
        img.save(image_path, "jpeg", exif=exif_bytes)
        print(f"✅ EXIF updated: {os.path.basename(image_path)} -> {dt}")
    except Exception as e:
        print(f"❌ EXIF error {os.path.basename(image_path)}: {e}")


def update_file_timestamp(file_path, dt, dry_run=False):
    """Update filesystem modified + access timestamps."""
    if dry_run:
        print(f"🔍 [Dry-run] Would set timestamp for {os.path.basename(file_path)} -> {dt}")
        return
    try:
        mod_time = dt.timestamp()
        os.utime(file_path, (mod_time, mod_time))
        print(f"🕒 Timestamp updated: {os.path.basename(file_path)} -> {dt}")
    except Exception as e:
        print(f"❌ Timestamp error {os.path.basename(file_path)}: {e}")


def main():
    args = parse_args()
    try:
        replacement_datetime = datetime.strptime(args.datetime, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        print("Invalid datetime format. Use: YYYY:MM:DD HH:MM:SS")
        return

    files = gather_files(args.folder, args.recursive)
    if not files:
        print(f"No files found in {args.folder}")
        return

    if args.mode == "increment":
        if args.sort_by == "name":
            files.sort(key=lambda p: os.path.basename(p).lower())
        else:
            files.sort(key=lambda p: os.path.getmtime(p))
    else:
        files.sort(key=lambda p: get_original_time(p))

    print(f"\nFound {len(files)} file(s) in `{args.folder}` (recursive={args.recursive}).")
    for p in files[:10]:
        print("  -", os.path.relpath(p, args.folder))

    if not args.yes:
        choice = input(
            f"\nMode: {args.mode}. Apply datetime = {replacement_datetime} "
            f"{'(dry-run)' if args.dry_run else ''}? (y/n): "
        ).strip().lower()
        if choice != "y":
            print("Operation canceled.")
            return

    # --- align-earliest mode ---
    if args.mode == "align-earliest":
        orig_times = {f: get_original_time(f) for f in files}
        earliest_file, earliest_time = min(orig_times.items(), key=lambda kv: kv[1])
        offset = replacement_datetime - earliest_time
        print(f"\nEarliest file: {os.path.basename(earliest_file)} ({earliest_time})")
        print(f"Offset applied to all: {offset}\n")

        for f in files:
            new_dt = orig_times[f] + offset
            if f.lower().endswith((".jpg", ".jpeg")):
                update_exif_date(f, new_dt, dry_run=args.dry_run)
            update_file_timestamp(f, new_dt, dry_run=args.dry_run)

    # --- increment mode ---
    else:
        for idx, filepath in enumerate(files):
            if args.no_increment:
                dt = replacement_datetime
            else:
                dt = replacement_datetime + timedelta(seconds=(idx * args.increment_seconds))
            if filepath.lower().endswith((".jpg", ".jpeg")):
                update_exif_date(filepath, dt, dry_run=args.dry_run)
            update_file_timestamp(filepath, dt, dry_run=args.dry_run)

    print("\n✅ Done." if not args.dry_run else "\n🔍 Dry-run complete. No files modified.")


if __name__ == "__main__":
    main()
