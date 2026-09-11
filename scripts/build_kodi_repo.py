#!/usr/bin/env python3
import re
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ADDON_DIR = ROOT / "plugin.video.kodiseerr"
ADDON_XML = ADDON_DIR / "addon.xml"
ZIP_ROOT = ROOT / "zip"


def read_addon_info(addon_xml: Path):
    tree = ET.parse(addon_xml)
    root = tree.getroot()
    addon_id = root.attrib["id"]
    version = root.attrib["version"]
    return addon_id, version


def make_addons_xml(zip_dir: Path, addon_xml_path: Path):
    xml_content = addon_xml_path.read_text(encoding="utf-8")
    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    xml_content = re.sub(r'^\s*<\?xml[^>]*\?>\s*', '', xml_content, flags=re.IGNORECASE)
    addons_xml += xml_content.strip() + "\n</addons>\n"

    out = zip_dir / "addons.xml"
    out.write_text(addons_xml, encoding="utf-8")


def make_addons_xml_md5(zip_dir: Path):
    import hashlib

    data = (zip_dir / "addons.xml").read_bytes()
    md5 = hashlib.md5(data).hexdigest()
    (zip_dir / "addons.xml.md5").write_text(md5, encoding="utf-8")


def make_addon_zip(addon_dir: Path, zip_dir: Path, addon_id: str, version: str):
    addon_zip_dir = zip_dir / addon_id
    addon_zip_dir.mkdir(parents=True, exist_ok=True)
    out_zip = addon_zip_dir / f"{addon_id}-{version}.zip"

    if out_zip.exists():
        out_zip.unlink()

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in addon_dir.rglob("*"):
            if path.is_file():
                rel = path.relative_to(addon_dir.parent)
                zf.write(path, rel.as_posix())


def main():
    if not ADDON_XML.exists():
        raise FileNotFoundError(f"Missing {ADDON_XML}")

    addon_id, version = read_addon_info(ADDON_XML)

    ZIP_ROOT.mkdir(parents=True, exist_ok=True)

    make_addon_zip(ADDON_DIR, ZIP_ROOT, addon_id, version)
    make_addons_xml(ZIP_ROOT, ADDON_XML)
    make_addons_xml_md5(ZIP_ROOT)

    print(f"Built Kodi repo files for {addon_id} v{version} in {ZIP_ROOT}")


if __name__ == "__main__":
    main()
