"""Validate generated Aya Chinese localization packages before publication."""

from __future__ import annotations

import argparse
import collections
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import build_translations as build

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
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()

    errors: list[str] = []
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
            for forbidden in FORBIDDEN_RELEASE_TEXT:
                if forbidden in value:
                    errors.append(
                        f"Forbidden text {forbidden!r}: {file}: {node.tag}: {value[:100]!r}"
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
