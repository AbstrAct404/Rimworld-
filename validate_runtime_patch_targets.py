"""Validate generated Aya runtime-patch XPath targets against active source defs."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from lxml import etree

from build_translations import MODS, WORKSHOP, active_defs


MODS_ROOT = Path("Mods")


def merged_active_defs() -> etree._Element:
    document = etree.Element("root")
    merged = etree.SubElement(document, "Defs")
    for mod_id, _mod_name in MODS:
        defs = active_defs(WORKSHOP / mod_id)
        if defs is None:
            continue
        for file in sorted(defs.rglob("*.xml")):
            try:
                root = etree.parse(str(file)).getroot()
            except etree.XMLSyntaxError:
                continue
            if root.tag != "Defs":
                continue
            for child in root:
                merged.append(child)
    return document


def main() -> None:
    defs = merged_active_defs()
    checked = 0
    missing: list[tuple[str, str]] = []
    find_mod_files: list[str] = []

    for package in sorted(MODS_ROOT.glob("* - * Chinese")):
        if package.name.startswith("0000000000"):
            continue
        patch_root = package / "Patches"
        if not patch_root.is_dir():
            continue
        for file in sorted(patch_root.glob("*.xml")):
            root = ET.parse(file).getroot()
            if root.findall('.//Operation[@Class="PatchOperationFindMod"]'):
                find_mod_files.append(str(file))
            for node in root.findall(".//xpath"):
                xpath = node.text or ""
                checked += 1
                if not defs.xpath(xpath):
                    missing.append((str(file), xpath))

    if find_mod_files or missing:
        for file in find_mod_files:
            print(f"unexpected PatchOperationFindMod: {file}")
        for file, xpath in missing:
            print(f"missing target: {file}: {xpath}")
        raise SystemExit(1)

    print(
        f"validated {checked} runtime-patch XPath targets; "
        "all resolve against active 1.6 source defs"
    )


if __name__ == "__main__":
    main()
