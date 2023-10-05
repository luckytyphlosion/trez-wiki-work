import json
import functools

import enemy_drops
from mystery_data import MysteryDataParser5


PAGE_HEADER = """\
{{nw|TODO: Add info and improve template.}}

Locations of BattleChips in [[Mega Man Battle Network 5]]. Due to the removed areas, some chips are distributed differently between the Japanese and international versions.
"""

CHIPS_HEADER = """\
{| class="wikitable sortable"
!ID||Name||! class="wikitable unsortable" | Locations || Traders
"""

NO_TRADER_CHIPS_HEADER = """\
{| class="wikitable sortable"
!ID||Name||! class="wikitable unsortable" | Locations
"""

CHIP_LOCATION_TEMPLATE_PART_1 = """\
{{{{ChipLocation
|id={id}
|name={name}
"""

DUMMY_LOCATION_TEXT = "TODO"

HIGSBYS_TRADER_TEXT = ""
HALL_TRADER_TEXT = ""
OLD_MINE_TRADER_TEXT = ""
BUGFRAG_TRADER_TEXT = ""

def convert_v2_format_to_v1(bn5_chips_v2):
    bn5_chips = []

    for v2_chip_full in bn5_chips_v2["results"].values():
        v2_chip = v2_chip_full["printouts"]
        chip = {
            "name": {
                "en": v2_chip["name"][0]
            },
            "codes": "".join(v2_chip["codes"]),
            "index": v2_chip["index"][0],
            "section": v2_chip["section"][0].lower()
        }

        v2_version_list = v2_chip["version"]
        if len(v2_version_list) != 0:
            v2_version = v2_version_list[0]
            if v2_version == "Team ProtoMan":
                version = "protoman"
            elif v2_version == "Team Colonel":
                version = "colonel"
            else:
                version = None
        else:
            version = None

        chip["version"] = version
        bn5_chips.append(chip)

    return bn5_chips

def is_library_chip(chip):
    if chip is None:
        return False

    if not isinstance(chip.get("index"), int):
        return False

    if chip.get("section") not in ("standard", "mega", "giga", "dark", "secret"):
        return False

    return True

version_to_ordinal = {
    "protoman": 0,
    "colonel": 1,
    None: None
}

def compare_chips(a, b):
    a_index = a.get("index")
    b_index = b.get("index")

    if a_index < b_index:
        return -1
    elif a_index > b_index:
        return 1
    else:
        a_version = version_to_ordinal[a.get("version")]
        b_version = version_to_ordinal[b.get("version")]

        if a_version < b_version:
            return -1
        elif a_version > b_version:
            return 1
        else:
            raise RuntimeError(f"Bad chip comparison! a: {a}, b: {b}")

def bn5_mega_sort_index(chip):
    chip_index = chip.get("index")
    if chip_index < 22:
        return chip_index
    # version exclusive megas
    elif 22 <= chip_index <= 39:
        if chip.get("version") == "protoman":
            return chip_index
        else:
            return chip_index + 18
    else:
        return chip_index + 36

def get_basic_chip_id_name(chip):
    return f"{chip['index']:03d}", chip["name"]["en"]

version_to_game_version = {
    "protoman": "{{GameVersion|TP}}",
    "colonel": "{{GameVersion|TC}}",
}

def get_mega_chip_id_name(chip):
    version = chip["version"]
    chip_name = chip["name"]["en"]
    if chip_name.endswith("DS"):
        stacked_suffix = "{{DS}}"
    elif chip_name.endswith("SP"):
        stacked_suffix = "{{SP}}"
    else:
        stacked_suffix = None

    if stacked_suffix is not None:
        chip_name = chip_name[:-2] + stacked_suffix

    chip_index = chip["index"]

    if version is None:
        chip_id = f"{chip_index:03d}"
    else:
        game_version = version_to_game_version[version]
        chip_id = f"{game_version} {chip_index:03d}"

    return chip_id, chip_name

def gen_basic_chiploc_table(chips, game_drop_table=None, mystery_data=None, chip_id_name_func=get_basic_chip_id_name, chip_traders=None):
    output = []
    if mystery_data is not None:
        mystery_data_jp, mystery_data_en = mystery_data
    for chip in chips:
        id, name = chip_id_name_func(chip)
        cur_output = CHIP_LOCATION_TEMPLATE_PART_1.format(id=id, name=name)
        output.append(cur_output)
        for code in chip["codes"]:
            original_code = code
            if code == "*":
                code = "asterisk"

            location_text_parts = []
            location_text_parts.append(DUMMY_LOCATION_TEXT)

            if game_drop_table is not None:
                original_name = name.replace("{{DS}}", "[DS]").replace("{{SP}}", "[SP]")
                enemy_chip_location = game_drop_table.find_chip(original_name, original_code)
                if enemy_chip_location is not None:
                    location_text_parts.append(enemy_chip_location)

            if mystery_data is not None:
                md_chip_location_jp = mystery_data_jp.find_chip(name, original_code)
                md_chip_location_en = mystery_data_en.find_chip(name, original_code)
                if md_chip_location_jp != md_chip_location_en:
                    if md_chip_location_jp is None:
                        print(f"{name} {original_code}: EN: {md_chip_location_en}")                        
                    elif md_chip_location_en is None:
                        print(f"{name} {original_code}: JP: {md_chip_location_jp}")
                    else:
                        print(f"{name} {original_code}: JP/EN: {md_chip_location_jp} | {md_chip_location_en}")

                if md_chip_location_en is not None:
                    location_text_parts.append(md_chip_location_en)

            location_text = ", ".join(location_text_parts)

            output.append(f"|{code}={location_text}\n")

        if chip_traders is not None:
            traders_for_chip, version_text = chip_traders.find_traders_for_chip(chip)
            output.append(f"|traders={traders_for_chip}\n")
            if version_text is not None:
                output.append(f"|tradersversion={version_text}\n")

        output.append("}}\n")

    #output.append("\n")

    return output

NO_VERSION = 0
PROTOMAN = 1
COLONEL = 2

class ChipTraderEntry:
    __slots__ = ("name", "codes", "version")

    def __init__(self, line):
        if "[TP]" in line:
            self.version = "protoman"
        elif "[TC]" in line:
            self.version = "colonel"
        else:
            self.version = None

        line = line.replace("[TC]", "").replace("[TP]", "").replace("[", "").replace("]", "").strip()
        self.name, self.codes = line.rsplit(maxsplit=1)

class ChipTrader:
    __slots__ = ("name", "chips")

    def __init__(self, filename):
        self.chips = {}

        with open(filename, "r") as f:
            line = next(f)
            self.name = line.strip()

            for line in f:
                entry = ChipTraderEntry(line)
                self.chips[entry.name] = entry

    def get_trader_text_if_has_chip(self, chip):
        chip_name = chip["name"]["en"]
        entry = self.chips.get(chip_name)
        if entry is not None:
            trader_text = ""
            if entry.version is not None:
                version_text = f"{version_to_game_version[entry.version]}"
            else:
                version_text = None

            trader_text += self.name
            all_codes = set(chip["codes"])
            entry_codes = set(entry.codes)
            missing_codes = all_codes - entry_codes

            if len(missing_codes) != 0:
                trader_text += " (No " + ", ".join(("{{code|%s}}" % code) for code in missing_codes) + ")"

            return trader_text, version_text
        else:
            return None, None

class ChipTraders:
    __slots__ = ("traders",)

    def __init__(self, filenames):
        self.traders = []
        for filename in filenames:
            self.traders.append(ChipTrader(filename))

    def find_traders_for_chip(self, chip):
        found_trader_texts = []
        found_version_text = None
        for trader in self.traders:
            cur_trader_text, version_text = trader.get_trader_text_if_has_chip(chip)
            if cur_trader_text is not None:
                found_trader_texts.append(cur_trader_text)
                if version_text is not None:
                    found_version_text = version_text

        if len(found_trader_texts) != 0:
            return ", ".join(found_trader_texts), found_version_text
        else:
            return None, None

def main():
    with open("bn5_chips_v2.json", "r") as f:
        bn5_chips_v2 = json.load(f)

    bn5_chips = convert_v2_format_to_v1(bn5_chips_v2)
    bn5_library_chips = list(filter(is_library_chip, bn5_chips))

    with open("bn5_library_chips.json", "w+") as f:
        json.dump(bn5_library_chips, f, indent=2)

    chip_traders = ChipTraders(("higsbys_trader.txt", "hall_trader.txt", "mine_trader.txt", "bugfrag_trader.txt"))
    mystery_data_jp = MysteryDataParser5("exe5_mystery_data.txt", False, bn5_library_chips)
    mystery_data_en = MysteryDataParser5("bn5_mystery_data.txt", True, bn5_library_chips)

    #bn5_remaining_sections = set(chip.get("section") for chip in bn5_library_chips)
    bn5_chips_by_section = {}

    for section in ("standard", "mega", "giga", "dark", "secret"):
        bn5_chips_by_section[section] = [chip for chip in bn5_library_chips if chip.get("section") == section]
        sort_func = lambda x: x.get("index")
        if section == "mega":
            sort_func = bn5_mega_sort_index
        elif section == "giga":
            bn5_gigas_full = bn5_chips_by_section["giga"]
            bn5_gigas_protoman = sorted([chip for chip in bn5_gigas_full if chip.get("version") == "protoman"], key=lambda x: x.get("index"))
            bn5_gigas_colonel = sorted([chip for chip in bn5_gigas_full if chip.get("version") == "colonel"], key=lambda x: x.get("index"))
            bn5_chips_by_section["giga_protoman"] = bn5_gigas_protoman
            bn5_chips_by_section["giga_colonel"] = bn5_gigas_colonel
        elif section == "secret":
            bn5_secret = bn5_chips_by_section["secret"]
            bn5_secret_registered = []
            bn5_secret_unregistered = []
            for chip in bn5_secret:
                chip_name = chip["name"]["en"]
                if chip_name == "Otenko":
                    bn5_secret_registered.append(chip)
                elif chip_name == "GunDelEX":
                    bn5_secret_registered.append(chip)
                elif chip_name == "LeaderR":
                    bn5_secret_unregistered.append(chip)
                elif chip_name == "ChaosL":
                    bn5_secret_unregistered.append(chip)

            bn5_chips_by_section["secret_registered"] = bn5_secret_registered
            bn5_chips_by_section["secret_unregistered"] = bn5_secret_unregistered

        bn5_chips_by_section[section].sort(key=sort_func)

    game_drop_table = enemy_drops.GameDropTable(enemy_drops.bn4to6_hp_percents_to_name, 5, 
        enemy_drops.InputDropTable("bn5p_drops.txt", "bn5p_ignored_enemies.txt", "5TP"),
        enemy_drops.InputDropTable("bn5c_drops.txt", "bn5c_ignored_enemies.txt", "5TC")
    )

    output = []
    output.append(PAGE_HEADER)

    bn5_standard = bn5_chips_by_section["standard"]
    output.append("==Standard Class Chips==\n")
    output.extend(gen_basic_chiploc_table(bn5_standard, game_drop_table=game_drop_table, mystery_data=(mystery_data_jp, mystery_data_en), chip_traders=chip_traders))

    bn5_mega = bn5_chips_by_section["mega"]
    output.append("==Mega Class Chips==\n")
    output.extend(gen_basic_chiploc_table(bn5_mega, game_drop_table=game_drop_table, mystery_data=(mystery_data_jp, mystery_data_en), chip_id_name_func=get_mega_chip_id_name, chip_traders=chip_traders))

    output.extend(["==Giga Class Chips==\n", "===Team ProtoMan===\n"])
    bn5_giga_protoman = bn5_chips_by_section["giga_protoman"]
    output.extend(gen_basic_chiploc_table(bn5_giga_protoman))

    bn5_giga_colonel = bn5_chips_by_section["giga_colonel"]
    output.append("===Team Colonel===\n")
    output.extend(gen_basic_chiploc_table(bn5_giga_colonel))

    bn5_dark = bn5_chips_by_section["dark"]
    output.append("==Dark Chips==\n")
    output.extend(gen_basic_chiploc_table(bn5_dark))

    output.extend(["==Secret Chips==\n", "That version's exclusive Navis are registered as Secret in other version's library.\n"])
    bn5_secret_registered = bn5_chips_by_section["secret_registered"]
    output.extend(gen_basic_chiploc_table(bn5_secret_registered))

    bn5_secret_unregistered = bn5_chips_by_section["secret_unregistered"]
    output.append("==Unregistered Chips==\n")
    output.extend(gen_basic_chiploc_table(bn5_secret_unregistered))
    output.append("\n")
    output.append("[[Category:Mega Man Battle Network Series]] [[Category:Mega Man Battle Network 5]]\n")

    with open("bn5_chips_out.dump", "w+") as f:
        f.write("".join(output))

if __name__ == "__main__":
    main()
