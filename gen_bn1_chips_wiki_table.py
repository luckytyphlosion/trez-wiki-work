import json
import functools
import re

import enemy_drops

PAGE_HEADER = """\
{{nw|TODO: Add info and improve template.}}

Locations of BattleChips in [[Mega Man Battle Network 1]].

Both Chip Traders can give any code of any chip registered in the library (even if you do not have the code in the pack). The regular Chip Trader (3 chip) can also give new chips from a fixed pool, while the Chip Trader Special (10 chips) can give every single chip in every single code, but will not give the following chips unless they have been registered in the library:
* LifeAura
* MagicMan, MagicMn2, MagicMn3
* PharoMan, PharoMn2, PharoMn3
* ShadoMan, ShadoMn2, ShadoMn3
* Bass

The chip locations below will only mention the codes of the chips that can be obtained while unregistered from the regular Chip Trader, if any.
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

        #if v2_chip_name == "AquaMan":
        #    v2_chip_name = "SpoutMan"
        #elif v2_chip_name == "AquaManEX":
        #    v2_chip_name = "SpoutMnEX"
        #elif v2_chip_name == "AquaManSP":
        #    v2_chip_name = "SpoutMnSP"

        chip["name"]["en"] = v2_chip_name

        chips.append(chip)

    return chips

def is_library_chip(chip):
    if chip is None:
        return False

    if not isinstance(chip.get("index"), int):
        return False

    if chip.get("section") != "standard":
        return False

    return True

version_to_ordinal = {
    "white": 0,
    "blue": 1,
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
        raise RuntimeError(f"Bad chip comparison! a: {a}, b: {b}")

def get_basic_chip_id_name(chip):
    return f"{chip['index']:03d}", chip["name"]["en"]

vX_regex = re.compile(r"\w+(V[1-3])")

def get_bn2_chip_id_name(chip):
    chip_name = chip["name"]["en"]
    match_obj = vX_regex.match(chip_name)
    if match_obj:
        stacked_suffix = "{{%s}}" % match_obj.group(1)
    else:
        stacked_suffix = None

    if stacked_suffix is not None:
        chip_name = chip_name[:-2] + stacked_suffix

    chip_index = chip["index"]

    if chip_index > 260:
        chip_id = "---"
    else:
        chip_id = f"{chip_index:03d}"

    return chip_id, chip_name

def gen_basic_chiploc_table(chips, game_drop_table=None, chip_id_name_func=get_basic_chip_id_name, chip_trader=None, is_free_battle_chip=False):
    output = []

    for chip in chips:
        id, name = chip_id_name_func(chip)
        cur_output = CHIP_LOCATION_TEMPLATE_PART_1.format(id=id, name=name)
        output.append(cur_output)
        chip_codes = chip["codes"]

        for code in chip_codes:
            if code == "*":
                code = "asterisk"

            location_text_parts = []
            location_text_parts.append(DUMMY_LOCATION_TEXT)

            enemy_chip_location = game_drop_table.find_chip(name, code)
            if enemy_chip_location is not None:
                location_text_parts.append(enemy_chip_location)

            if chip_trader.has_chip_in_code(chip, code):
                location_text_parts.append("Chip Exchanger")

            location_text = ", ".join(location_text_parts)
            output.append(f"|{code}={location_text}\n")

        output.append("}}\n")

    #output.append("\n")

    return output

JP_HAS_STAR_CODE = 0
JP_NO_STAR_CODE = 1
JP_STAR_CODE_IRRELEVANT = 2

class ChipTraderEntry:
    __slots__ = ("name", "codes", "version", "jp_star_code")

    def __init__(self, line):
        #if "[RS]" in line:
        #    self.version = "white"
        #elif "[BM]" in line:
        #    self.version = "blue"
        #else:
        self.version = None

        if "[J*Y]" in line:
            self.jp_star_code = JP_HAS_STAR_CODE
        elif "[J*N]" in line:
            self.jp_star_code = JP_NO_STAR_CODE
        else:
            self.jp_star_code = JP_STAR_CODE_IRRELEVANT

        line = line.replace("[RS]", "").replace("[BM]", "").replace("[J*Y]", "").replace("[J*N]", "").replace("[", "").replace("]", "").strip()
        self.name, self.codes = line.rsplit(maxsplit=1)

class ChipTrader:
    __slots__ = ("name", "chips")

    def __init__(self, filename):
        self.chips = {}

        with open(filename, "r") as f:
            for line in f:
                entry = ChipTraderEntry(line)
                self.chips[entry.name] = entry

    def has_chip_in_code(self, chip, code):
        chip_name = chip["name"]["en"]
        entry = self.chips.get(chip_name)
        if entry is not None:
            codes_as_set = set(entry.codes)
            if code in codes_as_set:
                return True
            else:
                return False
        else:
            return False

def main():
    with open("bn1_chips_v2.json", "r") as f:
        chips_v2 = json.load(f)

    chips = convert_v2_format_to_v1(chips_v2)
    library_chips = list(filter(is_library_chip, chips))

    with open("bn1_library_chips.json", "w+") as f:
        json.dump(library_chips, f, indent=2)

    chip_trader = ChipTrader("bn1_chip_trader.txt")

    #remaining_sections = set(chip.get("section") for chip in library_chips)
    chips_by_section = {}

    for section in ("standard",):
        chips_by_section[section] = [chip for chip in library_chips if chip.get("section") == section]
        sort_func = lambda x: x.get("index")

        chips_by_section[section].sort(key=sort_func)

    game_drop_table = enemy_drops.GameDropTable(None, enemy_drops.InputDropTable("bn1_drops.txt", "bn1_ignored_enemies.txt", None))

    output = []
    output.append(PAGE_HEADER)

    standard = chips_by_section["standard"]
    output.append("==Chips==\n")
    output.extend(gen_basic_chiploc_table(standard, game_drop_table=game_drop_table, chip_trader=chip_trader))

    output.append("\n")
    output.append("[[Category:Mega Man Battle Network Series]] [[Category:Mega Man Battle Network 1]]\n")

    with open("bn1_chips_out.dump", "w+") as f:
        f.write("".join(output))

if __name__ == "__main__":
    main()
