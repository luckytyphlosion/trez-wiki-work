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

def main():
    output = []

    with open("bn5_chips.json", "r") as f:
        bn5_chips = json.load(f)

    bn5_library_chips = list(filter(is_library_chip, bn5_chips))

    with open("bn5_library_chips.json", "w+") as f:
        json.dump(bn5_library_chips, f, indent=2)

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

    output.append(CHIPS_HEADER)

    for i, chip in enumerate(bn5_standard, 1):
        if i != chip["index"]:
            raise RuntimeError()

        output.append("|-\n")
        output.append(f"|{i:03d}||{chip['name']['en']}||\n")
        for code in chip["codes"]:
            output.append("{{coderow|" + code + "|}}\n")
        output.append("||\n")

    output.append("|}\n")

    with open("bn5_standard_chips_out.txt", "w+") as f:
        f.write("".join(output))

    output = []

    bn5_mega = bn5_chips_by_section["mega"]

    prev_chip_index = 0

    output.append(CHIPS_HEADER)

    for i, chip in enumerate(bn5_mega, 1):
        chip_index = chip["index"]
        #if chip_index - prev_chip_index not in (0, 1):
        #    raise RuntimeError()

        output.append("|-\n")

        version = chip["version"]
        chip_name = chip["name"]["en"]
        if chip_name.endswith("DS"):
            stacked_suffix = "{{stack|D|S}}"
        elif chip_name.endswith("SP"):
            stacked_suffix = "{{stack|S|P}}"
        else:
            stacked_suffix = None

        if stacked_suffix is not None:
            chip_name = chip_name[:-2] + stacked_suffix

        if version is None:
            output.append(f"|{chip_index:03d}||{chip_name}||\n")
        else:
            version_letter = version[0].upper()
            output.append(f"|{chip_index:03d} ({version_letter})||{chip_name}||\n")

        for code in chip["codes"]:
            output.append("{{coderow|" + code + "|}}\n")

        output.append("||\n")
        #prev_chip_index = chip_index

    output.append("|}\n")

    with open("bn5_mega_chips_out.txt", "w+") as f:
        f.write("".join(output))

    output = []
    output.append(NO_TRADER_CHIPS_HEADER)

    bn5_giga_protoman = bn5_chips_by_section["giga_protoman"]
    for i, chip in enumerate(bn5_giga_protoman, 1):
        if i != chip["index"]:
            raise RuntimeError()

        output.append("|-\n")
        output.append(f"|{i:03d}||{chip['name']['en']}||\n")
        for code in chip["codes"]:
            output.append("{{coderow|" + code + "|}}\n")

    output.append("|}\n")

    output.append(NO_TRADER_CHIPS_HEADER)

    bn5_giga_colonel = bn5_chips_by_section["giga_colonel"]
    for i, chip in enumerate(bn5_giga_colonel, 1):
        if i != chip["index"]:
            raise RuntimeError()

        output.append("|-\n")
        output.append(f"|{i:03d}||{chip['name']['en']}||\n")
        for code in chip["codes"]:
            output.append("{{coderow|" + code + "|}}\n")

    output.append("|}\n")

    output.append(NO_TRADER_CHIPS_HEADER)

    bn5_dark = bn5_chips_by_section["dark"]
    for i, chip in enumerate(bn5_dark, 1):
        if i != chip["index"]:
            raise RuntimeError()

        output.append("|-\n")
        output.append(f"|{i:03d}||{chip['name']['en']}||\n")
        for code in chip["codes"]:
            output.append("{{coderow|" + code + "|}}\n")

    with open("bn5_giga_dark_out.txt", "w+") as f:
        f.write("".join(output))

    output = []
    output.append(NO_TRADER_CHIPS_HEADER)

    bn5_secret_registered = bn5_chips_by_section["secret_registered"]

    for i, chip in enumerate(bn5_secret_registered, 1):
        output.append("|-\n")
        output.append(f"|{chip['index']:03d}||{chip['name']['en']}||\n")
        for code in chip["codes"]:
            output.append("{{coderow|" + code + "|}}\n")

    output.append("|}\n")

    output.append(NO_TRADER_CHIPS_HEADER)

    bn5_secret_unregistered = bn5_chips_by_section["secret_unregistered"]

    for i, chip in enumerate(bn5_secret_unregistered, 1):
        output.append("|-\n")
        output.append(f"|{chip['index']:03d}||{chip['name']['en']}||\n")
        for code in chip["codes"]:
            output.append("{{coderow|" + code + "|}}\n")

    output.append("|}\n")

    with open("bn5_secret_out.txt", "w+") as f:
        f.write("".join(output))

    #for section in ("standard", "mega", "giga", "dark", "secret"):
        
    #for section, bn5_chips_for_section in bn5_chips_by_section.items():
        


if __name__ == "__main__":
    main()
