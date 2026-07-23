"""Validate generated Aya Chinese localization packages before publication."""

from __future__ import annotations

import argparse
import collections
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import build_translations as build
from apply_race_names import KEY_OVERRIDES as CANONICAL_NAME_OVERRIDES

JAPANESE = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
FORBIDDEN_RELEASE_TEXT = (
    "鐢",
    "銈",
    "�",
    "人造竞赛",
    "人工比赛",
    "服装装",
    "衣服装",
    "克服装",
    "物理拟态",
    "太阳弧",
    "雷奎恩",
    "灵能敏感度",
    "精神敏感度",
    "精神灵敏度",
    "降低敏感度",
    "蕾奎恩",
    "雷奎恩",
    "每个季度",
    "Type A",
    "Type B",
    "原原本本地",
    "一般工作的工作速度",
    "弗如",
    "人鱼姬·人鱼姬",
    "女王种【女王种】",
    "舒舒服装",
    "情況",
    "Lv",
    "LV",
    "每季度",
    "每15日",
    "每2日",
    "縛刃",
    "憑剣",
    "魔槍",
    "夢杖",
    "墮狱",
    "ＯＣ式",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
    expected_key_values = {**build.KEY_OVERRIDES, **CANONICAL_NAME_OVERRIDES}
    xml_files = list(args.root.rglob("*.xml"))
    game_values = 0
    for file in xml_files:
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError as exc:
            errors.append(f"XML parse error: {file}: {exc}")
            continue
        is_game_language = "Languages" in file.parts
        for node in root.iter():
            value = node.text or ""
            if is_game_language and value:
                game_values += 1
                if JAPANESE.search(value):
                    errors.append(f"Japanese remains: {file}: {node.tag}: {value[:100]!r}")
                expected = expected_key_values.get(node.tag)
                if expected is not None and value.strip() != expected:
                    errors.append(
                        f"Canonical value mismatch: {file}: {node.tag}: "
                        f"{value.strip()!r} != {expected!r}"
                    )
            for forbidden in FORBIDDEN_RELEASE_TEXT:
                if forbidden in value:
                    errors.append(
                        f"Forbidden text {forbidden!r}: {file}: {node.tag}: {value[:100]!r}"
                    )

    # RimWorld 1.6 warns when dependency metadata contains only a packageId.
    # Keep these fields validated so a later rebuild cannot reintroduce the
    # empty display-name and missing Workshop-link warnings.
    for mod_id, fallback_name in build.MODS:
        generated = next(args.root.glob(f"{mod_id} - * Chinese"), None)
        if generated is None:
            errors.append(f"Generated package missing: {mod_id} - {fallback_name}")
            continue
        about_path = generated / "About" / "About.xml"
        try:
            about = ET.parse(about_path).getroot()
        except (ET.ParseError, OSError) as exc:
            errors.append(f"About.xml unavailable: {about_path}: {exc}")
            continue
        dependencies = about.findall("./modDependencies/li")
        if not dependencies:
            errors.append(f"Dependency missing: {about_path}")
            continue
        expected_url = f"steam://url/CommunityFilePage/{mod_id}"
        for dependency in dependencies:
            package_id = (dependency.findtext("packageId") or "").strip()
            display_name = (dependency.findtext("displayName") or "").strip()
            workshop_url = (dependency.findtext("steamWorkshopUrl") or "").strip()
            download_url = (dependency.findtext("downloadUrl") or "").strip()
            if not package_id:
                errors.append(f"Dependency packageId empty: {about_path}")
            if not display_name:
                errors.append(f"Dependency displayName empty: {about_path}")
            if not workshop_url and not download_url:
                errors.append(f"Dependency URL missing: {about_path}")
            if workshop_url and workshop_url != expected_url:
                errors.append(
                    f"Dependency Workshop URL mismatch: {about_path}: "
                    f"{workshop_url!r} != {expected_url!r}"
                )

    # The same Japanese source string must not acquire different Chinese
    # renderings merely because it occurs in another Aya package or Def type.
    translations_by_source: dict[str, set[str]] = collections.defaultdict(set)
    for mod_id, _ in build.MODS:
        generated = next(args.root.glob(f"{mod_id} - * Chinese"), None)
        source = build.WORKSHOP / mod_id
        if generated is None or not source.is_dir():
            continue
        output_values: dict[str, str] = {}
        language = generated / "Languages" / "ChineseSimplified"
        if language.is_dir():
            for file in language.rglob("*.xml"):
                for child in ET.parse(file).getroot():
                    output_values[child.tag] = (child.text or "").strip()

        defs = build.active_defs(source)
        if defs:
            for file in defs.rglob("*.xml"):
                try:
                    source_root = ET.parse(file).getroot()
                except ET.ParseError:
                    continue
                for definition in source_root:
                    def_name = (
                        build.text(definition.find("defName"))
                        or definition.get("Name", "")
                    )
                    if not def_name:
                        continue
                    for child in definition:
                        original = build.text(child)
                        key = f"{def_name}.{child.tag}"
                        if (
                            child.tag in build.FIELDS
                            and original
                            and key in output_values
                            and build.is_japanese(original)
                        ):
                            translations_by_source[original].add(output_values[key])

        for file in source.rglob("*.xml"):
            parts = {part.lower() for part in file.parts}
            if "languages" not in parts or "keyed" not in parts:
                continue
            try:
                source_root = ET.parse(file).getroot()
            except ET.ParseError:
                continue
            for child in source_root:
                original = build.text(child)
                if (
                    original
                    and child.tag in output_values
                    and build.is_japanese(original)
                ):
                    translations_by_source[original].add(output_values[child.tag])

    for original, translations in translations_by_source.items():
        if len(translations) > 1:
            errors.append(
                f"Inconsistent translation for {original!r}: {sorted(translations)!r}"
            )

    print(
        f"validated {len(xml_files)} XML files and {game_values} game-language values"
    )
    if errors:
        print("\n".join(errors))
        return 1
    print("validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
