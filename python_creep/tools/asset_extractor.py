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
        
        is_multicolor = (flags & 0x80) != 0
        width_px = width_blocks * 4 if is_multicolor else width_blocks * 8
        
        if width_px == 0 or height == 0: continue
        
        img = Image.new("RGBA", (width_px, height), (0, 0, 0, 0))
        pixels = img.load()
        
        data_ptr = 0
        for y in range(height):
            for x_block in range(width_blocks):
                byte = sprite_data[data_ptr]
                data_ptr += 1
                
                if is_multicolor:
                    # 2 bits per pixel
                    for p in range(4):
                        shift = (3 - p) * 2
                        bits = (byte >> shift) & 0x03
                        
                        color = None
                        if bits == 0x01: color = C64_PALETTE[10] + (255,) # Light Red (Multi 0)
                        elif bits == 0x02: color = C64_PALETTE[1] + (255,) # White (Primary)
                        elif bits == 0x03: color = C64_PALETTE[13] + (255,) # Light Green (Multi 1)
                        
                        if color:
                            px = (x_block * 4 + p)
                            if px < width_px: pixels[px, y] = color
                else:
                    # 1 bit per pixel (High-Res)
                    for p in range(8):
                        bit = (byte >> (7 - p)) & 1
                        if bit:
                            px = (x_block * 8 + p)
                            if px < width_px: pixels[px, y] = C64_PALETTE[1] + (255,)

        img.save(os.path.join(output_dir, f"sprite_{i:03d}.png"))
    
    print(f"Extracted sprites to {output_dir}")

def extract_tiles(char_rom, output_path):
    with open(char_rom, "rb") as f:
        data = f.read()
    
    num_tiles = len(data) // 8
    cols = 32
    rows = (num_tiles + cols - 1) // cols
    
    img = Image.new("RGBA", (cols * 8, rows * 8), (0, 0, 0, 0))
    pixels = img.load()
    
    for i in range(num_tiles):
        tile_data = data[i*8 : (i+1)*8]
        tx = (i % cols) * 8
        ty = (i // cols) * 8
        
        for y in range(8):
            byte = tile_data[y]
            for x in range(8):
                if (byte >> (7 - x)) & 1:
                    pixels[tx + x, ty + y] = (255, 255, 255, 255)
                    
    img.save(output_path)
    print(f"Extracted tiles to {output_path}")

def extract_custom_tiles(object_file, output_path):
    with open(object_file, "rb") as f:
        f.seek(2) # Skip PRG header
        data = f.read()
    
    # Custom tiles usually start at memory 0x1000
    # Content is at 0x800 in mMemory, so 0x1000 is offset 0x800
    tiles_offset = 0x800
    tiles_data = data[tiles_offset : tiles_offset + 2048] # 256 tiles
    
    num_tiles = len(tiles_data) // 8
    cols = 16
    rows = (num_tiles + cols - 1) // cols
    
    img = Image.new("RGBA", (cols * 8, rows * 8), (0, 0, 0, 0))
    pixels = img.load()
    
    for i in range(num_tiles):
        tile_data = tiles_data[i*8 : (i+1)*8]
        tx = (i % cols) * 8
        ty = (i // cols) * 8
        
        for y in range(8):
            byte = tile_data[y]
            for x in range(8):
                if (byte >> (7 - x)) & 1:
                    pixels[tx + x, ty + y] = (255, 255, 255, 255)
                    
    img.save(output_path)
    print(f"Extracted custom tiles to {output_path}")

if __name__ == "__main__":
    extract_sprites("run/data/OBJECT", "data/extracted_sprites")
    extract_tiles("run/data/CHAR.ROM", "data/tileset.png")
    extract_custom_tiles("run/data/OBJECT", "data/custom_tileset.png")
