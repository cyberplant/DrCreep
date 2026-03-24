import sys
import os
import struct
import argparse
from rich.console import Console
from rich.text import Text
from python_creep.engine.parser import CastleParser

C64_COLORS = {
    0: "black", 1: "white", 2: "red", 3: "cyan", 4: "purple", 5: "green",
    6: "blue", 7: "yellow", 8: "dark_orange", 9: "brown", 10: "orange_red1",
    11: "grey37", 12: "grey50", 13: "light_green", 14: "light_sky_blue1", 15: "grey82",
}

class TestExporter:
    def __init__(self, castle_parser, no_color=False):
        self.parser = castle_parser
        self.console = Console(width=10000, no_color=no_color)

    def get_room_grid(self, room):
        width, height = 80, 50
        grid = [[(' ', 1) for _ in range(82)] for _ in range(52)]
        floor_color = room.color & 0xF
        
        for i in range(82): grid[0][i] = grid[51][i] = ('-', 1)
        for i in range(52): grid[i][0] = grid[i][81] = ('|', 1)
        grid[0][0] = grid[0][81] = grid[51][0] = grid[51][81] = ('+', 1)

        def py(y): return (y // 4) + 1
        def px(x): return 2*((x >> 2) - 4) + 1

        # 1. Walkways
        for obj in room.objects:
            if obj['type'] == 'walkway':
                gx, gy = px(obj['x']), py(obj['y'])
                if 1 <= gy < 51:
                    for i in range(obj['length'] * 2):
                        if 1 <= gx + i < 81: grid[gy][gx+i] = ('=', floor_color)

        # 2. Objects
        for obj in room.objects:
            type = obj['type']
            gx, gy = px(obj['x']), py(obj['y'])
            
            if type == 'text':
                for i, char in enumerate(obj['text']):
                    if 1 <= gy < 51 and 1 <= gx + i*2 < 81:
                        grid[gy][gx + i*2] = (char, obj['color'])
                continue

            if type == 'walkway': continue

            if type == 'door':
                color = 2 if obj['is_exit'] else floor_color
                for dy in range(8):
                    for dx in range(10):
                        # Door bottom sits exactly on floor row.
                        # Height is 8. Bottom at gy+8.
                        ty, tx = gy + dy, gx + dx
                        if 1 <= ty < 51 and 1 <= tx < 81:
                            c = ' '
                            if obj['is_exit']:
                                labels = ["----------", " EXIT DOOR ", "----------"]
                                if 1 <= dy <= 3: c = labels[dy-1][dx]
                            else:
                                if dx in [0,9]: c = '[' if dx == 0 else ']'
                                elif dy in [0,7]: c = '-'
                                else: c = '░'
                            grid[ty][tx] = (c, color)
            elif type in ['ladder', 'pole']:
                char = '#' if type == 'ladder' else '|'
                max_w_ty = 0
                for w in room.objects:
                    if w['type'] == 'walkway':
                        if w['x'] <= obj['x'] <= w['x'] + w['length'] * 4:
                            w_ty = py(w['y'])
                            if w_ty > max_w_ty and w_ty >= gy:
                                max_w_ty = w_ty
                                
                draw_len = obj['length'] * 2
                for i in range(draw_len):
                    ty = gy + i
                    if max_w_ty > 0 and ty > max_w_ty:
                        break
                    if 1 <= ty < 51 and 1 <= gx < 81:
                        grid[ty][gx] = (char, floor_color)
            elif type == 'key':
                if 1 <= gy + 7 < 51: grid[gy+7][gx] = ('k', obj['color'])
            elif type == 'lock':
                # Lock at head level above walkway (gy + 5)
                if 1 <= gy + 5 < 51: grid[gy+5][gx] = ('X', obj['color'])
            elif type == 'teleport':
                if 1 <= gy + 3 < 51: grid[gy+3][gx] = ('T', obj['color'])
            elif type == 'teleport_target':
                if 1 <= gy + 7 < 51: grid[gy+7][gx] = ('t', obj['color'])
            elif type == 'doorbell':
                # Button at head level (gy + 5)
                if 1 <= gy + 5 < 51: grid[gy+5][gx] = ('●', floor_color)
            elif type == 'forcefield_switch':
                if 1 <= gy + 5 < 51: grid[gy+5][gx] = ('S', 3)
            elif type == 'forcefield':
                for dy in range(0, 8):
                    ty = gy + dy
                    if 1 <= ty < 51: grid[ty][x_grid] = ('z' if dy == 0 else '.', 3)
            elif type == 'mummy_release':
                if 1 <= gy + 7 < 51: grid[gy+7][gx] = ('M', 1)
            elif type == 'mummy_tomb':
                for dy in range(4):
                    for dx in range(-2, 3):
                        ty, tx = gy + 4 + dy, gx + dx
                        if 1 <= ty < 51 and 1 <= tx < 81: grid[ty][tx] = ('#', 2)
            elif type == 'lightning_machine':
                if 1 <= gy + 7 < 51: grid[gy+7][gx] = ('L', 3)
            elif type == 'lightning_switch':
                if 1 <= gy + 5 < 51: grid[gy+5][gx] = ('S', 3)

        return grid

    def print_grid(self, grid):
        for row in grid:
            line = Text()
            for char, col in row: line.append(char, style=C64_COLORS.get(col & 0xF, "white"))
            self.console.print(line, soft_wrap=True)

    def export_map(self, room_num=None):
        if not self.parser.rooms: return
        if room_num is not None:
            if room_num >= len(self.parser.rooms): return
            self.print_grid(self.get_room_grid(self.parser.rooms[room_num]))
            return
        xs = sorted(list(set(r.map_x for r in self.parser.rooms))); ys = sorted(list(set(r.map_y for r in self.parser.rooms)))
        xi, yi = {x: i for i, x in enumerate(xs)}, {y: i for i, y in enumerate(ys)}
        map_w, map_h = len(xs) * 82 + 2, len(ys) * 52 + 2
        global_grid = [[(' ', 1) for _ in range(map_w)] for _ in range(map_h)]
        for room in self.parser.rooms:
            gx, gy = xi[room.map_x] * 82 + 1, yi[room.map_y] * 52 + 1
            room_grid = self.get_room_grid(room)
            for ry in range(52):
                for rx in range(82):
                    char, col = room_grid[ry][rx]
                    if char != ' ' or col != 1 or ry in [0, 51] or rx in [0, 81]:
                        if gy + ry < map_h and gx + rx < map_w: global_grid[gy + ry][gx + rx] = (char, col)
            label = f"ROOM {room.number}"
            for i, c in enumerate(label):
                if gy-1 >= 0 and gx+i < map_w: global_grid[gy-1][gx+i] = (c, 1)
        for row in global_grid:
            line = Text()
            for char, col in row: line.append(char, style=C64_COLORS.get(col & 0xF, "white"))
            self.console.print(line, soft_wrap=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("castle_file"); parser.add_argument("--room", type=int)
    args = parser.parse_args()
    if not os.path.exists(args.castle_file):
        alt = os.path.join("run", "data", "castles", args.castle_file)
        if os.path.exists(alt): args.castle_file = alt
    TestExporter(CastleParser(args.castle_file)).export_map(room_num=args.room)
