#!/usr/bin/env python3
"""Build repo/addons.xml and repo/addons.xml.md5 for Kodi repository distribution."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ADDONS = [
    ROOT / "repository.kodiseerr" / "addon.xml",
    ROOT / "addon.xml",
]
OUTPUT_XML = ROOT / "repo" / "addons.xml"
OUTPUT_MD5 = ROOT / "repo" / "addons.xml.md5"


def build_addons_xml() -> bytes:
    addons_root = ET.Element("addons")

    for addon_path in SOURCE_ADDONS:
        addon_tree = ET.parse(addon_path)
        addon_root = addon_tree.getroot()
        addons_root.append(copy.deepcopy(addon_root))

    ET.indent(addons_root, space="    ")
    body = ET.tostring(addons_root, encoding="utf-8")
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + body + b"\n"


def main() -> None:
    OUTPUT_XML.parent.mkdir(parents=True, exist_ok=True)
    content = build_addons_xml()
    OUTPUT_XML.write_bytes(content)

    digest = hashlib.md5(content).hexdigest()
    OUTPUT_MD5.write_text(f"{digest}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
