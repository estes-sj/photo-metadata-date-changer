# Photo Metadata Date Changer

Simple python script that uses `piexif` and `pillow` to add/update the photos in a specified folder with the specified date.

## How to Use

Assuming you have `git`, `pip`, and `python` installed:

1. Clone this repo (or download directly)
   ```bash
   git clone https://github.com/estes-sj/photo-metadata-date-changer
   ```
2. Navigate inside the downloaded folder:
   ```bash
   cd photo-metadata-date-changer
   ```
3. Install the neccessary python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Manually edit the configuration section of `main.py` to match your folder containing the photos to be edited and the desired date:
   ```python
   # Path to your folder
   FOLDER_PATH = r"C:\example\path\to\your\folder"
   # Replacement date
   replacement_date_str = "2022:04:22"
   ```
5. Run the script:
   ```bash
   python main.py
   ```
6. If photos were successfully found, the number of photos to be changed and the first 10 found will be displayed. You will be asked to confirm changes by typing `y` and then hitting `ENTER`. Type anything else to cancel.

## Example Run

**`main.py` Configuration:**

```python
# Path to your folder
FOLDER_PATH = r"C:\Users\Samuel\Downloads\2bac1124ae8d39f9773e759813cb0f26987ed3b108749ccca625eab1612237102f0efb"
# Replacement date
replacement_date_str = "2022:04:22"
```

**Terminal Output:**

```bash
Samuel@DESKTOP-QST8A15 MINGW64 //teetunk.dev/user_share/Tools/Photo Metadata Date Changer
$ python main.py

Found 330 JPEG file(s) in `C:\Users\Samuel\Downloads\2bac1124ae8d39f9773e759813cb0f26987ed3b108749ccca625eab1612237102f0efb`.

First 10 files:
  - img_0001_52021093674_l.jpg
  - img_0002_52021087259_l.jpg
  - img_0003_52019797787_l.jpg
  - img_0004_52021356505_l.jpg
  - img_0005_52021093604_l.jpg
  - img_0006_52019797697_l.jpg
  - img_0007_52020836901_l.jpg
  - img_0008_52020881108_l.jpg
  - img_0009_52020836866_l.jpg
  - img_0010_52020881063_l.jpg

Apply EXIF date = 2022:04:22 to all 330 files? (y/n): y

✅ Updated EXIF: img_0001_52021093674_l.jpg
✅ Updated EXIF: img_0002_52021087259_l.jpg
✅ Updated EXIF: img_0003_52019797787_l.jpg
✅ Updated EXIF: img_0004_52021356505_l.jpg
✅ Updated EXIF: img_0005_52021093604_l.jpg

✅ Done. All files updated.
```
