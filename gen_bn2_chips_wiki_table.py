import json
import functools
import re

PAGE_HEADER = """\
{{nw|TODO: Add info and improve template.}}

Locations of BattleChips in [[Mega Man Battle Network 2]]. '''Traders will not drop {{code|*}} code if the chip has 6 codes total, except the Retro Trader (more info in that section), which will indicate if the chip drops in {{code|*}} code.'''
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

def gen_basic_chiploc_table(chips, chip_id_name_func=get_basic_chip_id_name, chip_traders=None, is_free_battle_chip=False):
    output = []

    for chip in chips:
        id, name = chip_id_name_func(chip)
        cur_output = CHIP_LOCATION_TEMPLATE_PART_1.format(id=id, name=name)
        output.append(cur_output)
        chip_codes = chip["codes"]
        if not chip_codes.endswith("*"):
            chip_codes += "*"

        for code in chip_codes:
            if code == "*":
                code = "asterisk"

            location_text = DUMMY_LOCATION_TEXT

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
        if self.name == "DrkHole":
            self.name = "Hole"

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

            if self.name == "RetroChip Trader" and chip_name == "Mine":
                missing_code_text = " (Has {{code|*}})"
            else:
                missing_code_text = ""
            #missing_codes_parts = [("{{code|%s}}" % code) for code in missing_codes]
            #if entry.jp_star_code == JP_NO_STAR_CODE:
            #    missing_code_text = " ({{JP2}}: No {{code|*}})"
            #elif naturally_missing_star_code:
            #    missing_code_text = " (No {{code|*}})"
            #else:
            #    missing_code_text = ""

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
    with open("bn2_chips_v2.json", "r") as f:
        chips_v2 = json.load(f)

    chips = convert_v2_format_to_v1(chips_v2)
    library_chips = list(filter(is_library_chip, chips))

    with open("bn2_library_chips.json", "w+") as f:
        json.dump(library_chips, f, indent=2)

    chip_traders = ChipTraders(("marine_harbor_lobby_trader.txt", "netopia_town_trader.txt", "marine_harbor_trader.txt", "acdc_metro_station_trader.txt", "retrochip_trader.txt"))

    #remaining_sections = set(chip.get("section") for chip in library_chips)
    chips_by_section = {}

    for section in ("standard",):
        chips_by_section[section] = [chip for chip in library_chips if chip.get("section") == section]
        sort_func = lambda x: x.get("index")

        chips_by_section[section].sort(key=sort_func)

    output = []
    output.append(PAGE_HEADER)

    standard = chips_by_section["standard"]
    output.append("==Chips==\n")
    output.extend(gen_basic_chiploc_table(standard, chip_traders=chip_traders, chip_id_name_func=get_bn2_chip_id_name))

    output.append("\n")
    output.append("[[Category:Mega Man Battle Network Series]] [[Category:Mega Man Battle Network 2]]\n")

    with open("bn2_chips_out.dump", "w+") as f:
        f.write("".join(output))

if __name__ == "__main__":
    main()
