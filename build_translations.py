"""Build standalone Chinese translation mods for the local Aya race Workshop mods.

The script intentionally reads source mods only and writes translation overlays.  It
uses RimWorld's DefInjected format, so it neither copies nor changes game assets.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

WORKSHOP = Path(r"D:\SteamLibrary\steamapps\workshop\content\294100")

MODS = [
    ("2946679071", "Chaoura Race"), ("3505571618", "Aya Premise Core"),
    ("3153539856", "Eveliet Race"), ("2954714860", "Idea Storyteller"),
    ("2871413100", "Idearn Race"), ("3223846919", "Idhale EX"),
    ("2227425882", "Idhale Race"), ("3223847068", "Littluna EX"),
    ("2569091688", "Littluna Race"), ("3223847765", "Nearmare EX"),
    ("2198830432", "Nearmare Race"), ("2394460334", "Neclose Race"),
    ("3223844717", "Neclose EX"), ("2763078885", "Qualeela Race"),
    ("2504657401", "Requeen Boss"), ("2676302514", "Saclean Race"),
    ("3223847242", "Silkiera EX"), ("2233666290", "Silkiera Race"),
    ("3223847402", "Solark EX"), ("2608237489", "Solark Race"),
    ("3223847562", "Xenoorca EX"), ("2216916011", "Xenoorca Race"),
]

FIELDS = {
    "label", "labelNoun", "labelMale", "labelFemale", "description", "jobString",
    "gerundLabel", "pawnSingular", "pawnPlural", "customLabel", "letterLabel",
    "letterText", "deathMessage", "beginLetter", "endLetter", "reportString",
    "ingestCommandString", "ingestReportString", "gerundLabel", "labelShort",
    "title", "titleShort", "fixedName",
}

# Proper nouns used consistently across this family.  General Japanese text is
# translated remotely when --translate-google is requested.
GLOSSARY = {
    "チャウラ": "查欧拉", "エヴェリエット": "艾维利特", "イデアーン": "伊迪恩",
    "イデール": "伊德尔", "リトルナ": "莉特露娜", "ニアメア": "尼亚梅尔",
    "ネクロース": "涅克洛斯", "クアリーラ": "夸莉拉", "リクイーン": "利奎恩",
    "サクリーン": "萨克琳", "シルキエラ": "希尔基耶拉", "ソラーク": "索拉克",
    "ゼノオルカ": "泽诺奥卡", "人工種族": "人工种族", "種族": "种族",
    "服": "服装", "武器": "武器", "防具": "护甲", "作業": "工作",
}

# A deliberately obfuscated source label cannot be translated reliably by an
# automatic service; use the established race name and a readable designation.
KEY_OVERRIDES = {
    "HAR_LL_Hive_Critias.label": "莉特露娜蜂巢·克里蒂亚斯",
    # Idhale EX: Tzvaot Shekinah — divine presence/glory of the hosts.
    "HAR_IH_Hediff_EX_a.label": "万军神临",
    "HAR_IH_Hediff_EX_b.label": "万军神临",
    "HAR_IH_Hediff_EX_c.label": "万军神临",
    "HAR_IH_Hediff_EX_d.label": "万军神临",
    "HAR_IH_Hediff_EX_e.label": "万军神临",
    # Idhale relic names: use their source-language meanings instead of katakana.
    "HAR_IH_Item_a.label": "辉耀之石",
    "HAR_IH_Archotech_a.label": "天穹之钥",
    # Biotech terminology: translate the concepts rather than preserving the
    # Japanese katakana names (Bereshit / Ishmutit / Akasha Wear).
    "Aya_Race_Gene_a.label": "创世基因",
    "Aya_Race_Xenotype.label": "人工族",
    "HAR_IH_AT_z.label": "以太礼装",
    # Idhale terminology: keep race/faction display names consistent, including
    # fixedName (which RimWorld displays instead of the FactionDef label).
    "HAR_Idhale.label": "伊德海尔",
    "HAR_Idhale_b.label": "伊德海尔·阿冯·鲁阿赫",
    "HAR_Idhale_b_Player.label": "伊德海尔·阿冯·鲁阿赫",
    "Idhale_P_Faction.pawnSingular": "伊德海尔人",
    "Idhale_Faction_NPC.pawnSingular": "伊德海尔人",
    "Idhale_Faction_NPC_b.pawnSingular": "伊德海尔人",
    "Idhale_Faction_NPC_b.fixedName": "苍穹之魂",
    "HAR_IH_Cultures_b.label": "苍穹之魂教义",
    "HAR_IH_Backstory_b_C1.title": "造物主遗物",
    "HAR_IH_Backstory_b_C1.titleShort": "造物主遗物",
    "HAR_IH_Backstory_b_A1.title": "旧世神灵",
    "HAR_IH_Backstory_b_A1.titleShort": "旧世神灵",
}
MISSING_STUBS = {"3223844717": ("Ayameduki.HARNecloseEX", ["1.5", "1.6"])}


def text(element: ET.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def package_id(mod: Path) -> str:
    about = mod / "About" / "About.xml"
    root = ET.parse(about).getroot()
    return text(root.find("packageId"))


def versions(mod: Path) -> list[str]:
    return sorted(p.name for p in mod.iterdir() if p.is_dir() and re.fullmatch(r"1\.\d+", p.name))


def active_defs(mod: Path) -> Path | None:
    available = versions(mod)
    if not available:
        return mod / "Defs" if (mod / "Defs").is_dir() else None
    latest = "1.6" if "1.6" in available else available[-1]
    folder = mod / latest / "Defs"
    return folder if folder.is_dir() else None


def is_japanese(value: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u31f0-\u31ff]", value))


def local_translate(value: str) -> str:
    for source, target in GLOSSARY.items():
        value = value.replace(source, target)
    return value


def google_translate(values: list[str], cache: dict[str, str]) -> dict[str, str]:
    """Translate unique Japanese values concurrently with a conservative worker cap."""
    pending = [v for v in values if v not in cache and is_japanese(v)]
    def request(value: str) -> tuple[str, str]:
        query = urllib.parse.urlencode({"client": "gtx", "sl": "ja", "tl": "zh-CN", "dt": "t", "q": value})
        url = "https://translate.googleapis.com/translate_a/single?" + query
        try:
            with urllib.request.urlopen(url, timeout=12) as response:
                data = json.load(response)
            translated = "".join(part[0] for part in data[0] if part and part[0])
            return value, translated or local_translate(value)
        except Exception:
            return value, local_translate(value)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for index, (value, translated) in enumerate(executor.map(request, pending), 1):
            cache[value] = translated
            if index % 100 == 0:
                print(f"  translated {index}/{len(pending)}")
    return cache


def xml_write(path: Path, root: ET.Element) -> None:
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def build_one(mod_id: str, fallback_name: str, destination: Path, translate_google: bool, cache: dict[str, str]) -> dict:
    source = WORKSHOP / mod_id
    if not source.is_dir():
        original_id, supported_versions = MISSING_STUBS[mod_id]
        out = destination / f"{mod_id} - {fallback_name} Chinese"
        if out.exists():
            shutil.rmtree(out)
        (out / "About").mkdir(parents=True)
        about = ET.Element("ModMetaData")
        for tag, value in [
            ("name", f"[ZH] {fallback_name}"),
            ("author", "AbstrAct404 / Chinese localization"),
            ("packageId", f"abstract404.aya.{mod_id}.zh"),
            ("description", f"[Aya] {fallback_name} 的简体中文本地化占位包。需加载原模组。"),
        ]:
            ET.SubElement(about, tag).text = value
        supported = ET.SubElement(about, "supportedVersions")
        for version in supported_versions:
            ET.SubElement(supported, "li").text = version
        deps = ET.SubElement(about, "modDependencies")
        dep = ET.SubElement(deps, "li")
        ET.SubElement(dep, "packageId").text = original_id
        load_after = ET.SubElement(about, "loadAfter")
        ET.SubElement(load_after, "li").text = original_id
        xml_write(out / "About" / "About.xml", about)
        (out / "README.md").write_text(
            "源创意工坊目录当前未安装；此空壳 EX 模组没有可提取的 Def。\\n"
            "依赖 packageId 根据同系列命名规则预填，安装源模组后请进行一次游戏内验证。\\n",
            encoding="utf-8",
        )
        return {"id": mod_id, "name": fallback_name, "status": "stub built (source unavailable)", "entries": 0, "path": str(out)}
    original_id = package_id(source)
    out_name = f"[ZH] {fallback_name}"
    out = destination / f"{mod_id} - {fallback_name} Chinese"
    if out.exists():
        shutil.rmtree(out)
    (out / "About").mkdir(parents=True)
    about = ET.Element("ModMetaData")
    for tag, value in [
        ("name", out_name), ("author", "AbstrAct404 / Chinese localization"),
        ("packageId", f"abstract404.aya.{mod_id}.zh"),
        ("description", f"[Aya] {fallback_name} 的简体中文本地化。\n需加载原模组；本模组仅含翻译文件，不包含原模组资源。"),
    ]:
        ET.SubElement(about, tag).text = value
    supported = ET.SubElement(about, "supportedVersions")
    for version in versions(source) or ["1.6"]:
        ET.SubElement(supported, "li").text = version
    deps = ET.SubElement(about, "modDependencies")
    dep = ET.SubElement(deps, "li")
    ET.SubElement(dep, "packageId").text = original_id
    load_after = ET.SubElement(about, "loadAfter")
    ET.SubElement(load_after, "li").text = original_id
    xml_write(out / "About" / "About.xml", about)
    (out / "README.md").write_text(
        f"# {out_name}\n\n原模组创意工坊 ID：{mod_id}\n\n加载顺序：原模组在前，本汉化在后。\n",
        encoding="utf-8",
    )

    defs = active_defs(source)
    collected: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    keyed: dict[str, list[tuple[str, str]]] = defaultdict(list)
    if defs:
        for file in defs.rglob("*.xml"):
            try:
                root = ET.parse(file).getroot()
            except ET.ParseError:
                continue
            for definition in root:
                def_name = text(definition.find("defName"))
                if not def_name:
                    continue
                for child in definition:
                    if child.tag in FIELDS and text(child):
                        collected[definition.tag].append((def_name, child.tag, text(child)))
    # Some releases keep UI messages under Languages directly (rather than in
    # Defs). Include every supplied Keyed XML file as a Chinese keyed overlay.
    for file in source.rglob("*.xml"):
        parts = {part.lower() for part in file.parts}
        if "languages" not in parts or "keyed" not in parts:
            continue
        try:
            root = ET.parse(file).getroot()
        except ET.ParseError:
            continue
        for child in root:
            if text(child):
                keyed[file.name].append((child.tag, text(child)))
    values = [value for entries in collected.values() for _, _, value in entries]
    values += [value for entries in keyed.values() for _, value in entries]
    if translate_google:
        google_translate(list(dict.fromkeys(values)), cache)
    written = 0
    for def_type, entries in collected.items():
        language = ET.Element("LanguageData")
        seen = set()
        for def_name, field, original in entries:
            key = f"{def_name}.{field}"
            if key in seen:
                continue
            seen.add(key)
            translated = KEY_OVERRIDES.get(key, cache.get(original, local_translate(original)))
            # Do not write an English duplicate: the base game can supply it.
            if translated == original and not is_japanese(original):
                continue
            ET.SubElement(language, key).text = translated
            written += 1
        if len(language):
            folder = out / "Languages" / "ChineseSimplified" / "DefInjected" / def_type
            folder.mkdir(parents=True, exist_ok=True)
            xml_write(folder / "Aya_Translated.xml", language)
    for file_name, entries in keyed.items():
        language = ET.Element("LanguageData")
        seen = set()
        for key, original in entries:
            if key in seen:
                continue
            seen.add(key)
            translated = cache.get(original, local_translate(original))
            if translated == original and not is_japanese(original):
                continue
            ET.SubElement(language, key).text = translated
            written += 1
        if len(language):
            folder = out / "Languages" / "ChineseSimplified" / "Keyed"
            folder.mkdir(parents=True, exist_ok=True)
            xml_write(folder / file_name, language)
    return {"id": mod_id, "name": fallback_name, "status": "built", "entries": written, "path": str(out)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--translate-google", action="store_true")
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    cache_file = args.destination / ".translation-cache.json"
    cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    # Earlier generator revisions used a failed batch format.  Remove those
    # Japanese fallbacks so they are translated correctly on this run.
    cache = {source: target for source, target in cache.items() if not is_japanese(target)}
    report = [build_one(mid, name, args.destination, args.translate_google, cache) for mid, name in MODS]
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    (args.destination / "BUILD-REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
