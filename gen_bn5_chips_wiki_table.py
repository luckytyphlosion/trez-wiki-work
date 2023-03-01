import json
import functools

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

def is_library_chip(chip):
    if chip is None:
        return False

    if not isinstance(chip.get("index"), int):
        return False

    if chip.get("section") in ("pa", "special", "capsule", None):
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

def gen_basic_chiploc_table(chips, chip_id_name_func=get_basic_chip_id_name, chip_traders=None):
    output = []

    for chip in chips:
        id, name = chip_id_name_func(chip)
        cur_output = CHIP_LOCATION_TEMPLATE_PART_1.format(id=id, name=name)
        output.append(cur_output)
        for code in chip["codes"]:
            if code == "*":
                code = "asterisk"
            output.append(f"|{code}={DUMMY_LOCATION_TEXT}\n")

        if chip_traders is not None:
            traders_for_chip = chip_traders.find_traders_for_chip(chip)
            output.append(f"|traders={traders_for_chip}\n")

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
                trader_text += f"{version_to_game_version[entry.version]} "

            trader_text += self.name
            all_codes = set(chip["codes"])
            entry_codes = set(entry.codes)
            missing_codes = all_codes - entry_codes

            if len(missing_codes) != 0:
                trader_text += " (No " + ", ".join(("{{code|%s}}" % code) for code in missing_codes) + ")"

            return trader_text
        else:
            return None

class ChipTraders:
    __slots__ = ("traders",)

    def __init__(self, filenames):
        self.traders = []
        for filename in filenames:
            self.traders.append(ChipTrader(filename))

    def find_traders_for_chip(self, chip):
        found_trader_texts = []
        for trader in self.traders:
            cur_trader_text = trader.get_trader_text_if_has_chip(chip)
            if cur_trader_text is not None:
                found_trader_texts.append(cur_trader_text)

        if len(found_trader_texts) != 0:
            return ", ".join(found_trader_texts)
        else:
            return None

def main():
    with open("bn5_chips.json", "r") as f:
        bn5_chips = json.load(f)

    bn5_library_chips = list(filter(is_library_chip, bn5_chips))

    with open("bn5_library_chips.json", "w+") as f:
        json.dump(bn5_library_chips, f, indent=2)

    chip_traders = ChipTraders(("higsbys_trader.txt", "hall_trader.txt", "mine_trader.txt", "bugfrag_trader.txt"))

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

    bn5_standard = bn5_chips_by_section["standard"]
    bn5_standard_output = ["==Standard Class Chips==\n"]
    bn5_standard_output.extend(gen_basic_chiploc_table(bn5_standard, chip_traders=chip_traders))

    with open("bn5_standard_chips_out.txt", "w+") as f:
        f.write("".join(bn5_standard_output))

    bn5_mega = bn5_chips_by_section["mega"]
    bn5_mega_output = ["==Mega Class Chips==\n"]
    bn5_mega_output.extend(gen_basic_chiploc_table(bn5_mega, chip_id_name_func=get_mega_chip_id_name, chip_traders=chip_traders))

    with open("bn5_mega_chips_out.txt", "w+") as f:
        f.write("".join(bn5_mega_output))

    bn5_giga_dark_output = ["==Giga Class Chips==\n", "===Team ProtoMan===\n"]
    bn5_giga_protoman = bn5_chips_by_section["giga_protoman"]
    bn5_giga_dark_output.extend(gen_basic_chiploc_table(bn5_giga_protoman))

    bn5_giga_colonel = bn5_chips_by_section["giga_colonel"]
    bn5_giga_dark_output.append("===Team Colonel===\n")
    bn5_giga_dark_output.extend(gen_basic_chiploc_table(bn5_giga_colonel))

    bn5_giga_dark_output.append("\n")
    bn5_dark = bn5_chips_by_section["dark"]
    bn5_giga_dark_output.append("==Dark Chips==\n")
    bn5_giga_dark_output.extend(gen_basic_chiploc_table(bn5_dark))

    with open("bn5_giga_dark_out.txt", "w+") as f:
        f.write("".join(bn5_giga_dark_output))

    bn5_secret_output = ["==Secret Chips==\n"]
    bn5_secret_registered = bn5_chips_by_section["secret_registered"]
    bn5_secret_output.extend(gen_basic_chiploc_table(bn5_secret_registered))
    bn5_secret_output.append("\n")

    bn5_secret_unregistered = bn5_chips_by_section["secret_unregistered"]
    bn5_secret_output.append("==Unregistered Chips==\n")
    bn5_secret_output.extend(gen_basic_chiploc_table(bn5_secret_unregistered))

    with open("bn5_secret_out.txt", "w+") as f:
        f.write("".join(bn5_secret_output))

if __name__ == "__main__":
    main()
