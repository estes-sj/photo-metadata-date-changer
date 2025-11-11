# Photo Metadata Date Changer

A Python script that updates **EXIF metadata** (for JPEGs) and **filesystem timestamps** for all photos in a given folder.
It supports incremental timestamps, aligning photo times based on the earliest photo, recursive processing, and dry-run mode for safe previews.

---

## ⚡ Quick Reference

| Use Case                       | Example Command                                                                | Description                                                                          |
| ------------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| 🧪 Preview changes (no writes) | `python main.py --dry-run -f "C:\Photos"`                                      | Safe preview without modifying any files                                             |
| 🕓 Increment timestamps        | `python main.py --datetime ""2025:11:03 11:45:00+00:00" -i 2 -f "C:\Photos"`   | Adds +2s between each file, starting from given date                                 |
| 🧭 Align earliest photo        | `python main.py --mode align-earliest -d "2025:11:03 11:45:00" -f "C:\Photos"` | Keeps relative spacing between photos, shifts all so the earliest matches given date |
| 🗂 Recursive processing         | `python main.py -r -y -f "D:\AllAlbums"`                                       | Processes subfolders too (no prompt)                                                 |
| 🕰 Fixed time (no increment)    | `python main.py --no-increment -y -d "2024:12:31 23:59:00" -f "C:\DCIM"`       | Sets all photos to exactly the same timestamp                                        |
| ⚙️ Full auto run               | `python main.py --mode align-earliest -r -y -f "E:\CameraDump"`                | Recursive + align-earliest + skip confirmation                                       |

---

## 📦 Features

- Update **EXIF DateTimeOriginal**, **DateTimeDigitized**, and **DateTime** for `.jpg`/`.jpeg`
- Update filesystem **modified/access** timestamps for all files
- Increment timestamps for ordered photo sequences
- Align timestamps while preserving relative differences
- Optional recursive mode
- Safe dry-run for verification

---

## ⚙️ Installation

Make sure you have Python 3.8+ and `pip` installed, then:

```bash
git clone https://github.com/estes-sj/photo-metadata-date-changer
cd photo-metadata-date-changer
pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
python main.py [OPTIONS]
```

---

## 🧭 Arguments

| Argument                    | Type        | Default                     | Description                                                                                |
| --------------------------- | ----------- | --------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------- |
| `--folder`, `-f`            | `str`       | `FOLDER_PATH` from config   | Path to the folder containing photos                                                       |
| `--datetime`, `-d`          | `str`       | `2025:11:03 11:45:00+00:00` | Base datetime (UTC, format: `YYYY:MM:DD HH:MM:SS+00:00` or ISO8601 `YYYY-MM-DDTHH:MM:SSZ`) |
| `--increment-seconds`, `-i` | `int`       | `1`                         | Seconds to increment per file in increment mode                                            |
| `--no-increment`            | flag        | —                           | Disable incremental offsets (use same timestamp for all)                                   |
| `--recursive`, `-r`         | flag        | —                           | Include subfolders                                                                         |
| `--sort-by`                 | `name`      | `mtime`                     | `name`                                                                                     | Sort order in increment mode |
| `--mode`                    | `increment` | `align-earliest`            | `increment`                                                                                | How timestamps are assigned  |
| `--yes`, `-y`               | flag        | —                           | Skip confirmation prompt                                                                   |
| `--dry-run`                 | flag        | —                           | Show what changes would be made (no writes)                                                |

---

## 🧩 Modes Explained

### 🕓 `increment` (default)

Each file gets the base datetime plus an incremental offset.
Perfect for restoring chronological order.

| File       | Assigned Time       |
| ---------- | ------------------- |
| photo1.jpg | 2025:11:03 11:45:00 |
| photo2.jpg | 2025:11:03 11:45:01 |
| photo3.jpg | 2025:11:03 11:45:02 |

---

### 🧭 `align-earliest`

The earliest photo becomes the reference.
All others keep their relative time difference compared to it.

| File       | Original Time       | New Time            |
| ---------- | ------------------- | ------------------- |
| photo1.jpg | 2023:08:14 09:31:45 | 2025:11:03 11:45:00 |
| photo2.jpg | +00:00:10 later     | 2025:11:03 11:45:10 |

---

## 🧪 Examples

### 🔹 Example 1 — Dry Run (Increment Mode)

```bash
python main.py --folder "C:\Photos\BeachTrip" --datetime "2025:11:03 11:45:00" --increment-seconds 2 --dry-run
```

**Output (trimmed):**

```bash
Found 4 file(s) in `C:\Photos\BeachTrip`.
  - beach_001.jpg
  - beach_002.jpg
  - beach_003.jpg
  - beach_004.jpg

Mode: increment. Apply datetime = 2025-11-03 11:45:00 (dry-run)? (y/n): y

🔍 [Dry-run] Would update EXIF for beach_001.jpg -> 2025-11-03 11:45:00
🔍 [Dry-run] Would set timestamp for beach_001.jpg -> 2025-11-03 11:45:00
🔍 [Dry-run] Would update EXIF for beach_002.jpg -> 2025-11-03 11:45:02
🔍 [Dry-run] Would set timestamp for beach_002.jpg -> 2025-11-03 11:45:02
...

🔍 Dry-run complete. No files modified.
```

---

### 🔹 Example 2 — Align Earliest Mode (Actual Run)

```bash
python main.py --mode align-earliest --datetime "2025:11:03 11:45:00" -y --folder "C:\Photos\Hike"
```

**Output (trimmed):**

```bash
Found 5 file(s) in `C:\Photos\Hike`.

Earliest file: IMG_103.jpg (2023-08-14 09:31:45)
Offset applied to all: 808 days, 2:13:15

✅ EXIF updated: IMG_101.jpg -> 2025-11-03 11:44:55
🕒 Timestamp updated: IMG_101.jpg -> 2025-11-03 11:44:55
✅ EXIF updated: IMG_102.jpg -> 2025-11-03 11:45:01
🕒 Timestamp updated: IMG_102.jpg -> 2025-11-03 11:45:01
...

✅ Done.
```

---

### 🔹 Example 3 — Recursive Same-Time Update

```bash
python main.py -r --no-increment -y -d "2024:12:31 23:59:00" -f "D:\CameraDump"
```

Every file (in all subfolders) gets:

```
2024:12:31 23:59:00
```

---

## 🧼 Tip: Always Start with Dry Run

Before doing an actual run, preview with:

```bash
python main.py --dry-run -f "C:\Photos"
```

You'll see exactly which timestamps would be changed.
