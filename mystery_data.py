import re

from line_reader import LineReader

multitab_regex = re.compile(r"\t+")
multispace_regex = re.compile(r" +")
tab_then_digit_regex = re.compile(r"^\t+[0-9]")
spaces_then_digit_regex = re.compile(r"^    +[0-9]")

availability_to_abbrev_availability = {
    "Game 1": "G1",
    "Game 2": "G2",
}

class MysteryDataParser:
    __slots__ = ("all_chip_locations",)

    def __init__(self, filename, game_number, library_chips):
        all_library_chip_code_combos = set()
        for chip in library_chips:
            for chip_code in chip["codes"]:
                all_library_chip_code_combos.add(f"{chip['name']['en']} {chip_code}")

        with open(filename, "r") as f:
            contents = f.read()
            contents = contents.replace("Game 1:", "Game 1:\n").replace("Game 2:", "Game 2:\n").replace("Rest:", "Rest:\n").replace("Always:", "Always:\n")
            line_reader = LineReader(contents.splitlines(), filename)

        self.all_chip_locations = {}

        for line in line_reader:
            map_name = line.split(": ")[1]
            while True:
                line = line_reader.next()
                if line.strip() != "":
                    break

            while True:
                mystery_data_type = line.split("\t", maxsplit=1)[0]
                #if mystery_data_type in {"Blue", "Purple"}:
                mystery_data_type_abbrev = f"{mystery_data_type[0]}MD"
                if mystery_data_type == "Green":
                    while True:
                        line = line_reader.next()
                        if not tab_then_digit_regex.match(line):
                            break
                else:
                    line = line_reader.next()
    
                while True:
                    md_contents = multitab_regex.split(line.strip())
                    print(f"md_contents: {md_contents}")
                    if mystery_data_type in {"Blue", "Purple"}:
                        if line.endswith(":"):
                            availability = "Rest"
                            line = line_reader.next()
                            md_contents = [""] + multitab_regex.split(line.strip())
                        else:
                            availability = md_contents[0].replace(":", "")
                    elif line.endswith(":"):
                        availability = line.strip()[:-1]
                        line = line_reader.next()
                        continue

                    if mystery_data_type == "Green":
                        reward_padded = md_contents[3]
                    else:
                        reward_padded = md_contents[4]
                    reward = multispace_regex.sub(" ", reward_padded)

                    abbrev_availability = availability_to_abbrev_availability.get(availability, availability)
                    if abbrev_availability == "Rest" and mystery_data_type == "Green":
                        if map_name in {"Undernet 5", "Black Earth 1", "Black Earth 2"}:
                            abbrev_availability = "Always"
                        else:
                            abbrev_availability = "G3+"
                    elif map_name == "Sharo Area" and reward == "BlkBomb Z":
                        abbrev_availability = "Always"

                    #print(line)
                    if reward not in all_library_chip_code_combos:
                        pass #print(f"ignored {reward}")
                    else:
                        location = f"{map_name} {mystery_data_type_abbrev} ({abbrev_availability})"
                        #print(f"location: {location}")
                        self.add_location(reward, location)
    
                    line = line_reader.next()
                    if not line.startswith("\t"):
                        break

                if line.startswith("---------------"):
                    break

    def add_location(self, chip_full, location):
        chip_locations = self.all_chip_locations.get(chip_full)
        if chip_locations is None:
            chip_locations = {location: True}
            self.all_chip_locations[chip_full] = chip_locations
        else:
            chip_locations[location] = True

    def find_chip(self, chip_name, code):
        chip_locations = self.all_chip_locations.get(f"{chip_name} {code}")
        if chip_locations is None:
            return None
        else:
            return ", ".join(chip_locations.keys())

dungeon_area_regex = re.compile(r"^(Main|Drill|Ship|Gargoyle|Factory) Comp")

bn5_availability_to_abbrev_availability = {
    "Level 1": "L1",
    "Level 2": "L2",
    "Level 3": "L3",
}

class MysteryDataParser5:
    __slots__ = ("all_chip_locations",)

    def __init__(self, filename, is_us, library_chips):
        all_library_chip_code_combos = set()
        for chip in library_chips:
            for chip_code in chip["codes"]:
                all_library_chip_code_combos.add(f"{chip['name']['en']} {chip_code}")

        with open(filename, "r") as f:
            contents = f.read()
            contents = contents.replace("Level 1:", "Level 1:\n").replace("Level 2:", "Level 2:\n").replace("Level 3:", "Level 3:\n")
            line_reader = LineReader(contents.splitlines(), filename)

        self.all_chip_locations = {}

        for line in line_reader:
            #print(f"line: {line}")
            map_name = line.split(": ")[1]
            is_dungeon_comp = dungeon_area_regex.match(map_name) or map_name.startswith("Nebula Area")
            if "/" in map_name:
                map_name_jp, map_name_en = map_name.replace(" (JP)", "").replace(" (EN)", "").split(" / ")
                map_name = f"{{{{JP}}}} {map_name_jp} / {{{{EN}}}} {map_name_en}"
            else:
                map_name = map_name.replace("(JP)", "{{JP}}")
                #if is_us:
                #    map_name = map_name_en
                #else:
                #    map_name = map_name_jp

            while True:
                line = line_reader.next()
                if line.strip() != "":
                    break

            while True:
                mystery_data_type = line.split("\t", maxsplit=1)[0]
                #if mystery_data_type in {"Blue", "Purple"}:
                mystery_data_type_abbrev = f"{mystery_data_type[0]}MD"
                if mystery_data_type == "Green":
                    while True:
                        line = line_reader.next()
                        #print(line)
                        if not tab_then_digit_regex.match(line):
                            break
                else:
                    line = line_reader.next()

                after_first_level = False

                while True:
                    md_contents = multitab_regex.split(line.strip())
                    #print(f"md_contents: {md_contents}")
                    if mystery_data_type in {"Blue", "Purple"}:
                        #if line.endswith(":"):
                        #    availability = "Rest"
                        #    line = line_reader.next()
                        #    md_contents = [""] + multitab_regex.split(line.strip())
                        #else:
                        availability = None # md_contents[0].replace(":", "")
                    elif line.endswith(":"):
                        availability = line.strip()[:-1]
                        if is_dungeon_comp:
                            availability = None
                            if after_first_level:
                                line = line_reader.next()
                                if not line.startswith("\t"):
                                    break

                        #print(f"availability: {availability}")
                        line = line_reader.next()
                        #md_contents = multitab_regex.split(line.strip())
                        #print(f"md_contents: {md_contents}")
                        after_first_level = True
                        continue

                    if mystery_data_type == "Green":
                        reward_padded = md_contents[3]
                    else:
                        reward_padded = md_contents[4]
                    reward = multispace_regex.sub(" ", reward_padded)

                    abbrev_availability = bn5_availability_to_abbrev_availability.get(availability, availability)
                    #if abbrev_availability == "Rest" and mystery_data_type == "Green":
                    #    if map_name in {"Undernet 5", "Black Earth 1", "Black Earth 2"}:
                    #        abbrev_availability = "Always"
                    #    else:
                    #        abbrev_availability = "G3+"
                    #elif map_name == "Sharo Area" and reward == "BlkBomb Z":
                    #    abbrev_availability = "Always"

                    #print(line)
                    if reward not in all_library_chip_code_combos:
                        pass #print(f"ignored {reward}")
                    else:
                        if abbrev_availability is None:
                            location = f"{map_name} {mystery_data_type_abbrev}"
                        else:
                            location = f"{map_name} {mystery_data_type_abbrev} ({abbrev_availability})"
                            
                        #print(f"location: {location}")
                        self.add_location(reward, location)
    
                    line = line_reader.next()
                    if not line.startswith("\t"):
                        break

                if line.startswith("---------------"):
                    break

    def add_location(self, chip_full, location):
        chip_locations = self.all_chip_locations.get(chip_full)
        if chip_locations is None:
            chip_locations = {location: True}
            self.all_chip_locations[chip_full] = chip_locations
        else:
            chip_locations[location] = True

    def find_chip(self, chip_name, code):
        chip_locations = self.all_chip_locations.get(f"{chip_name} {code}")
        if chip_locations is None:
            return None
        else:
            return ", ".join(chip_locations.keys())

class MysteryDataParser6:
    __slots__ = ("all_chip_locations",)

    def __init__(self, filename, is_us, library_chips):
        all_library_chip_code_combos = set()
        for chip in library_chips:
            for chip_code in chip["codes"]:
                all_library_chip_code_combos.add(f"{chip['name']['en']} {chip_code}")

        with open(filename, "r") as f:
            contents = f.read()
            contents = contents.replace("Contents:", "Contents:\n")
            line_reader = LineReader(contents.splitlines(), filename)

        self.all_chip_locations = {}

        for line in line_reader:
            #print(f"line: {line}")
            map_name = line.split(": ")[1]
            #is_dungeon_comp = dungeon_area_regex.match(map_name) or map_name.startswith("Nebula Area")
            if "/" in map_name:
                map_name_jp, map_name_en = map_name.replace(" (JP)", "").replace(" (EN)", "").split(" / ")
                map_name = f"{{{{JP}}}} {map_name_jp} / {{{{EN}}}} {map_name_en}"
            else:
                map_name = map_name.replace("(JP)", "{{JP}}")
                #if is_us:
                #    map_name = map_name_en
                #else:
                #    map_name = map_name_jp

            while True:
                line = line_reader.next()
                if line.strip() != "":
                    break

            while True:
                mystery_data_type = line.split(maxsplit=1)[0]
                #if mystery_data_type in {"Blue", "Purple"}:
                mystery_data_type_abbrev = f"{mystery_data_type[0]}MD"
                if mystery_data_type == "Green":
                    while True:
                        line = line_reader.next()
                        #print(line)
                        if not spaces_then_digit_regex.match(line):
                            print(f"line: {line}")
                            break
                else:
                    line = line_reader.next()

                after_first_level = False

                while True:
                    #print(f"line: {line}")
                    md_contents = multitab_regex.split(line.strip())
                    print(f"md_contents: {md_contents}")
                    #if mystery_data_type in {"Blue", "Purple"}:
                    #    #if line.endswith(":"):
                    #    #    availability = "Rest"
                    #    #    line = line_reader.next()
                    #    #    md_contents = [""] + multitab_regex.split(line.strip())
                    #    #else:
                    #    availability = None # md_contents[0].replace(":", "")
                    if line.endswith("Contents:"):
                        #print(f"ends with contents")
                        #availability = line.strip()[:-1]
                        #if is_dungeon_comp:
                        #    availability = None
                        #    if after_first_level:
                        #        line = line_reader.next()
                        #        if not line.startswith("\t"):
                        #            break

                        #print(f"availability: {availability}")
                        line = line_reader.next()
                        #md_contents = multitab_regex.split(line.strip())
                        #print(f"md_contents: {md_contents}")
                        continue

                    reward_padded = md_contents[3]
                    reward = multispace_regex.sub(" ", reward_padded)

                    if reward not in all_library_chip_code_combos:
                        pass #print(f"ignored {reward}")
                    else:
                        location = f"{map_name} {mystery_data_type_abbrev}"

                        self.add_location(reward, location)
    
                    #print(f"line before: {line}")
                    line = line_reader.next()
                    #print(f"line after: {line}")

                    if not line.startswith("    "):
                        break

                if line.startswith("---------------"):
                    break

    def add_location(self, chip_full, location):
        chip_locations = self.all_chip_locations.get(chip_full)
        if chip_locations is None:
            chip_locations = {location: True}
            self.all_chip_locations[chip_full] = chip_locations
        else:
            chip_locations[location] = True

    def find_chip(self, chip_name, code):
        chip_locations = self.all_chip_locations.get(f"{chip_name} {code}")
        if chip_locations is None:
            return None
        else:
            return ", ".join(chip_locations.keys())

def main():
    import json
    from gen_bn4_chips_wiki_table import convert_v2_format_to_v1, is_library_chip

    with open("bn4_chips_v2.json", "r") as f:
        chips_v2 = json.load(f)

    chips = convert_v2_format_to_v1(chips_v2)
    library_chips = list(filter(is_library_chip, chips))

    bn4_mystery_data = MysteryDataParser("bn4_mystery_data.txt", 4, library_chips)
    output = ""
    for chip_full, chip_locations in bn4_mystery_data.all_chip_locations.items():
        output += f"{chip_full}: {', '.join(chip_locations.keys())}\n"

    print(output)

if __name__ == "__main__":
    main()
