import os
import zipfile
import sys
import subprocess
from pathlib import Path
import pkg_resources  
def main():
    print("[*] Extracting zip file...")

    # zip ফাইলের path
    zip_path = pkg_resources.resource_filename('termux_native_gui', '../termux.zip')
    extract_dir = Path.home() / "termux_native_gui_extracted"

    if not extract_dir.exists():
        extract_dir.mkdir(parents=True)

    # unzip করা
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    print(f"[*] Extracted to {extract_dir}")

    # setup.sh এক্সিকিউট
    setup_script = extract_dir / "setup.sh"
    if setup_script.exists():
        print("[*] Running setup.sh...")
        subprocess.run(["bash", str(setup_script)])
    else:
        print("[!] setup.sh not found in the extracted folder.")