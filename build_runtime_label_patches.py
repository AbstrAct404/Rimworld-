"""Generate direct label fallbacks for Aya defs changed again during startup.

Some Aya defs are touched by runtime compatibility code after normal
DefInjected localization is loaded.  Their descriptions remain translated,
but their labels can fall back to the Japanese source text.  A small,
reviewed allow-list keeps these labels stable without replacing every
ThingDef label in the supported mods.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from build_translations import xml_write


MODS_ROOT = Path("Mods")
OUTPUT_NAME = "Aya_Runtime_Label_Overrides.xml"

# Defs observed in startup/runtime compatibility logs or reported in game.
TARGETS = {
    "2198830432": ["Gun_AssaultRifle_NM", "HAR_NM_Wear_y"],
    "2233666290": ["Gun_AssaultRifle_SK"],
    "2394460334": ["HAR_NC_Armor_b"],
    "2946679071": [
        "HAR_CO_Apparel_Head_c",
        "HAR_CO_Apparel_Shell_a",
        "HAR_CO_Apparel_Tops_z",
        "HAR_CO_Weapon_UB",
    ],
    "3153539856": ["HAR_EL_Apparel_Shell_c", "HAR_EL_Apparel_Tops_a"],
}


def load_labels(package: Path) -> dict[str, str]:
    labels: dict[str, str] = {}
    root = package / "Languages" / "ChineseSimplified" / "DefInjected" / "ThingDef"
    for file in sorted(root.glob("*.xml")):
        language_data = ET.parse(file).getroot()
        for node in language_data:
            if node.tag.endswith(".label") and node.text:
                labels[node.tag.removesuffix(".label")] = node.text.strip()
    return labels


def main() -> None:
    generated: list[dict[str, str]] = []
    for mod_id, def_names in TARGETS.items():
        package = next(MODS_ROOT.glob(f"{mod_id} - * Chinese"), None)
        if package is None:
            raise SystemExit(f"translation package missing for {mod_id}")
        labels = load_labels(package)
        missing = [def_name for def_name in def_names if def_name not in labels]
        if missing:
            raise SystemExit(
                f"{package.name}: missing ThingDef labels: {', '.join(missing)}"
            )

        patch = ET.Element("Patch")
        for def_name in def_names:
            label = labels[def_name]
            base = f'Defs/ThingDef[defName="{def_name}"]'
            conditional = ET.SubElement(
                patch, "Operation", {"Class": "PatchOperationConditional"}
            )
            ET.SubElement(conditional, "success").text = "Always"
            ET.SubElement(conditional, "xpath").text = base
            replace = ET.SubElement(
                conditional, "match", {"Class": "PatchOperationReplace"}
            )
            ET.SubElement(replace, "xpath").text = base + "/label"
            value = ET.SubElement(replace, "value")
            ET.SubElement(value, "label").text = label
            generated.append(
                {"modId": mod_id, "defName": def_name, "label": label}
            )

        patch_path = package / "Patches" / OUTPUT_NAME
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        xml_write(patch_path, patch)

    Path("RUNTIME-LABEL-PATCH-REPORT.json").write_text(
        json.dumps(
            {"generatedOperations": len(generated), "operations": generated},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "generatedOperations": len(generated),
                "report": "RUNTIME-LABEL-PATCH-REPORT.json",
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
