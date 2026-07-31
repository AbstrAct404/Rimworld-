"""Generate translations for UI-visible Hediff stage labels.

RimWorld stores stage labels below ``HediffDef/stages/li/label``.  They are
not top-level fields, so the normal DefInjected generator does not collect
them.  Emit both DefInjected keys and direct runtime replacements because
some Aya health displays have previously bypassed DefInjected.
"""

from __future__ import annotations

import json
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import build_translations as build


ROOT = Path(__file__).parent
SOURCE = ROOT / "health_stage_translations.json"
SUPPLEMENTAL = ROOT / "supplemental"
MODS = ROOT / "Mods"
REPORT = ROOT / "HEALTH-STAGE-AUDIT.json"
NON_TEXT_STAGE = re.compile(r"(?:EN:)?\s*(?:Lv)?\d+(?:[％%])?", re.I)


def xml_write(path: Path, root: ET.Element) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def active_hediffs(mod_id: str) -> dict[str, ET.Element]:
    defs = build.active_defs(build.WORKSHOP / mod_id)
    result: dict[str, ET.Element] = {}
    if defs is None:
        return result
    for file in defs.rglob("*.xml"):
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        for definition in root:
            if definition.tag != "HediffDef":
                continue
            def_name = build.text(definition.find("defName"))
            if def_name:
                result[def_name] = definition
    return result


def meaningful_stage_labels(
    definitions: dict[str, ET.Element],
) -> dict[tuple[str, int], str]:
    result: dict[tuple[str, int], str] = {}
    for def_name, definition in definitions.items():
        stages = definition.find("stages")
        if stages is None:
            continue
        for index, stage in enumerate(stages):
            label = build.text(stage.find("label"))
            if label and not NON_TEXT_STAGE.fullmatch(label):
                result[(def_name, index)] = label
    return result


def package_for(mod_id: str) -> Path:
    matches = list(MODS.glob(f"{mod_id} - * Chinese"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected one generated package for {mod_id}: {matches}")
    return matches[0]


def main() -> None:
    translations = json.loads(SOURCE.read_text(encoding="utf-8"))
    report_items: list[dict[str, object]] = []
    missing: list[dict[str, object]] = []
    stale: list[dict[str, object]] = []
    generated = 0

    for mod_id, mapped_defs in translations.items():
        definitions = active_hediffs(mod_id)
        discovered = meaningful_stage_labels(definitions)
        mapped_keys = {
            (def_name, int(index))
            for def_name, stages in mapped_defs.items()
            for index in stages
        }
        for (def_name, index), source in sorted(discovered.items()):
            if (def_name, index) not in mapped_keys:
                missing.append(
                    {
                        "modId": mod_id,
                        "defName": def_name,
                        "stageIndex": index,
                        "source": source,
                    }
                )

        language = ET.Element("LanguageData")
        patch = ET.Element("Patch")
        for def_name, stages in mapped_defs.items():
            definition = definitions.get(def_name)
            source_stages = definition.find("stages") if definition is not None else None
            for index_text, item in stages.items():
                index = int(index_text)
                actual = ""
                if source_stages is not None and index < len(source_stages):
                    actual = build.text(source_stages[index].find("label"))
                expected = item["source"]
                translation = item["translation"]
                if actual != expected:
                    stale.append(
                        {
                            "modId": mod_id,
                            "defName": def_name,
                            "stageIndex": index,
                            "expectedSource": expected,
                            "actualSource": actual,
                        }
                    )
                    continue

                key = f"{def_name}.stages.{index}.label"
                ET.SubElement(language, key).text = translation

                xpath = (
                    f'Defs/HediffDef[defName="{def_name}"]'
                    f"/stages/li[{index + 1}]/label"
                )
                conditional = ET.SubElement(
                    patch, "Operation", {"Class": "PatchOperationConditional"}
                )
                ET.SubElement(conditional, "success").text = "Always"
                ET.SubElement(conditional, "xpath").text = xpath
                match = ET.SubElement(
                    conditional, "match", {"Class": "PatchOperationReplace"}
                )
                ET.SubElement(match, "xpath").text = xpath
                value = ET.SubElement(match, "value")
                ET.SubElement(value, "label").text = translation
                generated += 1

        supplemental_root = SUPPLEMENTAL / mod_id
        language_path = (
            supplemental_root
            / "Languages"
            / "ChineseSimplified"
            / "DefInjected"
            / "HediffDef"
            / "Aya_HealthStages.xml"
        )
        patch_path = (
            supplemental_root
            / "Patches"
            / f"{mod_id}_Aya_Health_Stage_Overrides.xml"
        )
        xml_write(language_path, language)
        xml_write(patch_path, patch)

        package = package_for(mod_id)
        package_language = (
            package
            / "Languages"
            / "ChineseSimplified"
            / "DefInjected"
            / "HediffDef"
            / language_path.name
        )
        package_patch = package / "Patches" / patch_path.name
        package_language.parent.mkdir(parents=True, exist_ok=True)
        package_patch.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(language_path, package_language)
        shutil.copy2(patch_path, package_patch)
        report_items.append(
            {
                "modId": mod_id,
                "stageLabels": len(mapped_keys),
                "languageFile": str(language_path.relative_to(ROOT)),
                "patchFile": str(patch_path.relative_to(ROOT)),
            }
        )

    report = {
        "generatedStageLabels": generated,
        "missingCount": len(missing),
        "staleCount": len(stale),
        "missing": missing,
        "stale": stale,
        "packages": report_items,
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if missing or stale:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
