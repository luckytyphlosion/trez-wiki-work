import json
import functools

import enemy_drops
from mystery_data import MysteryDataParser6

PAGE_HEADER = """\
{{nw|TODO: Add info and improve template.}}

Locations of BattleChips in [[Mega Man Battle Network 6]]. Due to the removed areas, some chips are distributed differently between the Japanese and international versions.
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

def convert_v2_format_to_v1(chips_v2):
    chips = []

    for v2_chip_full in chips_v2["results"].values():
        v2_chip = v2_chip_full["printouts"]

        chip = {
            "name": {
                "en": None
            },
            "codes": "".join(v2_chip["codes"]),
            "index": v2_chip["index"][0],
            "section": v2_chip["section"][0].lower()
        }

        v2_chip_name = v2_chip["name"][0]

        if v2_chip_name == "AquaMan":
            v2_chip_name = "SpoutMan"
        elif v2_chip_name == "AquaManEX":
            v2_chip_name = "SpoutMnEX"
        elif v2_chip_name == "AquaManSP":
            v2_chip_name = "SpoutMnSP"

        chip["name"]["en"] = v2_chip_name

        v2_version_list = v2_chip["version"]
        if len(v2_version_list) != 0:
            v2_version = v2_version_list[0]
            if v2_version == "Gregar":
                version = "gregar"
            elif v2_version == "Falzar":
                version = "falzar"
            else:
                version = None
        else:
            version = None

        chip["version"] = version
        chips.append(chip)

    return chips

def is_library_chip(chip):
    if chip is None:
        return False

    if not isinstance(chip.get("index"), int):
        return False

    if chip.get("section") not in ("standard", "mega", "giga", "secret"):
        return False

    return True

version_to_ordinal = {
    "gregar": 0,
    "falzar": 1,
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

def mega_sort_index(chip):
    chip_index = chip.get("index")
    if chip_index < 7:
        return chip_index
    # version exclusive megas
    elif 7 <= chip_index <= 21:
        if chip.get("version") == "gregar":
            return chip_index
        else:
            return chip_index + 15
    else:
        return chip_index + 30

def get_basic_chip_id_name(chip):
    return f"{chip['index']:03d}", chip["name"]["en"]

version_to_game_version = {
    "gregar": "{{GameVersion|G}}",
    "falzar": "{{GameVersion|F}}",
}

def get_mega_chip_id_name(chip):
    version = chip["version"]
    chip_name = chip["name"]["en"]
    if chip_name.endswith("EX") and chip_name != "GunDelEX":
        stacked_suffix = "{{EX}}"
    elif chip_name.endswith("SP"):
        stacked_suffix = "{{SP}}"
    else:
        stacked_suffix = None

    if stacked_suffix is not None:
        chip_name = chip_name[:-2] + stacked_suffix

    chip_index = chip["index"]

    if version is None:
        chip_id = f"{chip_index:03d}"
    elif chip_index >= 40:
        chip_id = f"{{{{JP}}}} {chip_index:03d}"
    else:
        game_version = version_to_game_version[version]
        chip_id = f"{game_version} {chip_index:03d}"

    return chip_id, chip_name

def get_registered_secret_chip_id_name(chip):
    chip_name = chip["name"]["en"]
    chip_id = f"{{{{JP}}}} {chip['index']:03d}"
    return chip_id, chip_name

def get_unregistered_secret_chip_id_name(chip):
    chip_name = chip["name"]["en"]

    if chip_name == "Gregar":
        chip_id = "{{GameVersion|G}} ---"
    elif chip_name == "Falzar":
        chip_id = "{{GameVersion|F}} ---"
    else:
        chip_id = "---"

    return chip_id, chip_name

jp_en_chip_full_to_location_text = {
    "ElecSwrd E": "Central Area 3 PMD, {{JP}} Undernet 3 {{JP}} GMD",
    "Recov150 M": "{{JP}} Undernet 2 BMD / {{EN}} Undernet Zero BMD",
    "WhiCapsl *": "Fish Stick Shop Comp BMD, {{JP}} Class 1-2 Comp BMD / {{EN}} Stuffed Toy Shop Comp BMD"
}

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
                original_name = name.replace("{{EX}}", "[EX]").replace("{{SP}}", "[SP]")
                enemy_chip_location = game_drop_table.find_chip(original_name, original_code)
                if enemy_chip_location is not None:
                    location_text_parts.append(enemy_chip_location)

            if mystery_data is not None:
                md_chip_location_jp = mystery_data_jp.find_chip(name, original_code)
                md_chip_location_en = mystery_data_en.find_chip(name, original_code)
                if md_chip_location_jp != md_chip_location_en:
                    if md_chip_location_jp is None:
                        md_chip_location_en = f"{{{{EN}}}} {md_chip_location_en}"
                        location_text_parts.append(md_chip_location_en)
                        #print(f"{name} {original_code}: EN: {md_chip_location_en}")                        
                    elif md_chip_location_en is None:
                        md_chip_location_jp = f"{{{{JP}}}} {md_chip_location_jp}"
                        location_text_parts.append(md_chip_location_jp)
                        #print(f"{name} {original_code}: JP: {md_chip_location_jp}")
                    else:
                        chip_full = f"{name} {original_code}"
                        location_text = jp_en_chip_full_to_location_text[chip_full]
                        location_text_parts.append(location_text)
                        #print(f"{name} {original_code}: JP/EN: {md_chip_location_jp} | {md_chip_location_en}")
                elif md_chip_location_en is not None:
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

JP_HAS_STAR_CODE = 0
JP_NO_STAR_CODE = 1
JP_STAR_CODE_IRRELEVANT = 2

class ChipTraderEntry:
    __slots__ = ("name", "codes", "version", "jp_star_code")

    def __init__(self, line):
        if "[G]" in line:
            self.version = "gregar"
        elif "[F]" in line:
            self.version = "falzar"
        else:
            self.version = None

        if "[J*Y]" in line:
            self.jp_star_code = JP_HAS_STAR_CODE
        elif "[J*N]" in line:
            self.jp_star_code = JP_NO_STAR_CODE
        else:
            self.jp_star_code = JP_STAR_CODE_IRRELEVANT

        line = line.replace("[F]", "").replace("[G]", "").replace("[J*Y]", "").replace("[J*N]", "").replace("[", "").replace("]", "").strip()
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
            #print(f"chip_name: {chip_name}, entry.codes: {entry.codes}")
            entry_codes = set(entry.codes)
            missing_codes = all_codes - entry_codes
            if "*" in missing_codes and "*" in all_codes:
                naturally_missing_star_code = True
            else:
                naturally_missing_star_code = False
            if len(missing_codes) > 1:
                raise RuntimeError()
            elif len(missing_codes) == 1 and "*" not in missing_codes:
                raise RuntimeError()

            missing_codes_parts = [("{{code|%s}}" % code) for code in missing_codes]
            if entry.jp_star_code == JP_NO_STAR_CODE:
                missing_code_text = " ({{JP2}}: No {{code|*}})"
            elif naturally_missing_star_code:
                missing_code_text = " (No {{code|*}})"
            else:
                missing_code_text = ""

            trader_text += missing_code_text

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
    with open("bn6_chips_v2.json", "r") as f:
        chips_v2 = json.load(f)

    chips = convert_v2_format_to_v1(chips_v2)
    library_chips = list(filter(is_library_chip, chips))

    with open("bn6_library_chips.json", "w+") as f:
        json.dump(library_chips, f, indent=2)

    chip_traders = ChipTraders(("asterland_trader.txt", "acdc_town_trader.txt", "sky_town_trader.txt", "green_town_trader.txt", "bn6_bugfrag_trader.txt"))
    mystery_data_jp = MysteryDataParser6("exe6_mystery_data.txt", False, library_chips)
    mystery_data_en = MysteryDataParser6("bn6_mystery_data.txt", True, library_chips)

    #remaining_sections = set(chip.get("section") for chip in library_chips)
    chips_by_section = {}

    for section in ("standard", "mega", "giga", "secret"):
        chips_by_section[section] = [chip for chip in library_chips if chip.get("section") == section]
        sort_func = lambda x: x.get("index")
        if section == "mega":
            sort_func = mega_sort_index
        elif section == "giga":
            gigas_full = chips_by_section["giga"]
            gigas_gregar = sorted([chip for chip in gigas_full if chip.get("version") == "gregar"], key=lambda x: x.get("index"))
            gigas_falzar = sorted([chip for chip in gigas_full if chip.get("version") == "falzar"], key=lambda x: x.get("index"))
            chips_by_section["giga_gregar"] = gigas_gregar
            chips_by_section["giga_falzar"] = gigas_falzar
        elif section == "secret":
            secret = chips_by_section["secret"]
            secret_registered = []
            secret_unregistered = []
            for chip in secret:
                chip_name = chip["name"]["en"]
                if chip_name in {"Otenko", "GunDelEX"}:
                    secret_registered.append(chip)
                elif chip_name in {"DblBeast", "Gregar", "Falzar"}:
                    secret_unregistered.append(chip)

            chips_by_section["secret_registered"] = secret_registered
            chips_by_section["secret_unregistered"] = secret_unregistered

        chips_by_section[section].sort(key=sort_func)

    game_drop_table = enemy_drops.GameDropTable(enemy_drops.bn4to6_hp_percents_to_name, 6, 
        enemy_drops.InputDropTable("bn6g_drops.txt", "bn6g_ignored_enemies.txt", "6CG"),
        enemy_drops.InputDropTable("bn6f_drops.txt", "bn6f_ignored_enemies.txt", "6CF")
    )

    output = []
    output.append(PAGE_HEADER)

    standard = chips_by_section["standard"]
    output.append("==Standard Class Chips==\n")
    output.extend(gen_basic_chiploc_table(standard, game_drop_table=game_drop_table, mystery_data=(mystery_data_jp, mystery_data_en), chip_traders=chip_traders))

    mega = chips_by_section["mega"]
    output.extend(["==Mega Class Chips==\n", "Mega Chips #40 to #45 are Japanese version only.\n"])
    output.extend(gen_basic_chiploc_table(mega, game_drop_table=game_drop_table, mystery_data=(mystery_data_jp, mystery_data_en), chip_id_name_func=get_mega_chip_id_name, chip_traders=chip_traders))

    output.extend(["==Giga Class Chips==\n", "===Gregar===\n"])
    giga_gregar = chips_by_section["giga_gregar"]
    output.extend(gen_basic_chiploc_table(giga_gregar))

    giga_falzar = chips_by_section["giga_falzar"]
    output.append("===Falzar===\n")
    output.extend(gen_basic_chiploc_table(giga_falzar))

    output.extend(["==Secret Chips==\n", "That version's exclusive Navis are registered as Secret in other version's library.\n"])
    secret_registered = chips_by_section["secret_registered"]
    output.extend(gen_basic_chiploc_table(secret_registered, chip_id_name_func=get_registered_secret_chip_id_name))

    secret_unregistered = chips_by_section["secret_unregistered"]
    output.append("==Unregistered Chips==\n")
    output.extend(gen_basic_chiploc_table(secret_unregistered, chip_id_name_func=get_unregistered_secret_chip_id_name))
    output.append("\n")
    output.append("[[Category:Mega Man Battle Network Series]] [[Category:Mega Man Battle Network 6]]\n")

    with open("bn6_chips_out.dump", "w+") as f:
        f.write("".join(output))

if __name__ == "__main__":
    main()
