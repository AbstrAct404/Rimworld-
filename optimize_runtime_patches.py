"""Remove legacy duplicate patch bundles without reducing runtime coverage.

The repository previously consolidated every runtime fallback for a package
into ``<workshop-id>_Aya_Localization.xml``. Newer generators maintain the
skill, scenario and runtime-label patches separately. Keeping both layouts
causes the same XPath to be replaced twice.

This migration first restores the maintained supplemental health/gene
fallbacks, then removes a legacy bundle only when every modification target
in it is still covered by another direct runtime patch. It therefore removes
duplicate execution, but never relies on DefInjected as a replacement for a
runtime fallback.
"""

from __future__ import annotations

import json
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


MODS_ROOT = Path("Mods")
SUPPLEMENTAL_ROOT = Path("supplemental")
REPORT_PATH = Path("RUNTIME-PATCH-OPTIMIZATION.json")
MODIFIER_CLASSES = {
    "PatchOperationReplace",
    "PatchOperationAdd",
    "PatchOperationRemove",
}


def modification_targets(file: Path) -> list[str]:
    targets: list[str] = []
    root = ET.parse(file).getroot()
    for node in root.iter():
        if node.get("Class") not in MODIFIER_CLASSES:
            continue
        xpath = (node.findtext("xpath") or "").strip()
        if xpath:
            targets.append(xpath)
    return targets


def package_patch_index(package: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    patch_root = package / "Patches"
    if not patch_root.is_dir():
        return {}
    for file in sorted(patch_root.glob("*.xml")):
        for xpath in modification_targets(file):
            index[xpath].append(file.name)
    return dict(index)


def sync_supplemental_patches(package: Path, mod_id: str) -> list[str]:
    source = SUPPLEMENTAL_ROOT / mod_id / "Patches"
    if not source.is_dir():
        return []
    destination = package / "Patches"
    destination.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for file in sorted(source.glob("*.xml")):
        shutil.copy2(file, destination / file.name)
        copied.append(file.name)
    return copied


def main() -> None:
    report: list[dict[str, object]] = []
    for package in sorted(MODS_ROOT.glob("[0-9]* - * Chinese")):
        mod_id = package.name.split(" ", 1)[0]
        if mod_id == "0000000000":
            continue

        copied = sync_supplemental_patches(package, mod_id)
        before = package_patch_index(package)
        before_targets = set(before)
        before_operations = sum(len(files) for files in before.values())

        legacy = package / "Patches" / f"{mod_id}_Aya_Localization.xml"
        removed_legacy = False
        if legacy.is_file():
            legacy_targets = set(modification_targets(legacy))
            replacement_targets: set[str] = set()
            for file in sorted((package / "Patches").glob("*.xml")):
                if file == legacy:
                    continue
                replacement_targets.update(modification_targets(file))
            missing = sorted(legacy_targets - replacement_targets)
            if missing:
                raise RuntimeError(
                    f"{package.name}: refusing to remove {legacy.name}; "
                    f"{len(missing)} runtime targets would lose fallback coverage: "
                    + ", ".join(missing[:5])
                )
            legacy.unlink()
            removed_legacy = True

        after = package_patch_index(package)
        after_targets = set(after)
        after_operations = sum(len(files) for files in after.values())
        if before_targets != after_targets:
            missing = sorted(before_targets - after_targets)
            added = sorted(after_targets - before_targets)
            raise RuntimeError(
                f"{package.name}: runtime target set changed unexpectedly; "
                f"missing={missing[:5]}, added={added[:5]}"
            )
        duplicates = {
            xpath: files for xpath, files in after.items() if len(files) > 1
        }
        if duplicates:
            sample = next(iter(duplicates.items()))
            raise RuntimeError(
                f"{package.name}: duplicate runtime target remains: "
                f"{sample[0]} in {', '.join(sample[1])}"
            )

        report.append(
            {
                "modId": mod_id,
                "package": package.name,
                "supplementalFilesSynced": copied,
                "legacyBundleRemoved": removed_legacy,
                "runtimeTargets": len(after_targets),
                "operationsBefore": before_operations,
                "operationsAfter": after_operations,
                "coveragePreserved": before_targets == after_targets,
            }
        )

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "packagesChecked": len(report),
                "legacyBundlesRemoved": sum(
                    bool(item["legacyBundleRemoved"]) for item in report
                ),
                "operationsBefore": sum(
                    int(item["operationsBefore"]) for item in report
                ),
                "operationsAfter": sum(
                    int(item["operationsAfter"]) for item in report
                ),
                "runtimeTargets": sum(
                    int(item["runtimeTargets"]) for item in report
                ),
                "report": str(REPORT_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
