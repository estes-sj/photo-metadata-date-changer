import os
from datetime import datetime
from PIL import Image
import piexif

######### START CONFIG ###########

# Path to your folder
FOLDER_PATH = r"C:\Users\Samuel\Downloads\20250524ae8d39f9773e759813cb0f26987ed3b108749ccca625e1c8e2993037102f0efb"
# Replacement date
replacement_date_str = "2022:04:22"

########## END CONFIG ############

def update_exif_date(image_path):
    try:
        img = Image.open(image_path)
        exif_dict = piexif.load(img.info.get("exif", b""))

        modified = False
        # Ensure IFDs exist
        exif_dict.setdefault("Exif", {})
        exif_dict.setdefault("0th", {})

        # Set DateTimeOriginal and DateTimeDigitized to replacement date
        for tag in ("DateTimeOriginal", "DateTimeDigitized"):
            tag_id = piexif.ExifIFD.__dict__[tag]
            exif_dict["Exif"][tag_id] = f"{replacement_date_str} 12:00:00".encode("utf-8")
            modified = True

        # Set main DateTime in 0th IFD
        dt_tag = piexif.ImageIFD.DateTime
        exif_dict["0th"][dt_tag] = f"{replacement_date_str} 12:00:00".encode("utf-8")
        modified = True

        if modified:
            exif_bytes = piexif.dump(exif_dict)
            img.save(image_path, "jpeg", exif=exif_bytes)
            print(f"✅ Updated EXIF: {os.path.basename(image_path)}")

    except Exception as e:
        print(f"❌ Error processing {os.path.basename(image_path)}: {e}")

def main():
    # Gather all JPEGs
    all_files = [
        os.path.join(FOLDER_PATH, f)
        for f in os.listdir(FOLDER_PATH)
        if f.lower().endswith((".jpg", ".jpeg"))
    ]

    count = len(all_files)
    print(f"\nFound {count} JPEG file(s) in `{FOLDER_PATH}`.")

    if count == 0:
        print("No files to process.")
        return

    print("\nFirst 10 files:")
    for p in all_files[:10]:
        print("  -", os.path.basename(p))

    choice = input(f"\nApply EXIF date = {replacement_date_str} to all {count} files? (y/n): ").strip().lower()
    if choice != "y":
        print("Operation canceled.")
        return

    for filepath in all_files:
        update_exif_date(filepath)

    print("\n✅ Done. All files updated.")

if __name__ == "__main__":
    main()