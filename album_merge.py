import argparse
import re
from pathlib import Path
from typing import *
import shutil
from wand.image import Image
from datetime import datetime

def do_merge(source: Path, dest: Path, exts: List[str]) -> None:
    for ext in exts:
        for src_file in source.glob(ext, case_sensitive=False):
            if not src_file.is_file():
                continue
            copy_file(src_file, dest)

def copy_file(source_file: Path, dest:Path) -> None:
    """
    Copy file, name is `{date}_{second_of_day}` where second of day would be 00000 at midnight and 86399 a second before midnight.  Add a `_#` suffix if there is a collision of the file stem (irrespective of the suffix), so img_20250512_76447.jpg would collide with img_20250512_76447.heic and be renamed to img_20250512_76447_1.jpg
    """
    with Image(filename=source_file) as image:
        prefix = "img_unk"
        for key in "EXIF:DateTimeOriginal", "EXIF:DateTime":
            time_str = image.metadata.get(key, "")
            # meitu photo app was adding AM/PM to 24h time strings causing issues parsing 
            time_str = re.sub(r"[A-Za-z]", " ", time_str).strip()
            try:
                dt = datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S")
                date_str = dt.strftime("%Y%m%d")
                start_of_day = datetime.strptime(date_str, "%Y%m%d")
                second_of_day = (dt - start_of_day).total_seconds()
                prefix = f"img_{date_str}_{int(second_of_day):05d}"
                break
            except:
                continue
            
        suffix = source_file.suffix
        trailer = ""
        for i in range(1, 1<<31):
            stem = f"{prefix}{trailer}"
            if not list(dest.glob(f"{stem}.*")):
                file_path = dest / f"{stem}{suffix}"
                shutil.copy2(source_file, file_path)
                print(f"{source_file} -> {file_path}")
                break
            trailer = f"_{i}"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='album-merge',
                                     description=r'''
                                     Pool images from different sources into the same folder.
                                     During merge files are renamed based on EXIF timestamp. 
                                     Collisions are resolved by adding a suffix number to the file stem.
                                     ''')
    parser.add_argument('-s', '--src', required=True,
                        help="source folder"
                        )
    parser.add_argument('-d', '--dst', required=True,
                        help="destination folder, will be created if does not exist")
    parser.add_argument('-e', '--ext', action='append',
                        help="file extensions, multiple may be specified (i.e. --ext=jpg --ext=heic OR --ext=jpg,heic)")

    args = parser.parse_args()
    print(f"src={args.src}, dst={args.dst}, ext={args.ext}")
    if args.ext:
        ext = ",".join(args.ext)
        ext  = re.sub(r"\s","", ext)
        ext = ext.split(",")
        for i in range(len(ext)):
            if not ext[i].startswith("."):
                ext[i] = "*."+ext[i]
            else:
                ext[i] = "*"+ext[i]
    else:
        ext = ["*"]
    source = Path(args.src)
    dest = Path(args.dst)
    if not source.is_dir():
        print("Source does not exist or is not a directory")
        exit(-1)
    if not dest.is_dir():
        print("Destination does not exist, creating new directory")
        dest.mkdir()
    do_merge(source=source, dest=dest, exts=ext)

