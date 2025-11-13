"""EXIF read/write helpers."""
import os
from datetime import datetime
from PIL import Image
import piexif

class ExifHandler:
    """Read/write EXIF DateTime tags for JPEGs."""

    @staticmethod
    def parse_exif_datetime_str(dt_str: str) -> datetime:
        return datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S")

    @staticmethod
    def get_exif_datetime(path: str):
        try:
            img = Image.open(path)
            exif_bytes = img.info.get("exif", b"")
            if not exif_bytes:
                return None
            exif = piexif.load(exif_bytes)
            dto_tag = piexif.ExifIFD.DateTimeOriginal
            dto_val = exif.get("Exif", {}).get(dto_tag)
            if dto_val:
                if isinstance(dto_val, (bytes, bytearray)):
                    dto_val = dto_val.decode("utf-8", errors="ignore")
                return ExifHandler.parse_exif_datetime_str(dto_val)
        except Exception:
            return None

    @staticmethod
    def update_exif_date(image_path: str, dt: datetime, dry_run: bool=False, log_fn=print):
        if dry_run:
            log_fn(f"🔍 [Dry-run] Would update EXIF for {os.path.basename(image_path)} -> {dt}")
            return
        try:
            img = Image.open(image_path)
            exif_dict = piexif.load(img.info.get("exif", b"")) if img.info.get("exif", b"") else {}
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
            log_fn(f"✅ EXIF updated: {os.path.basename(image_path)} -> {dt}")
        except Exception as e:
            log_fn(f"❌ EXIF error {os.path.basename(image_path)}: {e}")
