"""Apply the canonical Aya race and special-form names to maintained artifacts."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from build_translations import KEY_OVERRIDES as BUILD_KEY_OVERRIDES
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
    # Littluna's 決戦種 is an epithet for its intended battlefield role,
    # rather than the name of a separate race.
    "幼年决战种": "年幼的“决战种”",
    "年幼的决战种": "年幼的“决战种”",
    "一名伪神族会来到殖民地附近，并在数小时后因体力不支而倒下；届时可将其俘获并尝试招募。":
        "一名拥有强大却不稳定召唤能力的年幼伪神族会加入殖民地。她因长途跋涉而虚弱，可能很快因体力不支倒下；休息数天后即可恢复。",
    # Simplified-Chinese presentation and punctuation used in game-facing
    # equipment, item, recipe, and research names.
    "(魅魔)": "（魅魔）",
    "(幽灵姬)": "（幽灵姬）",
    "(亚人兽娘)": "（亚人兽娘）",
    "(牧菌妖姬)": "（牧菌妖姬）",
    "(人鱼姬)": "（人鱼姬）",
    "(伪神族)": "（伪神族）",
    "(耐久型)": "（耐久型）",
    "(突袭型)": "（突袭型）",
    "(标准型)": "（标准型）",
    "(夜魔)": "（夜魔）",
    "(人鱼)": "（人鱼）",
    "(亚人)": "（亚人）",
    "(异形)": "（异形）",
    "(龙人)": "（龙人）",
    "交換:": "交换：",
    "交换:": "交换：",
    "样品:XSE023": "样本：XSE023",
    "肖像种:再设计数据:Ａ": "肖像种：重设计数据 A",
    "肖像种:再设计数据:Ｂ": "肖像种：重设计数据 B",
    "肖像种:再设计数据:Ｃ": "肖像种：重设计数据 C",
    "肖像种:再设计数据:Ｄ": "肖像种：重设计数据 D",
    "肖像种:再设计数据:Ｅ": "肖像种：重设计数据 E",
    "ＯＣ式": "OC 式",
    "縛刃『盖斯特』": "缚刃「盖斯特」",
    "憑剣『拉尔夫』": "凭剑「拉尔夫」",
    "魔槍『勒盖耶』": "魔枪「勒盖耶」",
    "夢杖『荒猎』": "梦杖「荒猎」",
    "魑枪『郄浍墮狱』": "魑枪「郄浍堕狱」",
    # Natural RimWorld time terminology: quadrum=象限, day=天, year=年.
    "每季度可生产“单纤维长丝”60份。": "每个象限可产出 60 份“单纤维长丝”。",
    "每2日可生产8份奶。": "每 2 天可产出 8 份奶。",
    "每15日生成粒子泡提取核心。": "每 15 天产出一个“粒子泡提取核心”。",
    "每1年生成研究AI亚人格核心。": "每年产出一个“研究型 AI 次人格核心”。",
    "这个状态会在1天后解除。": "该状态会在 1 天后解除。",
    "1天内就会自我毁灭": "会在 1 天内自行消亡",
    "大约一年上升一级(Lv上限是5)": "大约每年提升 1 级（等级上限为 5）",
    "Lv大约每过一年就会上升1级（Lv上限为5）": "大约每年提升 1 级（等级上限为 5）",
    "大约一年会上升一级（LV上限为5）": "大约每年提升 1 级（等级上限为 5）",
    "大约1年提升1级（等级上限为10）": "大约每年提升 1 级（等级上限为 10）",
    "大约1年提升1级（等级上限为5）": "大约每年提升 1 级（等级上限为 5）",
    "大约1年提升1级（上限为5级）": "大约每年提升 1 级（等级上限为 5）",
    "大约1年提升1级（上限为5）": "大约每年提升 1 级（等级上限为 5）",
    "大约1年提升1级（Lv上限为5级）": "大约每年提升 1 级（等级上限为 5）",
    "约一年提升1级 (Lv上限为5)": "约每年提升 1 级（等级上限为 5）",
    "约两年提升1级 (Lv上限为5)": "约每两年提升 1 级（等级上限为 5）",
    "飞蛾姬的Lv等级": "飞蛾姬等级",
    "她们个人作为人工种族的Lv": "她们各自的人工种族等级",
    "她们个人作为库莉菈的Lv": "她们各自的库莉菈等级",
    "她们个人的Lv等级": "她们各自的幽灵姬等级",
    # Readability fixes found while reviewing special forms and item prose.
    "人鱼姬·人鱼姬·渊丛主": SPECIAL_FORMS["Xenoorca_b"],
    "女王种【女王种】": BASE_NAMES["Requeen"],
    "情況": "情况",
    "服装饰": "服装",
    "身体素质有显著地提升": "身体素质得到显著提升",
    "她们对所有的血肉都兴趣颇丰": "她们对所有血肉都兴趣浓厚",
    "需要消耗极巨量的时间和能量": "需要耗费极其漫长的时间和巨量能量",
    "受到灵体化的影响服装边缘变得破破烂烂": "受灵体化影响，服装边缘显得破旧残缺",
    "坚韧的躯体足以在抵挡攻击的同时灵活地进行移动，并用锋利的双爪粉碎敌人的神圣的魔像。":
        "这个神圣魔像拥有坚韧的躯体，既能承受攻击，又能灵活移动，并以锋利双爪粉碎敌人。",
    "坚韧的躯体足以在抵挡攻击的同时灵活地进行移动，并用锋利的双爪粉碎敌人。这个神圣魔像。":
        "这个神圣魔像拥有坚韧的躯体，既能承受攻击，又能灵活移动，并以锋利双爪粉碎敌人。",
    "被召唤出的巨型魔像将在一天后消失": "召唤出的巨型魔像会在一天后消失。",
    "专用的特殊构造的服装": "专用的特殊结构服装",
    "创造者为身为近卫的人鱼姬·渊丛主作为主要武器而制造的大枪":
        "创造者为担任近卫的人鱼姬·渊丛主打造的主战骑枪",
    "舒舒服装服装": "舒舒服服",
    "舒服装到": "舒服到",
    "由于魅魔是人工种族，特别针对精神干涉，所以对精神相关有很强的耐性，相反对人工生物或病毒等的抗性和免疫力很低。":
        "魅魔是针对精神干涉特化的人工种族，对精神影响有很强的抗性；相对地，她们对疾病、病毒等威胁的抵抗力和免疫力较低。",
    "另外，她们有自己的眷属，可以召唤出来让其与敌人战斗，其强度、召唤数根据她们各自的人工种族等级而定，约每年提升 1 级（等级上限为 5）。":
        "她们还可以召唤眷属协助战斗。眷属的强度和召唤数量取决于魅魔等级；魅魔等级约每年提升 1 级（等级上限为 5）。",
    "库莉菈是人工种族，作为统率各个人工种族的存在具有着相应的精神力。":
        "库莉菈是负责统率其他人工种族的人工种族，拥有与这一职责相称的强大精神力。",
    "另外，她们有着自己的眷属，可以召唤出来让其与敌人战斗，其强度、召唤数根据她们各自的库莉菈等级而定，约每两年提升 1 级（等级上限为 5）。":
        "她们还可以召唤眷属协助战斗。眷属的强度和召唤数量取决于库莉菈等级；库莉菈等级约每两年提升 1 级（等级上限为 5）。",
    "幽灵姬由于灵体性质原因，物理干扰需要先进的技术支持，所以工作效率较低，而且对疾病的抵抗力和免疫力低下。":
        "幽灵姬具有灵体性质，干涉现实物质需要借助先进技术，因此工作效率较低，对疾病的抵抗力和免疫力也较弱。",
    "但是她们每天都在不断的成长，一点点的克服自己的缺点，她们的强度取决于她们各自的幽灵姬等级，大约每年提升 1 级（等级上限为 5）。":
        "不过，她们会随着时间逐渐克服这些弱点。能力取决于幽灵姬等级，约每年提升 1 级（等级上限为 5）。",
    "飞蛾姬是一个人工创造的种族，经过改良后，她们可以很好地完成一般工作。特别是她们的手很灵巧，且可以将很远处物体的细节都看得一清二楚，是一个在简单工作方面非常优秀的种族。":
        "飞蛾姬是经过改良的人工种族，擅长各类基础劳动。她们双手灵巧、视力敏锐，即使相隔很远也能看清物体细节。",
    "性能取决于飞蛾姬等级，大约每年提升 1 级（等级上限为 5）。":
        "能力取决于飞蛾姬等级，约每年提升 1 级（等级上限为 5）。",
    "亚人兽娘是人工种族，重视通用性。可能因为是人工生物的缘故，她们对疾病的耐性很低，免疫力也不如常人。但是在编入基因的野生动物力量的影响下，会随着时间的推移逐渐克服这些弱点，且其强度取决于她们各自的人工种族等级（大约1年提升1级，上限为5）。":
        "亚人兽娘是注重通用性的人工种族。作为人工生命，她们对疾病的抵抗力和免疫力不如常人；但受植入体内的野生动物基因影响，这些弱点会随成长逐渐改善。能力取决于人工种族等级，约每年提升 1 级（等级上限为 5）。",
    "牧菌妖姬是人工种族，拥有堪比魅魔的精神强度的同时，身体素质也极为出色。":
        "牧菌妖姬是人工种族，既拥有堪比魅魔的精神强度，也具备出色的身体素质。",
    "另外。她们还可以召唤眷属、协助战斗；其召唤数取决于她们的牧菌等级——牧菌等级大约每年上升1级（上限为5级）。":
        "她们还可以召唤眷属协助战斗；召唤数量取决于牧菌等级，约每年提升 1 级（等级上限为 5）。",
    "能够无穷尽地生产机械生命体": "能够源源不断地生产机械生命体",
    "万一自身能量耗尽也能从周围迅速汲取，只有外在因素能导致她们的死亡。":
        "即使自身能量耗尽，她们也能迅速从周围汲取能量；只有外力才能真正杀死她们。",
    "受到了甚至连原初种都没残存的致命伤害": "遭受了足以令原初种彻底毁灭的致命损伤",
    "越多的近战攻击单位意外着需要有更多的远程射击单机进行压制":
        "投入的近战单位越多，就越需要更多远程射击单位进行压制",
    "只有匍匐于大地一途": "只能匍匐在地",
    "儿童校服装": "儿童学生服",
    "儿童款式异度服装": "儿童异度服",
    "幽鬼礼服装（幽灵姬）": "幽鬼礼服（幽灵姬）",
    "幽鬼护士服装（幽灵姬）": "幽鬼护士服（幽灵姬）",
    "幽鬼奴隶服装（幽灵姬）": "幽鬼奴隶服（幽灵姬）",
    "羽绒服装（亚人兽娘）": "羽绒服（亚人兽娘）",
    "巫女服装（魅魔）": "巫女服（人鱼姬）",
    "言语之服装A": "言语礼装 A",
    "言语之服装B": "言语礼装 B",
    "言语之服装C": "言语礼装 C",
    "血色的蜂蜜酒": "血色蜂蜜酒",
    "1级.夜潜猎手": "夜潜猎手（1级）",
    "等级2.夜潜猎手": "夜潜猎手（2级）",
    "等级3.夜潜猎手": "夜潜猎手（3级）",
    "等级4.夜潜猎手": "夜潜猎手（4级）",
    "等级5.夜潜猎手": "夜潜猎手（5级）",
    "1级.噩梦骇兽": "噩梦骇兽（1级）",
    "等级2.噩梦骇兽": "噩梦骇兽（2级）",
    "等级3.噩梦骇兽": "噩梦骇兽（3级）",
    "等级4.噩梦骇兽": "噩梦骇兽（4级）",
    "等级5.噩梦骇兽": "噩梦骇兽（5级）",
    "1级.永夜巨兽": "永夜巨兽（1级）",
    "等级2.永夜巨兽": "永夜巨兽（2级）",
    "等级3.永夜巨兽": "永夜巨兽（3级）",
    "等级4.永夜巨兽": "永夜巨兽（4级）",
    "等级5.永夜巨兽": "永夜巨兽（5级）",
    "据说这种药物的功效是由人工女巫种族魅魔·魔女系的成员阿克特拉创造的。":
        "这种灵药由魅魔·魔女系成员阿克忒拉调制。",
    "老实说，我不信任阿拉迪娅，所以我不想太依赖这个药。\n他们表面上很平静，但内心却在嘲笑别人。":
        "“说实话，我不信任阿拉迪娅，所以不想过分依赖这种药。她们表面平静，心里却不知在盘算什么。”",
    "据说这种药物的功效是由人工雌性狐狸亚人兽娘·维​​克斯玛丽斯 (亚人兽娘 维克森玛丽斯) 之一艾廷 (艾提涅) 创造的。":
        "这种魔药由亚人兽娘·维克森玛丽斯成员艾提涅调制。",
    "当其生效时，身体能力会提高，防御力也会增强。\n相反，它会变得脆弱并产生副作用。":
        "药效生效时，身体能力与防御力都会提升；副作用发作时，身体则会变得脆弱。",
    "药物本身的功效是有益的，用起来也不错。":
        "药效本身十分实用。",
    "Hello friend！": "你好，朋友！",
    "空间部落": "太空部落",
    "她们的体内存在着着创造者全部技术的结晶": "她们体内存在着创造者全部技术的结晶",
    "她们作为创造者灭亡时的保险，继承创造者们的职务成为了统括人工种族们的王":
        "她们是创造者为自身灭亡预留的保险，并继承其职责，成为统领人工种族的王",
    "但由于她们被创造出来的时候已是大战末期，研究仅仅停留在试验阶段的缘故":
        "但由于她们诞生时已是大战末期，相关研究仍停留在试验阶段",
    "尽管身体素质仅仅与人类相似，但她们能够行使的强大的王权机能却能够彻底地左右整个战局。":
        "尽管身体素质与人类相近，她们强大的王权机能仍足以左右整个战局。",
    "由于她拥有着强大的力量的同时，每天都在和染上了科幻色彩的机器打交道，因此请不要指望她能在殖民地的日常生活中有所贡献。":
        "她们虽拥有强大力量，却长期与高度复杂的机械打交道，因此并不擅长殖民地的日常劳动。",
    "最终取缔了其生产能力": "最终接管了她的生产能力",
    "其解决了困扰母鸟许久的能量问题": "这解决了困扰母鸟许久的能量问题",
    "不主动攻击它的话有可能直到它离开这颗星球都相安无事 。":
        "只要不主动攻击它，或许直到它离开这颗星球都能相安无事。",
    "放任这只继承了正统血脉的雏鸟成长的话": "若放任这只继承正统血脉的雏鸟成长",
    "魅魔的附庸，以凶猛的硬度而自豪，利用庞大的身躯给予对方无法反击的强力一击。":
        "魅魔召唤的眷属，拥有惊人的坚韧与庞大身躯，能以沉重一击压制敌人。",
    "被超乎人类认知的超能力者拯救的人，已经没有任何残骸和灵魂，无论如何也不可能恢复到原来的状态。":
        "被超越人类认知的存在“拯救”后，这具躯体已经失去肉身与灵魂，再也无法恢复原状。",
    "他只是在发呆，重复着留在体内的条件反射动作。":
        "它只会茫然地重复残留在躯体中的条件反射。",
    "只要一天的时间，它就无法再维持无魂的躯体，而自毁。":
        "一天后，它便无法继续维持这具无魂躯体，最终自行崩解。",
    "通过使缚刃「盖斯特」强化派生出来的一种高性能射击武器":
        "由缚刃「盖斯特」强化改造而来的高性能射击武器",
    "一种放大魅魔幻觉能力的投掷武器，威力很低但是有极强的幻觉作用，还可以分身可以对敌人进行连续的5次打击。":
        "一种放大魅魔幻觉能力的投掷武器。直接威力较低，却能造成强烈幻觉，并分裂为五道投影连续攻击目标。",
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
    # Etine is a Silkiera character name, not an Idearn alias.
    "HAR_NM_Hediff_Potency_b.label": "艾提涅魔药",
    "HAR_NM_Skill_Damage_b_d.label": "艾提涅魔药",
    "HAR_LL_Skill_MIKO_Damage_a.label": "你好，朋友！",
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
            # DefInjected XML commonly stores line breaks as the two literal
            # characters ``\n`` while JSON review sources may contain real
            # newlines.  Keep both representations synchronized.
            if "\n" in source:
                new = new.replace(
                    source.replace("\n", "\\n"),
                    target.replace("\n", "\\n"),
                )
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
    # A prose cleanup pass can turn this legacy alias into an identity entry;
    # retain only the useful misspelling-to-canonical mapping.
    terms.pop("索拉克服装", None)
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
            "索拉克服装饰": "索拉克服装",
        }
    )
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def override_language_keys() -> None:
    # Build-time editorial overrides contain the reviewed equipment, item,
    # relic, and fixed-name translations.  Apply them to the checked-in
    # packages as well, then let the canonical race/special-form names below
    # take precedence where both maps contain the same key.
    game_overrides = {**BUILD_KEY_OVERRIDES, **KEY_OVERRIDES}
    for path in (ROOT / "Mods").rglob("Languages/ChineseSimplified/**/*.xml"):
        root = ET.parse(path).getroot()
        changed = False
        for node in root:
            value = game_overrides.get(node.tag)
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
