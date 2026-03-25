import sys
import os
import struct
import argparse
from rich.console import Console
from rich.text import Text

E_OBJECT_DOOR = 0x0803
E_OBJECT_WALKWAY = 0x0806
E_OBJECT_SLIDING_POLE = 0x0809
E_OBJECT_LADDER = 0x080C
E_OBJECT_DOOR_BELL = 0x080F
E_OBJECT_LIGHTNING = 0x0812
E_OBJECT_FORCEFIELD = 0x0815
E_OBJECT_MUMMY = 0x0818
E_OBJECT_KEY = 0x081B
E_OBJECT_LOCK = 0x081E
E_OBJECT_RAY_GUN = 0x0824
E_OBJECT_TELEPORT = 0x0827
E_OBJECT_TRAP_DOOR = 0x082A
E_OBJECT_CONVEYOR = 0x082D
E_OBJECT_FRANKENSTEIN = 0x0830
E_OBJECT_TEXT = 0x0833
E_OBJECT_IMAGE = 0x0836

VALID_IDS = {
    E_OBJECT_DOOR, E_OBJECT_WALKWAY, E_OBJECT_SLIDING_POLE, E_OBJECT_LADDER,
    E_OBJECT_DOOR_BELL, E_OBJECT_LIGHTNING, E_OBJECT_FORCEFIELD, E_OBJECT_MUMMY,
    E_OBJECT_KEY, E_OBJECT_LOCK, E_OBJECT_RAY_GUN,
    E_OBJECT_TELEPORT, E_OBJECT_TRAP_DOOR, E_OBJECT_CONVEYOR, E_OBJECT_FRANKENSTEIN,
    E_OBJECT_TEXT, E_OBJECT_IMAGE, 0x160A, 0x2A6D, 0x0839, 0x0821
}

C64_COLORS = {
    0: "black", 1: "white", 2: "red", 3: "cyan", 4: "purple", 5: "green",
    6: "blue", 7: "yellow", 8: "orange", 9: "brown", 10: "light_red",
    11: "grey37", 12: "grey50", 13: "light_green", 14: "light_blue", 15: "grey82",
}

LEGEND = """
[bold white]LEGEND:[/bold white]
[white][---][/white] : Door
[white] ● [/white]   : Doorbell / Button
[white] = [/white]   : Walkway
[white] # [/white]   : Ladder
[white] | [/white]   : Sliding Pole
[white] k [/white]   : Key
[white] X [/white]   : Lock
[white] M [/white]   : Mummy
[white] F [/white]   : Frankenstein
[white] G [/white]   : Ray Gun
[white] T [/white]   : Matter Transmitter (Teleport)
[white] t [/white]   : Teleport Target
[white] z [/white]   : Forcefield
[white] L [/white]   : Lightning Machine
[white] C [/white]   : Conveyor
[white] _ [/white]   : Trap Door
[red bold] EXIT [/red bold]: Escape Door!
"""

class Room:
    def __init__(self, number):
        self.number = number
        self.color, self.map_x, self.map_y = 0, 0, 0
        self.file_dir_ptr = 0
        self.objects = []

class Castle:
    def __init__(self, name, data, no_color=False):
        self.name, self.data, self.rooms = name, data, []
        self.console = Console(force_terminal=True, width=10000, no_color=no_color)
        self.parse()

    def read_word(self, offset):
        if offset + 2 > len(self.data): return None
        return struct.unpack("<H", self.data[offset:offset+2])[0]

    def parse(self):
        offset = 0x102
        dir_entries = []
        while offset < len(self.data):
            marker = self.data[offset]
            if marker == 0xFF: break
            ptr = self.read_word(offset + 6)
            if ptr < 0x7800: break
            room = Room(len(self.rooms))
            room.color, room.map_x, room.map_y = self.data[offset], self.data[offset+1], self.data[offset+2]
            room.file_dir_ptr = ptr - 0x7800 + 2
            self.rooms.append(room)
            dir_entries.append(room.file_dir_ptr)
            offset += 8
        
        dir_entries.sort()
        for room in self.rooms:
            if 0 < room.file_dir_ptr < len(self.data):
                end_offset = len(self.data)
                for entry in dir_entries:
                    if entry > room.file_dir_ptr:
                        end_offset = entry
                        break
                self.parse_objects(room, end_offset)

    def parse_objects(self, room, end_offset):
        offset = room.file_dir_ptr
        while offset < end_offset - 1:
            func = self.read_word(offset)
            if func not in VALID_IDS:
                offset += 1
                continue
            
            offset += 2
            if func == E_OBJECT_DOOR:
                count = self.data[offset]; offset += 1
                for _ in range(count):
                    room.objects.append(('Door', self.data[offset], self.data[offset+1], self.data[offset+7] != 0))
                    offset += 8
            elif func == E_OBJECT_DOOR_BELL:
                count = self.data[offset]; offset += 1
                for _ in range(count):
                    room.objects.append(('DoorBell', self.data[offset], self.data[offset+1])); offset += 3
            elif func in [E_OBJECT_WALKWAY, E_OBJECT_SLIDING_POLE, E_OBJECT_LADDER]:
                name = {E_OBJECT_WALKWAY: 'Walkway', E_OBJECT_SLIDING_POLE: 'Pole', E_OBJECT_LADDER: 'Ladder'}[func]
                while offset < end_offset and self.data[offset] != 0:
                    if self.read_word(offset) in VALID_IDS: break
                    room.objects.append((name, self.data[offset+1], self.data[offset+2], self.data[offset]))
                    offset += 3
                offset += 1
            elif func == E_OBJECT_LIGHTNING:
                while offset < end_offset and self.data[offset] != 0x20:
                    if self.read_word(offset) in VALID_IDS: break
                    if self.data[offset] & 0x80: room.objects.append(('LightningSwitch', self.data[offset+1], self.data[offset+2]))
                    else: room.objects.append(('LightningMachine', self.data[offset+1], self.data[offset+2], self.data[offset+3]))
                    offset += 8
                offset += 1
            elif func == E_OBJECT_TELEPORT:
                color = (self.data[offset+2] + 2) % 16
                room.objects.append(('Teleport', self.data[offset], self.data[offset+1], color)); offset += 3
                while offset < end_offset and self.data[offset] != 0:
                    if self.read_word(offset) in VALID_IDS: break
                    room.objects.append(('TeleportTarget', self.data[offset], self.data[offset+1], color)); offset += 2
                offset += 1
            elif func == E_OBJECT_KEY:
                while offset < end_offset and self.data[offset] != 0:
                    if self.read_word(offset) in VALID_IDS: break
                    room.objects.append(('Key', self.data[offset+2], self.data[offset+3], self.data[offset])); offset += 4
                offset += 1
            elif func == E_OBJECT_MUMMY:
                while offset < end_offset and self.data[offset] != 0:
                    if self.read_word(offset) in VALID_IDS: break
                    room.objects.append(('Mummy', self.data[offset+1], self.data[offset+2])); offset += 3
                offset += 1
            elif func in [E_OBJECT_FORCEFIELD, E_OBJECT_LOCK, E_OBJECT_IMAGE]:
                name = {E_OBJECT_FORCEFIELD: 'Forcefield', E_OBJECT_LOCK: 'Lock', E_OBJECT_IMAGE: 'Image'}[func]
                while offset < end_offset and self.data[offset] != 0:
                    if self.read_word(offset) in VALID_IDS: break
                    room.objects.append((name, self.data[offset], self.data[offset+1])); offset += 2
                offset += 1
            elif func in [E_OBJECT_TEXT, 0x2A6D, 0x0839]:
                while offset < end_offset and self.data[offset] != 0:
                    if self.read_word(offset) in VALID_IDS: break
                    x, y, col, text = self.data[offset], self.data[offset+1], self.data[offset+2], ""
                    offset += 4
                    while True:
                        if offset >= len(self.data): break
                        c = self.data[offset]; text += chr(c & 0x7F); offset += 1
                        if c & 0x80: break
                    room.objects.append(('Text', x, y, text, col))
                offset += 1
            elif func in [E_OBJECT_RAY_GUN, E_OBJECT_TRAP_DOOR, E_OBJECT_CONVEYOR, E_OBJECT_FRANKENSTEIN]:
                name = {E_OBJECT_RAY_GUN: 'RayGun', E_OBJECT_TRAP_DOOR: 'TrapDoor', E_OBJECT_CONVEYOR: 'Conveyor', E_OBJECT_FRANKENSTEIN: 'Frankie'}[func]
                while offset < end_offset and self.data[offset] != 0x80:
                    if self.read_word(offset) in VALID_IDS: break
                    room.objects.append((name, self.data[offset+1], self.data[offset+2])); offset += 7 if func in [E_OBJECT_RAY_GUN, E_OBJECT_FRANKENSTEIN] else 5
                offset += 1

    def get_room_grid(self, room):
        grid = [[(' ', 1) for _ in range(42)] for _ in range(27)]
        floor_color = room.color & 0xF
        for i in range(42): grid[0][i] = grid[26][i] = ('-', 1)
        for i in range(27): grid[i][0] = grid[i][41] = ('|', 1)
        grid[0][0] = grid[0][41] = grid[26][0] = grid[26][41] = ('+', 1)
        for obj in room.objects:
            type = obj[0]
            if type == 'Text':
                x, y, text, col = (obj[1] >> 2) - 4 + 1, (obj[2] >> 3) + 1, obj[3], obj[4]
                for i, c in enumerate(text):
                    if 1 <= y < 26 and 1 <= x + i < 41: grid[y][x+i] = (c, col)
                continue
            x, y = (obj[1] >> 2) - 4 + 1, (obj[2] >> 3) + 1
            if type in ['Frankie', 'Mummy']: y += 2
            if x >= 41 or y < 1 or y >= 26: continue
            if type == 'Walkway':
                for i in range(obj[3]):
                    if 1 <= x + i < 41: grid[y][x+i] = ('=', floor_color)
            elif type in ['Ladder', 'Pole']:
                char = '#' if type == 'Ladder' else '|'
                for i in range(obj[3]):
                    if 1 <= x < 41 and 1 <= y + i < 26: grid[y+i][x] = (char, floor_color)
            elif type == 'Door':
                is_exit, color = obj[3], 2 if obj[3] else floor_color
                for dy in range(4):
                    for dx in range(5):
                        if 1 <= y + dy < 26 and 1 <= x + dx < 41:
                            c = ["-----", "EXIT ", " DOOR", "-----"][dy][dx] if is_exit else (('[' if dx == 0 else ']') if dx in [0,4] else ('-' if dy in [0,3] else ' '))
                            grid[y+dy][x+dx] = (c, color)
            elif type == 'Key': grid[y][x] = ('k', obj[3])
            elif type == 'Lock': grid[y][x] = ('X', floor_color)
            elif type == 'Mummy': grid[y][x] = ('M', 1)
            elif type == 'Frankie': grid[y][x] = ('F', 1)
            elif type == 'RayGun': grid[y][x] = ('G', 1)
            elif type == 'Teleport' or type == 'TeleportTarget': grid[y][x] = ('T' if type == 'Teleport' else 't', obj[3])
            elif type == 'Forcefield': grid[y][x] = ('z', 3)
            elif type == 'LightningMachine': grid[y][x] = ('L', 3)
            elif type == 'Conveyor': grid[y][x] = ('C', floor_color)
            elif type == 'TrapDoor': grid[y][x] = ('_', floor_color)
            elif type == 'DoorBell': grid[y][x] = ('●', floor_color)
        return grid

    def export_map(self):
        if not self.rooms: return
        xs = sorted(list(set(r.map_x for r in self.rooms)))
        ys = sorted(list(set(r.map_y for r in self.rooms)))
        xi = {x: i for i, x in enumerate(xs)}
        yi = {y: i for i, y in enumerate(ys)}
        map_w, map_h = len(xs) * 42 + 2, len(ys) * 27 + 2
        global_grid = [[(' ', 1) for _ in range(map_w)] for _ in range(map_h)]
        for room in self.rooms:
            gx, gy = xi[room.map_x] * 42 + 1, yi[room.map_y] * 27 + 1
            room_grid = self.get_room_grid(room)
            for ry in range(27):
                for rx in range(42):
                    char, col = room_grid[ry][rx]
                    if char != ' ' or col != 1 or ry in [0, 26] or rx in [0, 41]:
                        global_grid[gy + ry][gx + rx] = (char, col)
            label = f"ROOM {room.number}"
            for i, c in enumerate(label): global_grid[gy-1][gx+i] = (c, 1)
        self.console.print(LEGEND)
        for row in global_grid:
            line = Text()
            for char, col in row: line.append(char, style=C64_COLORS.get(col & 0xF, "white"))
            self.console.print(line, soft_wrap=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("castle_file")
    parser.add_argument("--nocolor", action="store_true")
    args = parser.parse_args()
    if not os.path.exists(args.castle_file):
        alt = os.path.join("run", "data", "castles", args.castle_file)
        if os.path.exists(alt): args.castle_file = alt
    with open(args.castle_file, "rb") as f: data = f.read()
    Castle(os.path.basename(args.castle_file), data, no_color=args.nocolor).export_map()

if __name__ == "__main__": main()
