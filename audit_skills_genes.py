"""Audit Aya skill and gene UI text against the installed source mods.

The report is intentionally read-only.  It checks top-level AbilityDef,
GeneDef and XenotypeDef text by exact DefInjected key, then checks nested
commandLabel/commandDesc fields (custom comp gizmos) by definition and count.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from build_translations import MODS, WORKSHOP, active_defs, is_japanese, text


MODS_ROOT = Path("Mods")
TOP_LEVEL_TYPES = {"AbilityDef", "GeneDef", "XenotypeDef"}
TOP_LEVEL_FIELDS = {"label", "description"}
NESTED_FIELDS = {
    "commandLabel",
    "commandDesc",
    "CommandLabel",
    "CommandDesc",
    "AutoLabel",
    "AutoDesc",
}


def translation_values(mod_id: str) -> dict[str, list[str]]:
    package = next(MODS_ROOT.glob(f"{mod_id} - * Chinese"), None)
    values: dict[str, list[str]] = {}
    if package is None:
        return values
    language_root = package / "Languages" / "ChineseSimplified"
    for file in language_root.rglob("*.xml"):
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        for node in root:
            if text(node):
                values.setdefault(node.tag, []).append(text(node))
    for file in (package / "Patches").rglob("*.xml"):
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        for index, operation in enumerate(
            root.findall('.//li[@Class="PatchOperationReplace"]')
            + root.findall('.//match[@Class="PatchOperationReplace"]')
        ):
            xpath = text(operation.find("xpath"))
            def_match = re.search(
                r"""\[(?:defName|@Name)=(?:"([^"]+)"|'([^']+)')\]""",
                xpath,
            )
            field_match = re.search(
                r"/(commandLabel|commandDesc|CommandLabel|CommandDesc|"
                r"AutoLabel|AutoDesc)(?:\[\d+\])?$",
                xpath,
            )
            if not def_match or not field_match:
                continue
            def_name = def_match.group(1) or def_match.group(2)
            field = field_match.group(1)
            translated = text(operation.find(f"./value/{field}"))
            if translated:
                values.setdefault(
                    f"{def_name}.patch{index}.{field}", []
                ).append(translated)
    return values


def main() -> None:
    missing: list[dict[str, object]] = []
    untranslated: list[dict[str, object]] = []
    checked = 0
    checked_by_type: dict[str, int] = {}

    for mod_id, mod_name in MODS:
        source = WORKSHOP / mod_id
        defs = active_defs(source)
        if defs is None:
            continue
        translated = translation_values(mod_id)
        for file in defs.rglob("*.xml"):
            try:
                root = ET.parse(file).getroot()
            except ET.ParseError:
                continue
            for definition in root:
                def_name = text(definition.find("defName")) or definition.get("Name", "")
                if not def_name:
                    continue

                if definition.tag in TOP_LEVEL_TYPES:
                    for child in definition:
                        if child.tag not in TOP_LEVEL_FIELDS or not text(child):
                            continue
                        checked += 1
                        category = f"{definition.tag}.{child.tag}"
                        checked_by_type[category] = checked_by_type.get(category, 0) + 1
                        key = f"{def_name}.{child.tag}"
                        candidates = translated.get(key, [])
                        item = {
                            "modId": mod_id,
                            "mod": mod_name,
                            "defType": definition.tag,
                            "defName": def_name,
                            "field": child.tag,
                            "source": text(child),
                            "key": key,
                            "file": str(file),
                        }
                        if not candidates:
                            missing.append(item)
                        elif any(is_japanese(value) for value in candidates):
                            untranslated.append({**item, "translations": candidates})

                nested_sources: dict[str, set[str]] = {}
                for node in definition.iter():
                    if node.tag in NESTED_FIELDS and text(node):
                        nested_sources.setdefault(node.tag, set()).add(text(node))
                for field, sources in nested_sources.items():
                    source_count = len(sources)
                    checked += source_count
                    category = {
                        "commandLabel": "CustomCommand.label",
                        "commandDesc": "CustomCommand.description",
                        "CommandLabel": "CustomSummon.manualLabel",
                        "CommandDesc": "CustomSummon.manualDescription",
                        "AutoLabel": "CustomSummon.autoLabel",
                        "AutoDesc": "CustomSummon.autoDescription",
                    }[field]
                    checked_by_type[category] = (
                        checked_by_type.get(category, 0) + source_count
                    )
                    matching = [
                        value
                        for key, values in translated.items()
                        if key.startswith(f"{def_name}.") and key.endswith(f".{field}")
                        for value in values
                    ]
                    if len(matching) < source_count:
                        missing.append({
                            "modId": mod_id,
                            "mod": mod_name,
                            "defType": definition.tag,
                            "defName": def_name,
                            "field": field,
                            "sourceCount": source_count,
                            "translatedCount": len(matching),
                            "sources": sorted(sources),
                            "file": str(file),
                        })
                    if any(is_japanese(value) for value in matching):
                        untranslated.append({
                            "modId": mod_id,
                            "mod": mod_name,
                            "defType": definition.tag,
                            "defName": def_name,
                            "field": field,
                            "translations": matching,
                            "file": str(file),
                        })

    report = {
        "checkedValues": checked,
        "checkedByType": checked_by_type,
        "missingCount": len(missing),
        "untranslatedCount": len(untranslated),
        "missing": missing,
        "untranslated": untranslated,
    }
    Path("SKILL-GENE-AUDIT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "checkedValues": checked,
        "checkedByType": checked_by_type,
        "missingCount": len(missing),
        "untranslatedCount": len(untranslated),
        "report": "SKILL-GENE-AUDIT.json",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
