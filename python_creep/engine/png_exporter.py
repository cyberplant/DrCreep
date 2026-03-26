import os
import sys
import struct
from PIL import Image

# Add current directory to path to import engine modules
sys.path.append(os.getcwd())

from engine.parser import CastleParser

C64_PALETTE = {
    0: (0, 0, 0),       # Black
    1: (255, 255, 255), # White
    2: (136, 0, 0),     # Red
    3: (170, 255, 238), # Cyan
    4: (204, 68, 204),  # Purple
    5: (0, 204, 85),    # Green
    6: (0, 0, 170),     # Blue
    7: (238, 238, 119), # Yellow
    8: (212, 133, 61),  # Orange
    9: (102, 68, 0),    # Brown
    10: (255, 119, 119),# Light Red
    11: (51, 51, 51),   # Grey 1
    12: (119, 119, 119),# Grey 2
    13: (170, 255, 102),# Light Green
    14: (0, 136, 255),  # Light Blue
    15: (187, 187, 187),# Grey 3
}

class PNGExporter:
    def __init__(self, char_rom_path):
        if not os.path.exists(char_rom_path):
            raise FileNotFoundError(f"CHAR.ROM not found at {char_rom_path}")
        with open(char_rom_path, "rb") as f:
            self.char_data = f.read()

    def get_char_pixels(self, char_code):
        offset = (char_code % 512) * 8
        if offset + 8 > len(self.char_data):
            return [0] * 64
        
        pixels = []
        for i in range(8):
            byte = self.char_data[offset + i]
            for bit in range(7, -1, -1):
                pixels.append((byte >> bit) & 1)
        return pixels

    def ascii_to_screen_code(self, char):
        c = ord(char)
        if 64 <= c <= 95:
            return c - 64
        if 32 <= c <= 63:
            return c
        if 96 <= c <= 127:
            return c - 64
        return c & 0x3F # Fallback for other PETSCII-like ranges

    def draw_char(self, pixels, x_char, y_char, char, fg_color, bg_color=0):
        # Allow passing either a character string or an integer code
        char_code = self.ascii_to_screen_code(char) if isinstance(char, str) else char
        char_pixels = self.get_char_pixels(char_code)
        rgb_fg = C64_PALETTE.get(fg_color, (255, 255, 255))
        rgb_bg = C64_PALETTE.get(bg_color, (0, 0, 0))
        
        for py in range(8):
            for px in range(8):
                val = char_pixels[py * 8 + px]
                target_x = x_char * 8 + px
                target_y = y_char * 8 + py
                if 0 <= target_x < pixels.width and 0 <= target_y < pixels.height:
                    pixels.putpixel((target_x, target_y), rgb_fg if val else rgb_bg)

    def render_room(self, room_data, output_path):
        # 40x25 is standard C64, plus borders -> 42x27
        width_chars = 42
        height_chars = 27
        
        img = Image.new("RGB", (width_chars * 8, height_chars * 8), C64_PALETTE[0])
        
        # Border
        for x in range(width_chars):
            self.draw_char(img, x, 0, '-', 1)
            self.draw_char(img, x, height_chars-1, '-', 1)
        for y in range(height_chars):
            self.draw_char(img, 0, y, ']', 1)
            self.draw_char(img, width_chars-1, y, ']', 1)

        floor_color = room_data.color & 0x0F
        
        # Draw Objects
        for obj in room_data.objects:
            obj_type = obj['type']
            # Using the transformation from castle_exporter.py
            x_char = (obj['x'] >> 2) - 4 + 1
            y_char = (obj['y'] >> 3) + 1
            
            if obj_type == 'walkway':
                for i in range(obj['length']):
                    self.draw_char(img, x_char + i, y_char, 64, floor_color) # Screen code 64 is often a horizontal bar
            elif obj_type == 'ladder':
                for i in range(obj['length']):
                    self.draw_char(img, x_char, y_char + i, '#', floor_color)
            elif obj_type == 'pole':
                for i in range(obj['length']):
                    self.draw_char(img, x_char, y_char + i, ']', floor_color)
            elif obj_type == 'door':
                color = 2 if obj['is_exit'] else floor_color
                for dy in range(4):
                    for dx in range(5):
                        char = '#'
                        if dx == 0: char = '['
                        elif dx == 4: char = ']'
                        elif dy == 0 or dy == 3: char = '-'
                        self.draw_char(img, x_char + dx, y_char + dy, char, color)
            elif obj_type == 'doorbell':
                self.draw_char(img, x_char, y_char, 81, floor_color) # 'Q' dot
            elif obj_type == 'text':
                for i, char in enumerate(obj['text']):
                    self.draw_char(img, x_char + i, y_char, char, obj['color'])
            elif obj_type == 'key':
                self.draw_char(img, x_char, y_char, 'K', obj['color'])
            elif obj_type == 'lock':
                self.draw_char(img, x_char, y_char, 'X', floor_color)
            elif obj_type == 'mummy_tomb':
                for dy in range(3):
                    for dx in range(5):
                        self.draw_char(img, x_char + dx, y_char + dy, '#', 2)
            elif obj_type == 'mummy_release':
                self.draw_char(img, x_char, y_char, 'M', 1)
            elif obj_type == 'frankie':
                self.draw_char(img, x_char, y_char, 'F', 1)
            elif obj_type == 'raygun':
                for i in range(6):
                    self.draw_char(img, x_char + i, y_char, '=', 2)
            elif obj_type == 'teleport':
                self.draw_char(img, x_char, y_char, 'T', obj['color'])
            elif obj_type == 'teleport_target':
                self.draw_char(img, x_char, y_char, 't', obj['color'])

        img.save(output_path)
        print(f"Saved room to {output_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 engine/png_exporter.py <castle_file> [room_num]")
        return
    
    castle_file = sys.argv[1]
    room_num = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    
    char_rom = "run/data/CHAR.ROM"
    exporter = PNGExporter(char_rom)
    parser = CastleParser(castle_file)
    
    if room_num >= len(parser.rooms):
        print(f"Error: Room {room_num} not found. Max room: {len(parser.rooms)-1}")
        return
        
    room = parser.rooms[room_num]
    exporter.render_room(room, f"room_{room_num}.png")

if __name__ == "__main__":
    main()
