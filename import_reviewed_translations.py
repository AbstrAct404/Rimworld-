"""Import key-aligned Chinese translations as review candidates.

Only keys that are present in the current generated 1.6 localization are
imported.  Values are normalized through terminology.json.  The resulting JSON
is checked into the repository so normal builds never depend on the reference
Workshop items being installed.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import build_translations as build


REFERENCE_SOURCES = {
    "2946679071": ("3005231606", "Languages/ChineseSimplified"),
    "3505571618": ("3511842550", "Languages/ChineseSimplified (简体中文)"),
    "3153539856": ("3153837818", "Languages/ChineseSimplified"),
    "2954714860": ("3016320702", "Languages/ChineseSimplified"),
    "2871413100": ("3300652588", "Languages/ChineseSimplified"),
    "2227425882": ("3004183072", "Languages/ChineseSimplified"),
    "2569091688": ("3004183210", "Languages/ChineseSimplified"),
    "2198830432": ("2928115625", "1.6/Languages/ChineseSimplified"),
    "2394460334": ("3234346156", "Languages/ChineseSimplified"),
    "2763078885": ("3007159825", "Languages/ChineseSimplified"),
    "2504657401": ("3004183402", "Languages/ChineseSimplified"),
    "2676302514": ("3234134954", "Languages/ChineseSimplified"),
    "2233666290": ("3158663696", "Languages/ChineseSimplified"),
    "2608237489": ("2626045611", "1.5/Languages/ChineseSimplified"),
    "2216916011": ("3004183640", "Languages/ChineseSimplified"),
}


def read_language_values(folder: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for file in folder.rglob("*.xml"):
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        for child in root:
            value = (child.text or "").strip()
            if value:
                values[child.tag] = value
    return values


def usable_reference(value: str) -> bool:
    """Reject visibly incomplete, editorial, or encoding-damaged candidates."""
    if build.is_japanese(value):
        return False
    rejected_markers = (
        "作者另外",
        "口口口口",
        "鐢",
        "patn",
        "koo o",
    )
    return not any(marker in value for marker in rejected_markers)


def current_keys(generated_mod: Path) -> set[str]:
    values = read_language_values(generated_mod / "Languages" / "ChineseSimplified")
    return set(values)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-root", type=Path, required=True)
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result: dict[str, dict[str, str]] = {}
    for mod_id, (reference_id, relative_language_path) in REFERENCE_SOURCES.items():
        generated = next(args.generated_root.glob(f"{mod_id} - * Chinese"), None)
        if generated is None:
            continue
        keys = current_keys(generated)
        candidates = read_language_values(
            args.reference_root / reference_id / relative_language_path
        )
        reviewed = {}
        for key, value in candidates.items():
            if key not in keys:
                continue
            normalized = build.normalize_display_names(build.local_translate(value))
            if usable_reference(normalized):
                reviewed[key] = normalized
        result[mod_id] = dict(sorted(reviewed.items()))
        print(f"{mod_id}: {len(reviewed)}/{len(keys)} keys imported")

    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
