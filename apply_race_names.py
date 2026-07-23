"""Apply the canonical Aya race and special-form names to maintained artifacts."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from build_translations import write_readme


ROOT = Path(__file__).parent

BASE_NAMES = {
    "Saclean": "飞蛾姬",
    "Idhale": "幽灵姬",
    "Silkiera": "亚人兽娘",
    "Sikiera": "亚人兽娘",
    "Nearmare": "魅魔",
    "Chaoura": "混沌灵",
    "Neclose": "牧菌妖姬",
    "Solark": "索拉克（龙姬）",
    "Xenoorca": "人鱼姬",
    "Littluna": "伪神族",
    "Eveliet": "伊娃莉特",
    "Qualeela": "库莉菈",
    "Zoichor": "锢魂魔",
    "Idearn": "伊迪安",
    "Requeen": "女王种",
}

SPECIAL_FORMS = {
    "Idhale_b": "幽灵姬·罪孽灵",
    "Silkiera_b": "亚人兽娘·改良种",
    "Silkiera_c": "亚人兽娘·狐媚",
    "Nearmare_b": "魅魔·信仰系",
    "Nearmare_c": "魅魔·魔女系",
    "Nearmare_d": "魅魔·神秘系",
    "Nearmare_e": "魅魔·改良系",
    "Chaoura_z": "混沌灵·阿瓦露其安",
    "Neclose_b": "牧菌妖姬·无人（界外之血）",
    "Solark_b": "索拉克·赫雷勒夫",
    "Xenoorca_leader": "人鱼姬·渊丛主",
    "Xenoorca_b": "人鱼姬·渊丛主",
    "Littluna_b": "伪神族·伊迪亚之奴",
    "Littluna_c": "伪神族·杜娜米丝",
    "Qualeela_b": "库莉菈·凯特尔",
    "Idearn_Charmides": "伊迪安·卡尔米德",
    "Idearn_Menexenus": "伊迪安·梅涅克赛努",
    "Idearn_Theaetetus": "伊迪安·泰阿泰德",
    "Idearn_Critias": "伊迪安·克里提亚斯（焚书模型）",
    "Requeen_b": "女王种（要塞）",
    "Requeen_G": "远渡星海之鸟",
    "Requeen_Z": "雏鸟",
}

# Longest and most specific replacements must run first.
TEXT_REPLACEMENTS = {
    "蕾奎恩·克里提亚斯": SPECIAL_FORMS["Requeen_Z"],
    "蕾奎恩（要塞）": SPECIAL_FORMS["Requeen_b"],
    "蕾奎恩(要塞)": SPECIAL_FORMS["Requeen_b"],
    "蕾奎恩": BASE_NAMES["Requeen"],
    "伊迪安·克里提亚斯": SPECIAL_FORMS["Idearn_Critias"],
    "伊迪安·墨涅克塞诺斯": SPECIAL_FORMS["Idearn_Menexenus"],
    "伊迪安·泰阿泰托斯": SPECIAL_FORMS["Idearn_Theaetetus"],
    "伊迪安·卡尔米德斯": SPECIAL_FORMS["Idearn_Charmides"],
    "墨涅克塞诺斯": "梅涅克赛努",
    "梅内克塞诺斯": "梅涅克赛努",
    "美涅克塞努": "梅涅克赛努",
    "泰阿泰托斯": "泰阿泰德",
    "泰阿泰特斯": "泰阿泰德",
    "卡尔米德斯": "卡尔米德",
    "卡米德斯": "卡尔米德",
    "涅克洛斯·乌提斯福尼亚": SPECIAL_FORMS["Neclose_b"],
    "涅克洛斯·「无人」": SPECIAL_FORMS["Neclose_b"],
    "查欧拉·阿瓦齐翁": SPECIAL_FORMS["Chaoura_z"],
    "尼亚梅尔·阿拉迪亚": SPECIAL_FORMS["Nearmare_c"],
    "尼亚梅尔·温盖特": SPECIAL_FORMS["Nearmare_d"],
    "尼亚梅尔·涅墨塞亚": SPECIAL_FORMS["Nearmare_e"],
    "索拉克·海勒莱夫": SPECIAL_FORMS["Solark_b"],
    "人鱼族·海迪尔诺亚": SPECIAL_FORMS["Xenoorca_b"],
    "莉特露娜·伊迪亚之奴": SPECIAL_FORMS["Littluna_b"],
    "莉特露娜·杜娜米丝": SPECIAL_FORMS["Littluna_c"],
    "夸莉拉·凯特尔": SPECIAL_FORMS["Qualeela_b"],
    "夸莉拉·吉娜斯": BASE_NAMES["Qualeela"],
    "伊德海尔·罪孽灵": SPECIAL_FORMS["Idhale_b"],
    "希尔基耶拉·改良种": SPECIAL_FORMS["Silkiera_b"],
    "希尔基耶拉·狐媚": SPECIAL_FORMS["Silkiera_c"],
    "尼亚梅尔·信仰系": SPECIAL_FORMS["Nearmare_b"],
    "阿瓦齐翁": "阿瓦露其安",
    "阿拉迪亚": SPECIAL_FORMS["Nearmare_c"],
    "温盖特": SPECIAL_FORMS["Nearmare_d"],
    "涅墨塞亚": SPECIAL_FORMS["Nearmare_e"],
    "涅墨西娅": SPECIAL_FORMS["Nearmare_e"],
    "乌提斯福尼亚": "无人（界外之血）",
    "海迪尔诺亚": SPECIAL_FORMS["Xenoorca_b"],
    "海达诺亚": SPECIAL_FORMS["Xenoorca_b"],
    "人鱼族": BASE_NAMES["Xenoorca"],
    "噬菌妖姬": BASE_NAMES["Neclose"],
    "海勒莱夫": "赫雷勒夫",
    "达那米斯": "杜娜米丝",
    "迪纳米斯": "杜娜米丝",
    "萨克琳": BASE_NAMES["Saclean"],
    "伊德海尔": BASE_NAMES["Idhale"],
    "希尔基耶拉": BASE_NAMES["Silkiera"],
    "尼亚梅尔": BASE_NAMES["Nearmare"],
    "查欧拉": BASE_NAMES["Chaoura"],
    "涅克洛斯": BASE_NAMES["Neclose"],
    "泽诺奥卡": BASE_NAMES["Xenoorca"],
    "莉特露娜": BASE_NAMES["Littluna"],
    "艾维利特": BASE_NAMES["Eveliet"],
    "夸莉拉": BASE_NAMES["Qualeela"],
}

MOD_FORMS = {
    "2198830432": [
        BASE_NAMES["Nearmare"],
        SPECIAL_FORMS["Nearmare_b"],
        SPECIAL_FORMS["Nearmare_e"],
        SPECIAL_FORMS["Nearmare_d"],
        SPECIAL_FORMS["Nearmare_c"],
    ],
    "2216916011": [BASE_NAMES["Xenoorca"], SPECIAL_FORMS["Xenoorca_leader"]],
    "2227425882": [BASE_NAMES["Idhale"], SPECIAL_FORMS["Idhale_b"]],
    "2233666290": [
        BASE_NAMES["Silkiera"],
        SPECIAL_FORMS["Silkiera_b"],
        SPECIAL_FORMS["Silkiera_c"],
    ],
    "2394460334": [BASE_NAMES["Neclose"], SPECIAL_FORMS["Neclose_b"]],
    "2504657401": [
        BASE_NAMES["Requeen"],
        SPECIAL_FORMS["Requeen_b"],
        SPECIAL_FORMS["Requeen_G"],
        SPECIAL_FORMS["Requeen_Z"],
    ],
    "2569091688": [
        BASE_NAMES["Littluna"],
        SPECIAL_FORMS["Littluna_b"],
        SPECIAL_FORMS["Littluna_c"],
    ],
    "2608237489": [BASE_NAMES["Solark"], SPECIAL_FORMS["Solark_b"]],
    "2676302514": [BASE_NAMES["Saclean"]],
    "2763078885": [BASE_NAMES["Qualeela"], SPECIAL_FORMS["Qualeela_b"]],
    "2871413100": [
        BASE_NAMES["Idearn"],
        SPECIAL_FORMS["Idearn_Charmides"],
        SPECIAL_FORMS["Idearn_Menexenus"],
        SPECIAL_FORMS["Idearn_Theaetetus"],
        SPECIAL_FORMS["Idearn_Critias"],
    ],
    "2946679071": [BASE_NAMES["Chaoura"], SPECIAL_FORMS["Chaoura_z"], BASE_NAMES["Zoichor"]],
    "3153539856": [BASE_NAMES["Eveliet"]],
}

KEY_OVERRIDES = {
    "HAR_Idhale_b.label": SPECIAL_FORMS["Idhale_b"],
    "HAR_Idhale_b_Player.label": SPECIAL_FORMS["Idhale_b"],
    "HAR_Silkiera_b.label": SPECIAL_FORMS["Silkiera_b"],
    "HAR_Silkiera_c.label": SPECIAL_FORMS["Silkiera_c"],
    "HAR_Silkiera_NPC_Resident_b.label": SPECIAL_FORMS["Silkiera_b"],
    "HAR_Silkiera_NPC_Resident_c.label": SPECIAL_FORMS["Silkiera_c"],
    "HAR_Nearmaere_b.label": SPECIAL_FORMS["Nearmare_b"],
    "HAR_Nearmaere_c.label": SPECIAL_FORMS["Nearmare_c"],
    "HAR_Nearmaere_d.label": SPECIAL_FORMS["Nearmare_d"],
    "HAR_Nearmaere_e.label": SPECIAL_FORMS["Nearmare_e"],
    "HAR_CO_Race_Chaoura_z.label": SPECIAL_FORMS["Chaoura_z"],
    "HAR_Neclose_b.label": SPECIAL_FORMS["Neclose_b"],
    "HAR_Neclose_KindBase_NPC_b.label": SPECIAL_FORMS["Neclose_b"],
    "HAR_Neclose_NPC_b_Leader.label": SPECIAL_FORMS["Neclose_b"],
    "HAR_Neclose_NPC_b_Resident.label": SPECIAL_FORMS["Neclose_b"],
    "HAR_Solark_b.label": SPECIAL_FORMS["Solark_b"],
    "HAR_Solark_KindBase_NPC_b.label": SPECIAL_FORMS["Solark_b"],
    "HAR_Solark_NPC_Resident_b.label": SPECIAL_FORMS["Solark_b"],
    "HAR_Xenoorca_NPC_Leader.label": SPECIAL_FORMS["Xenoorca_leader"],
    "HAR_Xenoorca_b.label": SPECIAL_FORMS["Xenoorca_b"],
    "HAR_Littluna_b.label": SPECIAL_FORMS["Littluna_b"],
    "HAR_Littluna_c.label": SPECIAL_FORMS["Littluna_c"],
    "HAR_Qualeela.label": BASE_NAMES["Qualeela"],
    "HAR_Qualeela_b.label": SPECIAL_FORMS["Qualeela_b"],
    "HAR_Idearn_Critias.label": SPECIAL_FORMS["Idearn_Critias"],
    "HAR_IA_Item_spawn_Critias.label": SPECIAL_FORMS["Idearn_Critias"],
    "BOSS_RQ_Incident_Requeen.label": BASE_NAMES["Requeen"],
    "BOSS_RQ_Incident_Requeen.letterLabel": BASE_NAMES["Requeen"],
    "BOSS_RQ_Incident_Requeen_b.label": SPECIAL_FORMS["Requeen_b"],
    "BOSS_RQ_Incident_Requeen_b.letterLabel": SPECIAL_FORMS["Requeen_b"],
    "BOSS_RQ_Incident_Requeen_G.label": SPECIAL_FORMS["Requeen_G"],
    "BOSS_RQ_Incident_Requeen_G.letterLabel": SPECIAL_FORMS["Requeen_G"],
    "BOSS_RQ_Incident_Requeen_Gone_Error.label": SPECIAL_FORMS["Requeen_G"],
    "BOSS_RQ_Incident_Requeen_Gone_Error.letterLabel": SPECIAL_FORMS["Requeen_G"],
    "BOSS_RQ_Incident_Requeen_Z.label": SPECIAL_FORMS["Requeen_Z"],
    "BOSS_RQ_Incident_Requeen_Z.letterLabel": SPECIAL_FORMS["Requeen_Z"],
    "BOSS_RQ_Hive_Requeen.label": BASE_NAMES["Requeen"],
    "BOSS_RQ_Hive_Requeen_b.label": SPECIAL_FORMS["Requeen_b"],
    "BOSS_RQ_Hive_Requeen_Z.label": SPECIAL_FORMS["Requeen_Z"],
}

INCIDENT_KEYS = {
    key: value
    for key, value in KEY_OVERRIDES.items()
    if key.startswith("BOSS_RQ_Incident_Requeen")
}


def replace_text_files() -> None:
    extensions = {".py", ".json", ".xml", ".md", ".txt"}
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or ".git" in path.parts
            or "steam_upload" in path.parts
            or path.name in {Path(__file__).name, "validate_translations.py"}
            or path.suffix.lower() not in extensions
        ):
            continue
        old = path.read_text(encoding="utf-8")
        critias_token = "__AYA_IDEARN_CRITIAS_MODEL__"
        new = old.replace(
            SPECIAL_FORMS["Idearn_Critias"] + "（焚书模型）",
            SPECIAL_FORMS["Idearn_Critias"],
        ).replace(SPECIAL_FORMS["Idearn_Critias"], critias_token)
        for source, target in TEXT_REPLACEMENTS.items():
            new = new.replace(source, target)
        new = new.replace(critias_token, SPECIAL_FORMS["Idearn_Critias"])
        if new != old:
            path.write_text(new, encoding="utf-8")


def update_terminology() -> None:
    path = ROOT / "terminology.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    races = data["race_names"]
    old_canonical = {
        "Saclean": {"萨克琳", "萨克林", "飞蛾姬"},
        "Idhale": {"伊德海尔", "伊德哈尔", "爱得乐", "幽灵姬"},
        "Silkiera": {"希尔基耶拉", "丝基拉", "亚人兽娘"},
        "Nearmare": {"尼亚梅尔", "尼亚美亚", "尼亚美", "魅魔"},
        "Chaoura": {"查欧拉", "查乌拉", "混沌灵"},
        "Neclose": {"涅克洛斯", "奈克洛斯", "牧菌妖姬", "弑菌姬"},
        "Xenoorca": {"泽诺奥卡", "异兽卡", "人鱼姬"},
        "Littluna": {"莉特露娜", "利特鲁纳", "利托鲁纳", "伪神族"},
        "Eveliet": {"艾维利特", "艾芙莉特", "艾维利托", "伊娃莉特"},
        "Qualeela": {"夸莉拉", "夸利拉", "库莉菈"},
        "Idearn": {"伊迪安", "伊迪恩", "艾迪安", "艾蒂安"},
        "Solark": {"索拉克", "龙姬", "索拉克（龙姬）"},
        "Requeen": {"蕾奎恩", "雷奎恩", "女王种", "女王物种"},
    }
    for english, aliases in old_canonical.items():
        target = BASE_NAMES[english]
        for alias in aliases | {english}:
            races[alias] = target
    races["Sikiera"] = BASE_NAMES["Silkiera"]
    races["Zoichor"] = BASE_NAMES["Zoichor"]
    races[BASE_NAMES["Zoichor"]] = BASE_NAMES["Zoichor"]
    data["special_forms"] = SPECIAL_FORMS

    terms = data["game_terms"]
    terms.update(
        {
            "Silkira": BASE_NAMES["Silkiera"],
            "Niamea": BASE_NAMES["Nearmare"],
            "Niamere": BASE_NAMES["Nearmare"],
            "Litoruna": BASE_NAMES["Littluna"],
            "Ritorina": BASE_NAMES["Littluna"],
            "Litluna": BASE_NAMES["Littluna"],
            "Idohale": BASE_NAMES["Idhale"],
            "Idheir": BASE_NAMES["Idhale"],
            "Idhair": BASE_NAMES["Idhale"],
            "Keiora": BASE_NAMES["Chaoura"],
            "Avarzion": "阿瓦露其安",
            "Avalzion": "阿瓦露其安",
            "Utisphonia": "无人（界外之血）",
            "Dunamis": "杜娜米丝",
            "Charmides": "卡尔米德",
            "Menexenos": "梅涅克赛努",
            "Theaetetus": "泰阿泰德",
            "Theaetetos": "泰阿泰德",
            "Zoichor": BASE_NAMES["Zoichor"],
            "Ivrit": BASE_NAMES["Eveliet"],
            "Ivrito": BASE_NAMES["Eveliet"],
            "Sacleans": BASE_NAMES["Saclean"],
            "Requeen": BASE_NAMES["Requeen"],
        }
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def override_language_keys() -> None:
    for path in (ROOT / "Mods").rglob("Languages/ChineseSimplified/**/*.xml"):
        root = ET.parse(path).getroot()
        changed = False
        for node in root:
            value = KEY_OVERRIDES.get(node.tag)
            if value and node.text != value:
                node.text = value
                changed = True
        is_requeen = "2504657401 - Requeen Boss Chinese" in path.parts
        if path.parent.name == "IncidentDef" and not is_requeen:
            for node in list(root):
                if node.tag in INCIDENT_KEYS:
                    root.remove(node)
                    changed = True
        if path.name == "Aya_Translated.xml" and path.parent.name == "IncidentDef" and is_requeen:
            present = {node.tag for node in root}
            for key, value in INCIDENT_KEYS.items():
                if key not in present:
                    ET.SubElement(root, key).text = value
                    changed = True
        if changed:
            ET.indent(root, space="  ")
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def update_about_and_readmes() -> None:
    for package in sorted((ROOT / "Mods").glob("* Chinese")):
        mod_id = package.name.split(" - ", 1)[0]
        about_path = package / "About" / "About.xml"
        root = ET.parse(about_path).getroot()
        forms = MOD_FORMS.get(mod_id)
        if forms:
            marker = "【收录种族与特殊形态】"
            description = (root.findtext("description") or "").strip()
            if marker in description:
                description = description.split(marker, 1)[0].rstrip()
            description += "\n\n" + marker + "\n" + "\n".join(f"・{name}" for name in forms)
            root.find("description").text = description
            ET.indent(root, space="  ")
            ET.ElementTree(root).write(about_path, encoding="utf-8", xml_declaration=True)
        write_readme(package, mod_id, root)


def main() -> None:
    replace_text_files()
    update_terminology()
    override_language_keys()
    update_about_and_readmes()


if __name__ == "__main__":
    main()
