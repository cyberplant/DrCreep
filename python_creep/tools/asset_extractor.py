import os
import struct
from PIL import Image

# C64 Palette
C64_PALETTE = [
    (0, 0, 0), (255, 255, 255), (136, 0, 0), (170, 255, 238),
    (204, 68, 204), (0, 204, 85), (0, 0, 170), (238, 238, 119),
    (212, 133, 61), (102, 68, 0), (255, 119, 119), (51, 51, 51),
    (119, 119, 119), (170, 255, 102), (0, 136, 255), (187, 187, 187)
]

def extract_sprites(object_file, output_dir):
    with open(object_file, "rb") as f:
        data = f.read()
    
    # Pointer table at address 0x603B
    # File offset = 0x603B - 0x800 + 2 = 0x583D
    table_offset = 0x583D
    
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(256): # Max sprites
        ptr_offset = table_offset + (i * 2)
        ptr = struct.unpack("<H", data[ptr_offset:ptr_offset+2])[0]
        
        if ptr == 0: break # End of table (or invalid)
        
        file_offset = ptr - 0x800 + 2
        if file_offset >= len(data): continue
        
        # Descriptor
        width_blocks = data[file_offset]
        height = data[file_offset + 1]
        flags = data[file_offset + 2]
        
        sprite_data = data[file_offset + 3:]
        
        # Width in pixels: each block is 4 pixels in multicolor, or 8 in single color?
        # C++ source: tmpWidth << 2 (width * 4)
        width_px = width_blocks * 4
        
        if width_px == 0 or height == 0: continue
        
        img = Image.new("RGB", (width_px, height), (0, 0, 0))
        pixels = img.load()
        
        # Draw multicolor sprite (based on src/vic-ii/sprite.cpp)
        # 2 bits per pixel
        data_ptr = 0
        for y in range(height):
            for x_block in range(width_blocks):
                byte = sprite_data[data_ptr]
                data_ptr += 1
                
                # Each byte has 4 multicolor pixels
                for p in range(4):
                    # Bits: 76 54 32 10
                    shift = (3 - p) * 2
                    bits = (byte >> shift) & 0x03
                    
                    color = (0, 0, 0)
                    if bits == 0x01: color = C64_PALETTE[10] # Light Red (Multi 0)
                    elif bits == 0x02: color = C64_PALETTE[1] # White (Primary)
                    elif bits == 0x03: color = C64_PALETTE[13] # Light Green (Multi 1)
                    
                    if bits != 0:
                        # Draw 2x1 pixel (since multicolor pixels are double-wide)
                        px = (x_block * 4 + p)
                        if px < width_px:
                            pixels[px, y] = color

        img.save(os.path.join(output_dir, f"sprite_{i:03d}.png"))
    
    print(f"Extracted sprites to {output_dir}")

def extract_tiles(char_rom, output_path):
    with open(char_rom, "rb") as f:
        data = f.read()
    
    num_tiles = len(data) // 8
    cols = 32
    rows = (num_tiles + cols - 1) // cols
    
    img = Image.new("1", (cols * 8, rows * 8), 0)
    pixels = img.load()
    
    for i in range(num_tiles):
        tile_data = data[i*8 : (i+1)*8]
        tx = (i % cols) * 8
        ty = (i // cols) * 8
        
        for y in range(8):
            byte = tile_data[y]
            for x in range(8):
                if (byte >> (7 - x)) & 1:
                    pixels[tx + x, ty + y] = 1
                    
    img.save(output_path)
    print(f"Extracted tiles to {output_path}")

if __name__ == "__main__":
    extract_sprites("run/data/OBJECT", "data/extracted_sprites")
    extract_tiles("run/data/CHAR.ROM", "data/tileset.png")
