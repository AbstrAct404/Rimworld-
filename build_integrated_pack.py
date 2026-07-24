"""Build one optional Aya Simplified Chinese language pack from all standalones.

The integrated package deliberately uses ``loadAfter`` rather than mandatory
Workshop dependencies, matching the reference pack's "install only the races
you use" behavior.  Duplicate language keys are merged deterministically and
reported for review.
"""

from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

import build_translations as build


INTEGRATED_FOLDER = "0000000000 - Aya Integrated Chinese"
PACKAGE_ID = "abstract404.aya.integrated.zh"
PUBLISHED_FILE_ID = "3770548798"


def read_about(package: Path) -> tuple[str, str]:
    root = ET.parse(package / "About" / "About.xml").getroot()
    original_id = package.name.split(" ", 1)[0]
    dependency = build.text(root.find("./modDependencies/li/packageId"))
    return original_id, dependency


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mods-root", type=Path, default=Path("Mods"))
    parser.add_argument("--steam-vdf-dir", type=Path)
    args = parser.parse_args()

    mods_root = args.mods_root
    output = mods_root / INTEGRATED_FOLDER
    if output.exists():
        shutil.rmtree(output)
    (output / "About").mkdir(parents=True)

    packages = sorted(
        package
        for package in mods_root.glob("[0-9]* - * Chinese")
        if package.name != INTEGRATED_FOLDER
        and (package / "Languages" / "ChineseSimplified").is_dir()
    )
    load_after: list[str] = []
    package_info: list[dict[str, object]] = []
    # (section, subtype) -> key -> (value, source ID)
    buckets: dict[tuple[str, str], dict[str, tuple[str, str]]] = defaultdict(dict)
    conflicts: list[dict[str, str]] = []

    for package in packages:
        original_id, dependency = read_about(package)
        if dependency and dependency not in load_after:
            load_after.append(dependency)
        entry_count = 0
        language_root = package / "Languages" / "ChineseSimplified"
        for file in sorted(language_root.rglob("*.xml")):
            relative = file.relative_to(language_root)
            if len(relative.parts) < 2:
                continue
            section, subtype = relative.parts[0], relative.parts[1]
            if section not in {"DefInjected", "Keyed"}:
                continue
            if section == "Keyed":
                subtype = "Keyed"
            try:
                root = ET.parse(file).getroot()
            except ET.ParseError:
                continue
            bucket = buckets[(section, subtype)]
            for child in root:
                value = build.text(child)
                if not value:
                    continue
                entry_count += 1
                previous = bucket.get(child.tag)
                if previous and previous[0] != value:
                    conflicts.append({
                        "key": child.tag,
                        "keptValue": previous[0],
                        "keptFrom": previous[1],
                        "ignoredValue": value,
                        "ignoredFrom": original_id,
                    })
                    continue
                bucket[child.tag] = (value, original_id)
        package_info.append({
            "originalWorkshopId": original_id,
            "folder": package.name,
            "entriesRead": entry_count,
        })

    included_lines = []
    for item in package_info:
        original_id = str(item["originalWorkshopId"])
        standalone_id = build.PUBLISHED_FILE_IDS.get(original_id)
        display_name = str(item["folder"]).removeprefix(
            f"{original_id} - "
        ).removesuffix(" Chinese")
        if standalone_id and standalone_id != "0":
            included_lines.append(
                f"・{display_name}\n"
                f"https://steamcommunity.com/sharedfiles/filedetails/?id={standalone_id}"
            )
        else:
            included_lines.append(f"・{display_name}（尚未发布独立汉化）")

    written = 0
    for (section, subtype), values in sorted(buckets.items()):
        root = ET.Element("LanguageData")
        for key, (value, _source_id) in sorted(values.items()):
            ET.SubElement(root, key).text = value
            written += 1
        if section == "DefInjected":
            destination = (
                output
                / "Languages"
                / "ChineseSimplified"
                / "DefInjected"
                / subtype
                / "Aya_Integrated.xml"
            )
        else:
            destination = (
                output
                / "Languages"
                / "ChineseSimplified"
                / "Keyed"
                / "Aya_Integrated.xml"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        build.xml_write(destination, root)

    about = ET.Element("ModMetaData")
    description = (
        "Aya 人工种族系列简体中文整合汉化包。\n\n"
        "可只安装自己使用的原模组，无需安装整合包支持的全部种族。"
        "请将本汉化置于所有 Aya 原模组之后加载；不要与对应的独立汉化包同时启用。\n\n"
        f"当前收录 {len(packages)} 个原模组，共合并 {written} 条游戏文本。\n\n"
        "【收录的独立汉化及链接】\n"
        + "\n".join(included_lines)
        + "\n\n"
        "——\n兼容版本：RimWorld 1.6\n"
        "本模组仅含翻译文件，不包含任何原模组资源。"
    )
    for tag, value in [
        ("name", "[Aya] 人工种族简体中文整合汉化包 v1.6"),
        ("author", "AbstrAct404 / Chinese localization"),
        ("packageId", PACKAGE_ID),
        ("description", description),
    ]:
        ET.SubElement(about, tag).text = value
    supported = ET.SubElement(about, "supportedVersions")
    ET.SubElement(supported, "li").text = "1.6"
    load_after_node = ET.SubElement(about, "loadAfter")
    for dependency in load_after:
        ET.SubElement(load_after_node, "li").text = dependency
    build.xml_write(output / "About" / "About.xml", about)
    preview_source = (
        mods_root
        / "3505571618 - Aya Premise Core Chinese"
        / "About"
        / "Preview.png"
    )
    if preview_source.is_file():
        shutil.copy2(preview_source, output / "About" / "Preview.png")

    readme = "\n".join([
        "# [Aya] 人工种族简体中文整合汉化包 v1.6",
        "",
        description,
        "",
        "## 收录内容",
        *included_lines,
        "",
        "## 使用说明",
        "- 只需安装实际使用的 Aya 原模组。",
        "- 将本整合汉化放在全部 Aya 原模组之后。",
        "- 不要与对应的独立汉化包同时启用。",
        "",
    ])
    (output / "README.md").write_text(readme, encoding="utf-8")
    report = {
        "packageId": PACKAGE_ID,
        "includedPackages": package_info,
        "uniqueEntriesWritten": written,
        "conflictCount": len(conflicts),
        "conflicts": conflicts,
    }
    (output / "BUILD-REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    standalone_report = [
        {
            "id": item["originalWorkshopId"],
            "name": str(item["folder"]).removeprefix(
                f"{item['originalWorkshopId']} - "
            ).removesuffix(" Chinese"),
            "status": "present",
            "entries": item["entriesRead"],
            "path": str(mods_root / str(item["folder"])),
        }
        for item in package_info
    ]
    (mods_root / "BUILD-REPORT.json").write_text(
        json.dumps(standalone_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if args.steam_vdf_dir:
        args.steam_vdf_dir.mkdir(parents=True, exist_ok=True)
        title = build.text(about.find("name"))
        for language, suffix in (("english", ""), ("schinese", "-schinese")):
            content = "\n".join([
                '"workshopitem"', "{",
                '\t"appid"\t\t"294100"',
                f'\t"publishedfileid"\t\t"{PUBLISHED_FILE_ID}"',
                f'\t"language"\t\t"{language}"',
                f'\t"contentfolder"\t\t"{build.vdf_quote(build.vdf_path(output))}"',
                f'\t"previewfile"\t\t"{build.vdf_quote(build.vdf_path(output / "About" / "Preview.png"))}"',
                f'\t"title"\t\t"{build.vdf_quote(title)}"',
                f'\t"description"\t\t"{build.vdf_quote(description)}"',
                '\t"changenote"\t\t"首次发布：收录 Aya 系列简体中文整合汉化。"',
                "}", "",
            ])
            (
                args.steam_vdf_dir
                / f"aya-integrated-{PUBLISHED_FILE_ID}{suffix}.vdf"
            ).write_text(content, encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "packages": len(packages),
        "entries": written,
        "conflicts": len(conflicts),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
