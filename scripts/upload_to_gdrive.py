#!/usr/bin/env python3
"""
upload_to_gdrive.py — Uploads all project screenshots and master ZIP to Google Drive.
"""

import subprocess
import sys
from pathlib import Path

FOLDER_ID = "1YbLNFueJb6pXvRurNymoy4TYBGKd6LYj"
ROOT = Path("/home/aumpatro/Project_Crime_detection")
SCREENSHOTS_DIR = ROOT / "screenshots"
ZIP_PATH = ROOT / "Project_Screenshots_and_Charts.zip"

def upload_file(path: Path):
    print(f"Uploading {path.name} to Google Drive...")
    cmd = ["gdrive", "mutate", "upload", str(path), "--parent", FOLDER_ID]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  ✓ {res.stdout.strip()}")
    else:
        print(f"  ✗ Error uploading {path.name}: {res.stderr}")

def main():
    # 1. Upload master ZIP first
    if ZIP_PATH.exists():
        upload_file(ZIP_PATH)

    # 2. Upload all individual screenshots
    png_files = sorted(SCREENSHOTS_DIR.glob("*.png"))
    for png in png_files:
        upload_file(png)

    print("\nAll uploads completed successfully!")

if __name__ == "__main__":
    main()
