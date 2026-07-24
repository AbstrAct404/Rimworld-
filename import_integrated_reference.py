"""Import the six newly maintained mods from the reference Aya language pack.

The referenced Workshop package labels some folders ``ChineseSimplified`` even
when their values still contain traditional characters.  Convert them with
OpenCC, then apply the repository terminology normalizer before checking the
key-aligned values into ``reviewed_game_translations.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).with_name("tools") / "python-packages"))
from opencc import OpenCC  # type: ignore

import build_translations as build


REFERENCE_LAYOUT = {
    "3750626266": ("CanaanIntellect", "1.6/Languages/ChineseSimplified (简体中文)"),
    "3489429571": ("Chaoura", "1.6/Languages/ChineseSimplified"),
    "2729712799": ("Enforcer", "1.6/Languages/ChineseSimplified"),
    "2706009136": ("Nexaga", "1.6/Languages/ChineseSimplified"),
    "3675887482": ("Outerm", "1.6/Languages/ChineseSimplified"),
    "3477749439": ("Zoichor", "1.6/Languages/ChineseSimplified"),
}


def read_values(folder: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not folder.is_dir():
        return values
    for file in folder.rglob("*.xml"):
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        for child in root:
            value = build.text(child)
            if value:
                values[child.tag] = value
    return values


def source_keys(source: Path) -> set[str]:
    keys: set[str] = set()
    defs = build.active_defs(source)
    if defs:
        for file in defs.rglob("*.xml"):
            try:
                root = ET.parse(file).getroot()
            except ET.ParseError:
                continue
            for definition in root:
                def_name = (
                    build.text(definition.find("defName"))
                    or definition.get("Name", "")
                )
                if not def_name:
                    continue
                for child in definition:
                    if child.tag in build.FIELDS and build.text(child):
                        keys.add(f"{def_name}.{child.tag}")
    for file in source.rglob("*.xml"):
        parts = {part.lower() for part in file.parts}
        if "languages" not in parts or "keyed" not in parts:
            continue
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        keys.update(child.tag for child in root if build.text(child))
    return keys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("reviewed_game_translations.json"),
    )
    parser.add_argument(
        "--supplemental-root",
        type=Path,
        default=Path(__file__).with_name("supplemental"),
        help="Destination for reference-only overlays whose source mod has no XML defs",
    )
    args = parser.parse_args()

    reviewed = json.loads(args.output.read_text(encoding="utf-8"))
    converter = OpenCC("t2s")
    for mod_id, (folder_name, relative_language_path) in REFERENCE_LAYOUT.items():
        keys = source_keys(args.source_root / mod_id)
        candidates = read_values(
            args.reference_root / folder_name / relative_language_path
        )
        imported: dict[str, str] = {}
        for key in sorted(keys & candidates.keys()):
            value = converter.convert(candidates[key])
            value = build.normalize_display_names(build.local_translate(value))
            if value and not build.is_japanese(value):
                imported[key] = value
        reviewed[mod_id] = imported
        print(
            f"{mod_id}: imported {len(imported)}/{len(keys)} "
            f"(reference contains {len(candidates)} keys)"
        )

    args.output.write_text(
        json.dumps(reviewed, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Chaoura UB defines most of its content in an assembly, so there are no
    # source Def XML files for the normal extractor to walk.  Preserve the
    # dedicated UB files from the reference pack as a reproducible supplemental
    # overlay instead of silently publishing an empty localization.
    chaoura_source = (
        args.reference_root
        / "Chaoura"
        / "1.6"
        / "Languages"
        / "ChineseSimplified"
    )
    chaoura_output = (
        args.supplemental_root
        / "3489429571"
        / "Languages"
        / "ChineseSimplified"
    )
    copied = 0
    for file in chaoura_source.rglob("*.xml"):
        if "CO_UB" not in file.name and "UB_" not in file.name:
            continue
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        for child in root:
            value = converter.convert(build.text(child))
            child.text = build.normalize_display_names(build.local_translate(value))
        destination = chaoura_output / file.relative_to(chaoura_source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        build.xml_write(destination, root)
        copied += sum(1 for child in root if build.text(child))
    print(f"3489429571: wrote {copied} supplemental Chaoura UB values")


if __name__ == "__main__":
    main()
