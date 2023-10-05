import pathlib
import re
from sortedcontainers import SortedList
import itertools

from line_reader import LineReader

class InputDropTable:
    __slots__ = ("filename", "ignored_enemies_filename", "version")

    def __init__(self, filename, ignored_enemies_filename, version):
        self.filename = filename
        self.ignored_enemies_filename = ignored_enemies_filename
        self.version = version

class EnemyDropTablesAndVersion:
    __slots__ = ("enemy_drop_tables", "version")

    def __init__(self, enemy_drop_tables, version):
        self.enemy_drop_tables = enemy_drop_tables
        self.version = version

bn4to6_hp_percents_to_name = {
    frozenset((">37.5%",)): "High",
    frozenset(("<=37.5%",)): "Low",
    frozenset((">37.5%", "<=37.5%")): "",
}

class GameDropTable:
    __slots__ = ("game_enemy_drop_tables", "hp_percents_to_name", "game_number")

    def __init__(self, hp_percents_to_name, game_number, *input_drop_tables):
        self.game_enemy_drop_tables = []
        self.hp_percents_to_name = hp_percents_to_name
        if self.hp_percents_to_name is not None:
            hp_percent_drops = True
        else:
            hp_percent_drops = False
        self.game_number = game_number

        for input_drop_table in input_drop_tables:
            enemy_drop_tables = EnemyDropTables(input_drop_table.filename, input_drop_table.ignored_enemies_filename, hp_percent_drops=hp_percent_drops)
            enemy_drop_tables.parse_enemy_drop_tables()
            enemy_drop_tables.fold_same_drop_entries()
            enemy_drop_tables_and_version = EnemyDropTablesAndVersion(enemy_drop_tables, input_drop_table.version)
            self.game_enemy_drop_tables.append(enemy_drop_tables_and_version)

    def find_chip(self, chip_name, code):
        chip_full = f"{chip_name} {code}"
        output = ""

        chosen_version = None
        chip_drop_locations = None

        if len(self.game_enemy_drop_tables) == 1:
            enemy_drop_tables = self.game_enemy_drop_tables[0].enemy_drop_tables
            chip_drop_locations = enemy_drop_tables.all_chip_drop_locations.get(chip_full)
        else:
            enemy_drop_tables_1 = self.game_enemy_drop_tables[0].enemy_drop_tables
            version_1 = self.game_enemy_drop_tables[0].version

            enemy_drop_tables_2 = self.game_enemy_drop_tables[1].enemy_drop_tables
            version_2 = self.game_enemy_drop_tables[1].version

            chip_drop_locations_1 = enemy_drop_tables_1.all_chip_drop_locations.get(chip_full)
            chip_drop_locations_2 = enemy_drop_tables_2.all_chip_drop_locations.get(chip_full)

            if chip_drop_locations_1 is not None and chip_drop_locations_2 is not None:
                if chip_drop_locations_1 != chip_drop_locations_2:
                    #print(f"chip_drop_locations_1 B: {chip_drop_locations_1}")
                    #print(f"chip_drop_locations_2 B: {chip_drop_locations_2}\n")

                    if self.game_number in (3, 4):
                        chip_location_parts = []

                        for enemy_name_1, enemy_drop_1 in chip_drop_locations_1.enemy_drops.items():
                            enemy_drop_2 = chip_drop_locations_2.enemy_drops.get(enemy_name_1)
                            if enemy_drop_2 is None or len(enemy_drop_1.drop_entries) != 1 or len(enemy_drop_2.drop_entries) != 1:
                                raise RuntimeError()

                            drop_entry_1 = enemy_drop_1.drop_entries[0]
                            drop_entry_2 = enemy_drop_2.drop_entries[0]

                            if len(drop_entry_1.hp_percents) != 2 or len(drop_entry_2.hp_percents) != 2:
                                #print(f"type(enemy_drop_1.drop_entries[0].hp_percents).__name__: {type(enemy_drop_1.drop_entries[0].hp_percents).__name__}")
                                raise RuntimeError(f"{enemy_drop_1.drop_entries[0].hp_percents}, {enemy_drop_2.drop_entries[0].hp_percents}")

                            drop_ranks_formatted_1 = drop_entry_1.format_ranks()
                            drop_ranks_formatted_2 = drop_entry_2.format_ranks()

                            enemy_and_rank = f"{enemy_name_1} ({{{{{version_1}2}}}}: {drop_ranks_formatted_1}; {{{{{version_2}2}}}}: {drop_ranks_formatted_2})"
                            chip_location_parts.append(enemy_and_rank)

                        output += ", ".join(chip_location_parts)

                    elif self.game_number == 6:
                        enemy_drops_1 = chip_drop_locations_1.enemy_drops
                        enemy_drops_2 = chip_drop_locations_2.enemy_drops

                        if chip_full == "FlshBom1 Q":
                            output += "BigHat (LV5~10) ({{6CG2}}: Any HP, {{6CF2}}: HP > 37.5%)"
                        else:
                            if len(enemy_drops_1) == 1 and len(enemy_drops_2) == 2 or len(enemy_drops_1) == 2 and len(enemy_drops_2) == 1:
                                if len(enemy_drops_1) == 1 and len(enemy_drops_2) == 2:
                                    bigger_enemy_drops = enemy_drops_2
                                    bigger_enemy_drops_version = version_2
                                    smaller_enemy_drops = enemy_drops_1
                                    smaller_enemy_drops_version = version_1
                                else:
                                    bigger_enemy_drops = enemy_drops_1
                                    bigger_enemy_drops_version = version_1
                                    smaller_enemy_drops = enemy_drops_2
                                    smaller_enemy_drops_version = version_2

                                chip_location_parts = []

                                for bigger_enemy_name, bigger_enemy_drop in bigger_enemy_drops.items():
                                    if len(bigger_enemy_drop.drop_entries) != 1:
                                        raise RuntimeError()

                                    smaller_enemy_drop = smaller_enemy_drops.get(bigger_enemy_name)
                                    if smaller_enemy_drop is None:
                                        bigger_drop_entry = bigger_enemy_drop.drop_entries[0]
                                        if len(bigger_drop_entry.hp_percents) != 2:
                                            raise RuntimeError()
                                        bigger_drop_ranks_formatted = bigger_drop_entry.format_ranks()
                                        enemy_and_rank = f"{{{{{bigger_enemy_drops_version}}}}} {bigger_enemy_name} ({bigger_drop_ranks_formatted})"
                                        chip_location_parts.append(enemy_and_rank)
                                    else:
                                        if smaller_enemy_drop != bigger_enemy_drop:
                                            raise RuntimeError()

                                        smaller_drop_entry = smaller_enemy_drop.drop_entries[0]
                                        if len(smaller_drop_entry.hp_percents) != 2:
                                            raise RuntimeError()

                                        smaller_drop_ranks_formatted = smaller_drop_entry.format_ranks()
                                        enemy_and_rank = f"{bigger_enemy_name} ({smaller_drop_ranks_formatted})"
                                        chip_location_parts.append(enemy_and_rank)

                                output += ", ".join(chip_location_parts)
                                #print(f"6 1,2 weird output: {chip_full}: {output}")
                                        #print(f"smaller_enemy_drop: {smaller_enemy_drop}")
                                        #print(f"bigger_enemy_drop: {bigger_enemy_drop}")
                                        #if smaller_enemy_drop
                                        #bigger_drop_ranks_formatted = 
                                #print(f"chip_drop_locations_1 A: {chip_drop_locations_1}")
                                #print(f"chip_drop_locations_2 A: {chip_drop_locations_2}\n")
                            else:
                                if chip_full == "FireBrn2 T":
                                    output += "OldHeatr (LV9~S), {{6CG}} RarOldSt (LV9~S), RarOldS2 (LV7~10)"
                                elif chip_full == "BblStar2 C":
                                    output += "{{6CG}} StarFsh2 (LV9~S), RarStrFs (LV9~S), RarStrF2 (LV7~10)"
                                elif chip_full == "CornSht2 C":
                                    output += "MegaCorn (LV9~S), {{6CF}} RareCorn (LV9~S), {{6CF}} RarCorn2 (LV5~10)"
                                elif chip_full == "CornSht2 D":
                                    output += "MegaCorn (LV7~10), {{6CG}} RareCorn (LV9~S), {{6CG}} RarCorn2 (LV5~10)"
                                elif chip_full == "FireHit2 R":
                                    output += "Chumpy (LV7~10), {{6CG}} RarChampy (LV9~S), {{6CG}} RarChmpy2 (LV5~10)"
                                elif chip_full == "FireHit2 S":
                                    output += "Chumpy (LV9~S), {{6CF}} RarChampy (LV9~S), {{6CF}} RarChmpy2 (LV5~10)"
                                elif chip_full == "Rflectr1 *":
                                    output += "RareMttar ({{6CG2}}: LV5~7, {{6CF2}}: LV5~10)"
                                elif chip_full == "Rflectr2 *":
                                    output += "RareMttar ({{6CG2}}: LV7~S, {{6CF2}}: LV5~7), RareMttr2 ({{6CG2}}: LV9~11, {{6CF2}}: LV5~10)"
                                elif chip_full == "Rflectr3 *":
                                    output += "RareMttr2 ({{6CG2}}: LV7~S, {{6CF2}}: LV9~S)"
                                else:
                                    raise RuntimeError()
                    else:
                        raise RuntimeError()

                    chip_drop_locations = None
                else:
                    chip_drop_locations = chip_drop_locations_1
            elif chip_drop_locations_1 is not None and chip_drop_locations_2 is None:
                chip_drop_locations = chip_drop_locations_1
                chosen_version = version_1
            elif chip_drop_locations_1 is None and chip_drop_locations_2 is not None:
                chip_drop_locations = chip_drop_locations_2
                chosen_version = version_2
            else:
                chip_drop_locations = None

        if chip_drop_locations is not None:
            chip_location_parts = []
            if chosen_version is not None:
                chosen_version_str = f"{{{{{chosen_version}}}}} "
            else:
                chosen_version_str = ""

            for enemy_name, enemy_drop in chip_drop_locations.enemy_drops.items():
                if self.hp_percents_to_name is not None:
                    hp_percent_and_drop_ranks_formatted_parts = []

                    for drop_entry in enemy_drop.drop_entries:
                        drop_ranks_formatted = drop_entry.format_ranks()
                        hp_percent_name = self.hp_percents_to_name[frozenset(drop_entry.hp_percents)]
                        if hp_percent_name == "":
                            hp_percent_and_drop_ranks_formatted = drop_ranks_formatted
                        else:
                            hp_percent_and_drop_ranks_formatted = f"{hp_percent_name}: {drop_ranks_formatted}"
                        hp_percent_and_drop_ranks_formatted_parts.append(hp_percent_and_drop_ranks_formatted)

                    all_hp_percent_and_drop_ranks_formatted = "; ".join(hp_percent_and_drop_ranks_formatted_parts)
                    enemy_and_rank = f"{chosen_version_str}{enemy_name} ({all_hp_percent_and_drop_ranks_formatted})"
                else:
                    if len(enemy_drop.drop_entries) != 1:
                        raise RuntimeError()

                    drop_entry = enemy_drop.drop_entries[0]
                    drop_ranks_formatted = drop_entry.format_ranks()
                    enemy_and_rank = f"{enemy_name} ({drop_ranks_formatted})"

                chip_location_parts.append(enemy_and_rank)

            output += ", ".join(chip_location_parts)
        elif output == "":
            return None

        #print(f"{chip_full}: {output}")
        return output
                        #print(f"3,4 weird version output: {output}")
                        #"VolGear (4RS: 
                        #print(f"enemy_drop_1: {enemy_drop_1}, enemy_drop_2: {enemy_drop_2}")

                    #if len(chip_drop_locations_1.enemy_drops) == 1 and len(chip_drop_locations_2.enemy_drops) == 1:
                    #    enemy_name_1 = next(iter(chip_drop_locations_1.enemy_drops.keys()))
                    #    enemy_name_2 = next(iter(chip_drop_locations_2.enemy_drops.keys()))
                    #    if enemy_name_1 == enemy_name_2:
                            
                        
                    #if game_number == 3:
                    #    if chip_full == "Yo-Yo2 H":
                    #        chip_location_parts = ["Yurt ({{3W2}}: LV7-10
                        
                    #enemy_drops = []
                    #other_version_exclusive_drops = set(chip_drop_locations_2.enemy_drops.keys())
                    #
                    ## C: Dominerd (W: LV7-10; B: LV9-S) 
                    #"""
                    #enemy_drops = [
                    #    EnemyDrop(
                    #        name="Dominerd",
                    #        drop_entries=[
                    #            DropEntry(hp_percents={'<37.5%', '>=37.5%'}, ranks=7,8,9,10)
                    #        ],
                    #        version=3W
                    #    ),
                    #    EnemyDrop(
                    #        name="Dominerd",
                    #        drop_entries=[
                    #            DropEntry(hp_percents={'<37.5%', '>=37.5%'}, ranks=9,10,11)
                    #        ],
                    #        version=3B
                    #    )
                    #]
                    #"""
                    #for enemy_name_1, enemy_drop_1 in chip_drop_locations_1.enemy_drops.items():
                    #    enemy_drop_2 = chip_drop_locations_2.enemy_drops.get(enemy_name_1)
                    #    if enemy_drop_2 is not None:
                    #        other_version_exclusive_drops -= enemy_name_1
                    #        for 


        return output
"""
Shockwav:
H: Mettaur (Mid: LV9-S)
J: Mettaur (High: LV9-S, Mid: LV7-10)
L: Mettaur (Low: LV9-S)
R: Mettaur (High: LV7-10)
U: Mettaur (Low: LV7-10)
"""

nontab_at_start_regex = re.compile(r"^[^\t]+")
multitab_regex = re.compile(r"\t+")

class EnemyDropTables:

    """
    all_chip_drop_locations =
    {
        "Guard1 A": ChipDropLocations(
            name="Guard1 A",
            enemy_drops={
                "Mettaur": EnemyDrop(
                    name="Mettaur",
                    drop_entries=[
                        DropEntry(
                            hp_percent=">37.5%",
                            ranks=[Range(7, 7), Range(8, S)]
                        ),
                        DropEntry(
                            hp_percent="<=37.5%",
                            ranks=[Range(7, 7), Range(8, S)]
                        )                    
                    ]
                ),
                "MettEX": EnemyDrop(
                    name="MettEX",
                    drop_entries=[
                        DropEntry(
                            hp_percent=">37.5%",
                            ranks=[Range(7, 7), Range(8, S)]
                        ),
                        DropEntry(
                            hp_percent="<=37.5%",
                            ranks=[Range(7, 7), Range(8, S)]
                        )                    
                    ]
                )
            }
        ]
    }
    """

    __slots__ = ("line_reader", "hp_percent_drops", "cur_enemy_index", "all_chip_drop_locations", "ignored_enemies", "version")

    def __init__(self, input_filename, ignored_enemies_filename, hp_percent_drops=True, version=None):
        with open(input_filename, "r") as f:
            lines = f.read().splitlines()

        self.line_reader = LineReader(lines, input_filename)
        self.hp_percent_drops = hp_percent_drops
        self.cur_enemy_index = 0
        self.ignored_enemies = {}
        self.version = version

        if ignored_enemies_filename is not None:
            with open(ignored_enemies_filename, "r") as f:
                for line in f:
                    index_as_str, enemy_name = line.split(": ", maxsplit=1)
                    enemy_name = enemy_name.strip()
                    self.ignored_enemies[int(index_as_str)] = enemy_name

    def find_all_enemies(self):
        self.line_reader.reset()
        for line in self.line_reader:
            if line.startswith("Enemy\t"):
                break

        READING_LINE_SEPARATOR = 0
        READING_ENEMY_NAME = 1

        state = READING_LINE_SEPARATOR
        enemy_names = []

        for line in self.line_reader:
            if state == READING_LINE_SEPARATOR:
                if line.startswith("--------------------------------------------------------"):
                    state = READING_ENEMY_NAME
            elif state == READING_ENEMY_NAME:
                enemy_name = line.split("\t", maxsplit=1)[0]
                enemy_names.append(enemy_name)
                state = READING_LINE_SEPARATOR

        output = ""
        output = "".join(f"{enemy_index: >3d}: {enemy_name}\n" for enemy_index, enemy_name in enumerate(enemy_names))
        return output

    def parse_enemy_drop_tables(self):
        self.line_reader.reset()
        
        self.all_chip_drop_locations = {}

        for line in self.line_reader:
            if line.startswith("Enemy\t"):
                break

        for line in self.line_reader:
            if line.startswith("--------------------------------------------------------"):
                break

        while True:
            end_of_file = self.parse_enemy_drop_table()
            if end_of_file:
                break

    def parse_enemy_drop_table(self):
        line = self.line_reader.next()
        enemy_name = line.split("\t", maxsplit=1)[0]
        ignored_enemy = self.ignored_enemies.get(self.cur_enemy_index)
        skip_enemy = False

        if ignored_enemy is not None: 
            if enemy_name != ignored_enemy:
                raise RuntimeError(f"Invalid ignored enemy index/name pair! Expected: ({self.cur_enemy_index}, {ignored_enemy}). Got: ({self.cur_enemy_index}, {enemy_name})")

            skip_enemy = True
        elif enemy_name == "Unused":
            skip_enemy = True
            
        if skip_enemy:
            while True:
                if line.startswith("--------------------------------------------------------"):
                    break
                line = self.line_reader.next().strip()
                
        else:
            #print(f"line: {line}")
            line = nontab_at_start_regex.sub("", line, count=1).strip()
    
            hp_percent = None
    
            FOUND_NEW_REWARD = 0
            ON_CURRENT_REWARD = 1
            SKIP_CURRENT_REWARD = 2
    
            state = FOUND_NEW_REWARD
            drop_entry = None
            reward = None
    
            while True:
                if line.startswith("--------------------------------------------------------"):
                    if state == ON_CURRENT_REWARD:
                        enemy_drop.add_drop_entry(drop_entry)
    
                    break
                elif line == "":
                    if state == ON_CURRENT_REWARD:
                        enemy_drop.add_drop_entry(drop_entry)
                    line = self.line_reader.next().strip()
                    hp_percent = None
                    state = FOUND_NEW_REWARD
                    continue

                if self.hp_percent_drops:
                    cur_hp_percent_and_cur_reward_parts = multitab_regex.split(line)
                    #print(f"cur_hp_percent_and_cur_reward_parts: {cur_hp_percent_and_cur_reward_parts}")
                    cur_hp_percent = cur_hp_percent_and_cur_reward_parts[0]
                    cur_reward_parts = cur_hp_percent_and_cur_reward_parts[1:]
                    if hp_percent is not None:
                        if cur_hp_percent != hp_percent:
                            raise RuntimeError()
                    else:
                        hp_percent = cur_hp_percent
                else:
                    #print(f"line: {line}")
                    cur_reward_parts = multitab_regex.split(line)
    
                #print(f"cur_reward_parts: {cur_reward_parts}")
    
                if state == ON_CURRENT_REWARD:
                    if len(cur_reward_parts) == 3:
                        enemy_drop.add_drop_entry(drop_entry)
                        state = FOUND_NEW_REWARD
                    else:
                        
                        rank, percentage = cur_reward_parts
                        drop_entry.add_rank(rank)
                elif state == SKIP_CURRENT_REWARD and len(cur_reward_parts) == 3:
                    state = FOUND_NEW_REWARD
    
                if state == FOUND_NEW_REWARD:
                    if len(cur_reward_parts) == 3:
                        reward, rank, percentage = cur_reward_parts
                        if not reward.endswith("z") and not reward.startswith("HP+") and not reward.startswith("HP Max"):
                            chip_drop_locations = self.get_chip_drop_locations(reward)
                            enemy_drop = chip_drop_locations.get_enemy_drop(enemy_name)
                            drop_entry = DropEntry.from_hp_percent(hp_percent)
                            drop_entry.add_rank(rank)
                            state = ON_CURRENT_REWARD
                        else:
                            state = SKIP_CURRENT_REWARD
                            enemy_drop = None
                    else:
                        raise RuntimeError(cur_reward_parts)
    
                line = self.line_reader.next().strip()

        self.cur_enemy_index += 1
        return self.line_reader.is_end_of_file_or_last_line()

    def fold_same_drop_entries(self):
        for chip_name, chip_drop_locations in self.all_chip_drop_locations.items():
            for enemy_name, enemy_drop in chip_drop_locations.enemy_drops.items():
                enemy_drop.fold_drop_entries()

    def get_chip_drop_locations(self, name):
        chip_drop_locations = self.all_chip_drop_locations.get(name)

        if chip_drop_locations is None:
            chip_drop_locations = ChipDropLocations(name, self.version)
            self.all_chip_drop_locations[name] = chip_drop_locations

        return chip_drop_locations

class IgnoredEnemy:
    __slots__ = ("index", "name")

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __key(self):
        return (self.name, self.index)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if isinstance(other, IgnoredEnemy):
            return self.__key() == other.__key()
        return NotImplemented

class ChipDropLocations:
    __slots__ = ("name", "enemy_drops", "version")

    def __init__(self, name, version):
        self.name = name
        self.enemy_drops = {}
        self.version = None # version

    def get_enemy_drop(self, enemy_name):
        enemy_drop = self.enemy_drops.get(enemy_name)

        if enemy_drop is None:
            enemy_drop = EnemyDrop(enemy_name, self.version)
            self.enemy_drops[enemy_name] = enemy_drop

        return enemy_drop

    def __eq__(self, other):
        if isinstance(other, ChipDropLocations):
            return self.name == other.name and self.enemy_drops == other.enemy_drops
        return NotImplemented

    def __repr__(self):
        return f"ChipDropLocations(name={self.name}, enemy_drops={self.enemy_drops})"

class EnemyDrop:
    __slots__ = ("enemy_name", "drop_entries", "version")

    def __init__(self, enemy_name, version):
        self.enemy_name = enemy_name
        self.drop_entries = []
        self.version = version

    def __eq__(self, other):
        if isinstance(other, EnemyDrop):
            return self.enemy_name == other.enemy_name and self.drop_entries == other.drop_entries
        return NotImplemented

    def add_drop_entry(self, drop_entry):
        self.drop_entries.append(drop_entry)

    def fold_drop_entries(self):
        if len(self.drop_entries) == 1:
            return

        elif len(self.drop_entries) == 2:
            drop_entries_0 = self.drop_entries[0]
            drop_entries_1 = self.drop_entries[1]
            new_drop_entries = drop_entries_0.create_merged_if_ranks_equal(drop_entries_1)
            if new_drop_entries is not None:
                self.drop_entries = [new_drop_entries]
        elif len(self.drop_entries) == 3:
            # 0=1, 2
            # 0=2, 1
            # 1=2, 0
            # 0=1=2

            drop_entries_0 = self.drop_entries[0]
            drop_entries_1 = self.drop_entries[1]
            drop_entries_2 = self.drop_entries[2]

            new_drop_entries = drop_entries_0.create_merged_if_ranks_equal(drop_entries_1)
            if new_drop_entries is not None:
                other_drop_entries = drop_entries_2
            else:
                new_drop_entries = drop_entries_0.create_merged_if_ranks_equal(drop_entries_2)
                if new_drop_entries is not None:
                    other_drop_entries = drop_entries_1
                else:
                    new_drop_entries = drop_entries_1.create_merged_if_ranks_equal(drop_entries_2)
                    if new_drop_entries is not None:
                        other_drop_entries = drop_entries_0
                    else:
                        other_drop_entries = None

            if other_drop_entries is not None:
                new_drop_entry_2 = new_drop_entries.create_merged_if_ranks_equal(other_drop_entries)
                if new_drop_entry_2 is not None:
                    self.drop_entries = [new_drop_entry_2]
                else:
                    self.drop_entries = [new_drop_entries, other_drop_entries]
            else:
                pass # keep self.drop_entries as is
        else:
            raise RuntimeError(f"drop_entries has len {len(self.drop_entries)}! enemy_name: {self.enemy_name}, drop_entries: {self.drop_entries}")

    def __repr__(self):
        return f"EnemyDrop(name={self.enemy_name}, drop_entries={self.drop_entries})"

class DropEntry:
    __slots__ = ("hp_percents", "ranks", "version")

    def __init__(self, hp_percents, ranks):
        self.hp_percents = hp_percents
        self.ranks = ranks
        self.version = None

    def __eq__(self, other):
        if isinstance(other, DropEntry):
            return self.hp_percents == other.hp_percents and self.ranks == other.ranks
        return NotImplemented

    @classmethod
    def from_hp_percent(cls, hp_percent):
        return cls({hp_percent}, SortedList())

    @classmethod
    def from_merge(cls, drop_entry_1, drop_entry_2):
        hp_percents = drop_entry_1.hp_percents | drop_entry_2.hp_percents
        ranks = drop_entry_1.ranks
        return cls(hp_percents, ranks)

    def add_rank(self, rank):
        if "-" in rank:
            start_rank, end_rank = rank.split(" - ", maxsplit=1)

            start_rank_num = DropEntry.rank_to_int(start_rank)
            end_rank_num = DropEntry.rank_to_int(end_rank)

            for rank_num in range(start_rank_num, end_rank_num+1):
                self.ranks.add(rank_num)
        else:
            self.ranks.add(DropEntry.rank_to_int(rank))

    def create_merged_if_ranks_equal(self, other):
        if self.ranks == other.ranks:
            return DropEntry.from_merge(self, other)
        else:
            return None

    def format_ranks(self):
        rank_parts = []
        ranks_1_onwards_plus_sentinel = list(self.ranks[1:]) + [100]
        start_rank = self.ranks[0]
        prev_rank = start_rank

        for rank in ranks_1_onwards_plus_sentinel:
            if rank != prev_rank + 1:
                if start_rank == prev_rank:
                    rank_parts.append(DropEntry.int_to_rank(start_rank))
                else:
                    end_rank = prev_rank
                    rank_parts.append(f"{DropEntry.int_to_rank(start_rank)}~{DropEntry.int_to_rank(end_rank)}")

                start_rank = rank

            prev_rank = rank

        output = ""
        output += "LV"
        output += ", ".join(rank_parts)

        return output

    @staticmethod
    def rank_to_int(rank):
        if rank == "S":
            return 11
        elif rank == "S+":
            return 12
        elif rank == "S++":
            return 13
        else:
            return int(rank, 10)

    @staticmethod
    def int_to_rank(rank):
        if rank == 11:
            return "S"
        elif rank == 12:
            return "S+"
        elif rank == 13:
            return "S++"
        else:
            return str(rank)

    def __repr__(self):
        return f"DropEntry(hp_percents={self.hp_percents}, ranks={','.join(str(rank) for rank in self.ranks)})"

def generate_droprate_enemies():
    droprate_filenames = [
        "bn1_drops.txt",
        "bn2_drops.txt",
        "bn3w_drops.txt",
        "bn3b_drops.txt",
        "bn4rs_drops.txt",
        "bn4bm_drops.txt",
        "bn5p_drops.txt",
        "bn5c_drops.txt",
        "bn6g_drops.txt",
        "bn6f_drops.txt",
    ]

    for droprate_filename in droprate_filenames:
        enemy_drop_table = EnemyDropTables(droprate_filename, None)
        enemies = enemy_drop_table.find_all_enemies()
        droprate_stem = pathlib.Path(droprate_filename).stem
        output_filename = f"{droprate_stem}_enemies_out.txt"
        enemies = f"== {droprate_stem} ==\n" + enemies
        with open(output_filename, "w+") as f:
            f.write(enemies)

def test_dump_bn1_enemy_drops():
    droprate_filenames = [
        ("bn1_drops.txt", "bn1_ignored_enemies.txt"),
        ("bn2_drops.txt", None),
        #"bn3w_drops.txt",
        #"bn3b_drops.txt",
        #"bn4rs_drops.txt",
        #"bn4bm_drops.txt",
        #"bn5p_drops.txt",
        #"bn5c_drops.txt",
        #"bn6g_drops.txt",
        #"bn6f_drops.txt",
    ]

    hp_percent_drops = False

    for droprate_filename, ignored_enemies_filename in droprate_filenames:
        enemy_drop_table = EnemyDropTables(droprate_filename, ignored_enemies_filename, hp_percent_drops=hp_percent_drops)
        enemy_drop_table.parse_enemy_drop_tables()
    
        output = []
    
        for chip_name, chip_drop_locations in enemy_drop_table.all_chip_drop_locations.items():
            output.append(f"{chip_name}:\n")
    
            for enemy_name, enemy_drop in chip_drop_locations.enemy_drops.items():
                output.append(f"  {enemy_name}:\n")
                for drop_entry in enemy_drop.drop_entries:
                    output.append(f"    {drop_entry.hp_percents}: {', '.join(str(rank) for rank in drop_entry.ranks)}\n")

        droprate_stem = pathlib.Path(droprate_filename).stem
        output_filename = f"{droprate_stem}_by_chips.txt"

        with open(output_filename, "w+") as f:
            f.write("".join(output))

        hp_percent_drops = True

def main():
    MODE = 1
    if MODE == 0:
        generate_droprate_enemies()
    elif MODE == 1:
        test_dump_bn1_enemy_drops()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
