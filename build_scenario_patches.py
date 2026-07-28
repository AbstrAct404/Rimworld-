"""Build direct Aya scenario patches and bespoke opening-dialog translations.

ScenarioDef labels can be injected through DefInjected, but their nested
``scenario.summary`` and ``ScenPart_GameStartDialog.textKey`` are not.  The
source scenarios used the base-game ``GameStartDialog`` key, which presents
the three-colonist crashlanded letter even for their one-pawn starts.  Patch
the full definition and give each scenario its own keyed opening text.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from build_translations import MODS, WORKSHOP, active_defs, text, xml_write


MODS_ROOT = Path("Mods")
PATCH_NAME = "Aya_Scenario_Translations.xml"
KEYED_NAME = "Aya_Scenarios.xml"

# Canonical display translations.  These names follow terminology.json and
# are intentionally shared by the selector, scenario description and opening
# letter.
SCENARIOS = {
    "Nearmaere_Scenario": {
        "label": "魅魔的夜曲",
        "description": "魅魔的专属剧本",
        "start_key": "AyaScenarioStartNearmare",
        "start_text": "你在休眠舱中被警报和船体撕裂声惊醒。飞船解体前，你勉强登上逃生舱。\n\n短暂漂流后，你降落在这颗未知的边缘世界。\n\n残骸散落在身边。现在，作为一名魅魔，你必须在这片土地上开辟自己的生存之路。",
    },
    "Xenoorca_Scenario": {
        "label": "人鱼姬剧本",
        "description": "人鱼姬的专属剧本",
        "start_key": "AyaScenarioStartXenoorca",
        "start_text": "你在休眠舱中被警报和船体撕裂声惊醒。飞船解体前，你勉强登上逃生舱。\n\n短暂漂流后，你降落在这颗未知的边缘世界。\n\n残骸散落在身边。现在，作为一名人鱼姬，你必须在这片土地上开辟自己的生存之路。",
    },
    "Silkiera_Scenario": {
        "label": "亚人兽娘剧本",
        "description": "亚人兽娘的专属剧本",
        "start_key": "AyaScenarioStartSilkiera",
        "start_text": "你在休眠舱中被警报和船体撕裂声惊醒。飞船解体前，你勉强登上逃生舱。\n\n短暂漂流后，你降落在这颗未知的边缘世界。\n\n残骸散落在身边。现在，作为一名亚人兽娘，你必须在这片土地上开辟自己的生存之路。",
    },
    "Neclose_Scenario": {
        "label": "牧菌妖姬剧本",
        "description": "牧菌妖姬的专属剧本",
        "start_key": "AyaScenarioStartNeclose",
        "start_text": "你在休眠舱中被警报和船体撕裂声惊醒。飞船解体前，你勉强登上逃生舱。\n\n短暂漂流后，你降落在这颗未知的边缘世界。\n\n残骸散落在身边。现在，作为一名牧菌妖姬，你必须在这片土地上开辟自己的生存之路。",
    },
    "Chaoura_Scenario": {
        "label": "混沌灵剧本",
        "description": "混沌灵的专属剧本",
        "start_key": "AyaScenarioStartChaoura",
        "start_text": "你在休眠舱中被警报和船体撕裂声惊醒。飞船解体前，你勉强登上逃生舱。\n\n短暂漂流后，你降落在这颗未知的边缘世界。\n\n残骸散落在身边。现在，作为一名混沌灵，你必须在这片土地上开辟自己的生存之路。",
    },
}


def add_replace(operations: ET.Element, xpath: str, tag: str, value: str) -> None:
    op = ET.SubElement(operations, "li", {"Class": "PatchOperationReplace"})
    ET.SubElement(op, "xpath").text = xpath
    replacement = ET.SubElement(op, "value")
    ET.SubElement(replacement, tag).text = value


def main() -> None:
    generated: list[dict[str, str]] = []
    missing: list[str] = []
    for mod_id, _ in MODS:
        source = WORKSHOP / mod_id
        defs = active_defs(source)
        package = next(MODS_ROOT.glob(f"{mod_id} - * Chinese"), None)
        if defs is None or package is None:
            continue
        about = ET.parse(source / "About" / "About.xml").getroot()
        package_id = text(about.find("packageId"))
        found: list[str] = []
        for file in defs.rglob("*.xml"):
            try:
                root = ET.parse(file).getroot()
            except ET.ParseError:
                continue
            for definition in root.findall("ScenarioDef"):
                def_name = text(definition.find("defName"))
                if def_name in SCENARIOS:
                    found.append(def_name)
        if not found:
            continue

        patch = ET.Element("Patch")
        keyed = ET.Element("LanguageData")
        for def_name in found:
            data = SCENARIOS[def_name]
            base = f'Defs/ScenarioDef[defName="{def_name}"]'
            conditional = ET.SubElement(
                patch, "Operation", {"Class": "PatchOperationConditional"}
            )
            ET.SubElement(conditional, "success").text = "Always"
            # PatchOperationFindMod matches the source mod's display name,
            # not its packageId.  Aya's display names have changed between
            # releases, which made these patches silently skip.  Testing the
            # actual target Def is stable and remains safe in the integrated
            # optional-dependency package.
            ET.SubElement(conditional, "xpath").text = base
            sequence = ET.SubElement(
                conditional, "match", {"Class": "PatchOperationSequence"}
            )
            operations = ET.SubElement(sequence, "operations")
            add_replace(operations, base + "/label", "label", data["label"])
            add_replace(operations, base + "/description", "description", data["description"])
            add_replace(operations, base + "/scenario/summary", "summary", data["start_text"])
            add_replace(
                operations,
                base + '/scenario/parts/li[def="GameStartDialog"]/textKey',
                "textKey",
                data["start_key"],
            )
            ET.SubElement(keyed, data["start_key"]).text = data["start_text"]
            generated.append({
                "modId": mod_id,
                "packageId": package_id,
                "scenarioDef": def_name,
                "label": data["label"],
                "startKey": data["start_key"],
            })
        patch_path = package / "Patches" / PATCH_NAME
        xml_write(patch_path, patch)
        keyed_path = package / "Languages" / "ChineseSimplified" / "Keyed" / KEYED_NAME
        keyed_path.parent.mkdir(parents=True, exist_ok=True)
        xml_write(keyed_path, keyed)

    Path("SCENARIO-AUDIT.json").write_text(
        json.dumps({"scenarioCount": len(generated), "scenarios": generated, "missing": missing}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if missing:
        raise SystemExit("scenario definitions missing: " + ", ".join(missing))
    print(json.dumps({"scenarioCount": len(generated), "report": "SCENARIO-AUDIT.json"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
