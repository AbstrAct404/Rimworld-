"""Audit Japanese ThingDef labels/descriptions against Chinese packages."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from build_translations import MODS, WORKSHOP, active_defs


MODS_ROOT = Path("Mods")
REPORT = Path("EQUIPMENT-ITEM-AUDIT.json")
JAPANESE = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")


def load_thing_translations(package: Path) -> dict[str, str]:
    translations: dict[str, str] = {}
    root = package / "Languages" / "ChineseSimplified" / "DefInjected" / "ThingDef"
    for file in sorted(root.glob("*.xml")):
        language_data = ET.parse(file).getroot()
        for node in language_data:
            translations[node.tag] = (node.text or "").strip()
    return translations


def main() -> None:
    checked = 0
    missing: list[dict[str, str]] = []
    residual: list[dict[str, str]] = []

    for mod_id, mod_name in MODS:
        package = next(MODS_ROOT.glob(f"{mod_id} - * Chinese"), None)
        defs = active_defs(WORKSHOP / mod_id)
        if package is None or defs is None:
            continue
        translations = load_thing_translations(package)
        for file in sorted(defs.rglob("*.xml")):
            try:
                root = ET.parse(file).getroot()
            except ET.ParseError:
                continue
            for definition in root.findall("ThingDef"):
                def_name = (definition.findtext("defName") or "").strip()
                if not def_name:
                    continue
                for field in ("label", "description"):
                    source = (definition.findtext(field) or "").strip()
                    if not source or not JAPANESE.search(source):
                        continue
                    checked += 1
                    key = f"{def_name}.{field}"
                    translated = translations.get(key)
                    item = {
                        "modId": mod_id,
                        "mod": mod_name,
                        "defName": def_name,
                        "field": field,
                    }
                    if translated is None:
                        missing.append(item)
                    elif JAPANESE.search(translated):
                        residual.append(item | {"translation": translated})

    data = {
        "checkedJapaneseThingDefFields": checked,
        "missingCount": len(missing),
        "japaneseResidualCount": len(residual),
        "missing": missing,
        "japaneseResidual": residual,
    }
    REPORT.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    if missing or residual:
        raise SystemExit("equipment/item translation audit failed")


if __name__ == "__main__":
    main()
