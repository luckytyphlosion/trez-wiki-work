import re

from line_reader import LineReader

multitab_regex = re.compile(r"\t+")
multispace_regex = re.compile(r" +")
tab_then_digit_regex = re.compile(r"^\t+[0-9]")

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
            contents.replace("Game 1:", "Game 1:\n").replace("Game 2:", "Game 2:\n").replace("Rest:", "Rest:\n").replace("Always:", "Always:\n")
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
                    if mystery_data_type in {"Blue", "Purple"}:
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

"Main|Drill|Ship|Gargoyle|Factory"

class MysteryDataParser5:
    __slots__ = ("all_chip_locations",)

    def __init__(self, filename, game_number, library_chips):
        all_library_chip_code_combos = set()
        for chip in library_chips:
            for chip_code in chip["codes"]:
                all_library_chip_code_combos.add(f"{chip['name']['en']} {chip_code}")

        with open(filename, "r") as f:
            contents = f.read()
            contents.replace("Game 1:", "Game 1:\n").replace("Game 2:", "Game 2:\n").replace("Rest:", "Rest:\n").replace("Always:", "Always:\n")
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
                    if mystery_data_type in {"Blue", "Purple"}:
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
