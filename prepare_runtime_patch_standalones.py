"""Prepare Steam manifests for standalones affected by Aya runtime-patch fixes."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from build_translations import PUBLISHED_FILE_IDS, text, vdf_path, vdf_quote


MODS_ROOT = Path("Mods")
OUTPUT = Path("steam_upload") / "runtime-patches"
PUBLISH_ROOT = Path(r"D:\MODS\Rimworld")
ASCII_VDF_ROOT = Path(r"C:\Users\AA\Documents\AyaRaceZH\steam_upload\runtime-patches")
SKILL_PATCH = "Aya_Skill_Command_Translations.xml"
SCENARIO_PATCH = "Aya_Scenario_Translations.xml"
RUNTIME_LABEL_PATCH = "Aya_Runtime_Label_Overrides.xml"


def manifest(
    package: Path,
    published_id: str,
    title: str,
    description: str,
    changenote: str,
) -> str:
    publish_package = PUBLISH_ROOT / package.name
    return "\n".join(
        [
            '"workshopitem"',
            "{",
            '\t"appid"\t\t"294100"',
            f'\t"publishedfileid"\t\t"{published_id}"',
            f'\t"contentfolder"\t\t"{vdf_quote(vdf_path(publish_package))}"',
            f'\t"previewfile"\t\t"{vdf_quote(vdf_path(publish_package / "About" / "Preview.png"))}"',
            f'\t"title"\t\t"{vdf_quote(title)}"',
            f'\t"description"\t\t"{vdf_quote(description)}"',
            f'\t"changenote"\t\t"{vdf_quote(changenote)}"',
            "}",
            "",
        ]
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    affected: list[dict[str, object]] = []
    commands = ["@ShutdownOnFailedCommand 1", "@NoPromptForPassword 0"]

    for package in sorted(MODS_ROOT.glob("[0-9]* - * Chinese")):
        source_id = package.name.split(" ", 1)[0]
        if source_id not in PUBLISHED_FILE_IDS:
            continue
        skill = (package / "Patches" / SKILL_PATCH).is_file()
        scenario = (package / "Patches" / SCENARIO_PATCH).is_file()
        runtime_label = (package / "Patches" / RUNTIME_LABEL_PATCH).is_file()
        if not skill and not scenario and not runtime_label:
            continue
        published_id = PUBLISHED_FILE_IDS[source_id]
        about = ET.parse(package / "About" / "About.xml").getroot()
        title = text(about.find("name"))
        description = text(about.find("description"))
        if runtime_label:
            changenote = (
                "修复部分装备或武器名称在运行时回退为日文的问题；"
                "为确认会被兼容逻辑二次改写的 Def 增加简体中文标签兜底。"
                "其中包含种族切换后“无限之光”恢复为日文的问题。"
            )
        elif scenario:
            changenote = (
                "修复自定义技能补丁的字段定位与加载顺序，使技能名称和说明、"
                "种族剧本标题及专属开场信件实际生效。"
            )
        else:
            changenote = (
                "修复自定义技能补丁的字段定位与加载顺序，使技能名称和说明"
                "在 EX 扩展启用时仍能稳定显示为简体中文。"
            )
        default_name = f"{source_id}-{published_id}.vdf"
        localized_name = f"{source_id}-{published_id}-schinese.vdf"
        content = manifest(
            package, published_id, title, description, changenote
        )
        (OUTPUT / default_name).write_text(content, encoding="utf-8")
        (OUTPUT / localized_name).write_text(content, encoding="utf-8")
        commands.append(
            f'workshop_build_item "{vdf_path(ASCII_VDF_ROOT / default_name)}"'
        )
        affected.append(
            {
                "sourceId": source_id,
                "publishedId": published_id,
                "folder": package.name,
                "skillPatch": skill,
                "scenarioPatch": scenario,
                "runtimeLabelPatch": runtime_label,
                "defaultVdf": default_name,
                "schineseVdf": localized_name,
            }
        )

    commands.append("")
    (OUTPUT / "steamcmd_commands.txt").write_text(
        "\n".join(commands), encoding="utf-8"
    )
    (OUTPUT / "manifest.json").write_text(
        json.dumps(affected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "affectedPackages": len(affected),
                "output": str(OUTPUT),
                "manifest": str(OUTPUT / "manifest.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
