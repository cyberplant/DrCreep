import pygame
import os

C64_PALETTE = [
    (0, 0, 0), (255, 255, 255), (136, 0, 0), (170, 255, 238),
    (204, 68, 204), (0, 204, 85), (0, 0, 170), (238, 238, 119),
    (212, 133, 61), (102, 68, 0), (255, 119, 119), (51, 51, 51),
    (119, 119, 119), (170, 255, 102), (0, 136, 255), (187, 187, 187)
]

class C64Assets:
    def __init__(self, sprite_dir, tileset_path, custom_tileset_path=None):
        self.sprites = {}
        self.tiles = []
        self.custom_tiles = []
        print(f"DEBUG: Initializing assets. Sprite Dir: {sprite_dir}, Tileset: {tileset_path}")
        self._load_sprites(sprite_dir)
        self._load_tiles(tileset_path, self.tiles)
        if custom_tileset_path:
            self._load_tiles(custom_tileset_path, self.custom_tiles)

    def _load_sprites(self, sprite_dir):
        if not os.path.exists(sprite_dir):
            print(f"ERROR: Sprite directory not found: {os.path.abspath(sprite_dir)}")
            return
        
        count = 0
        for filename in sorted(os.listdir(sprite_dir)):
            if filename.endswith(".png"):
                try:
                    sprite_id = int(filename.split("_")[1].split(".")[0])
                    path = os.path.join(sprite_dir, filename)
                    surface = pygame.image.load(path).convert_alpha()
                    surface.set_colorkey((0, 0, 0))
                    self.sprites[sprite_id] = surface
                    count += 1
                except Exception as e:
                    print(f"DEBUG: Failed to load sprite {filename}: {e}")
        print(f"DEBUG: Loaded {count} sprites from {sprite_dir}")

    def _load_tiles(self, path, target_list):
        if not os.path.exists(path):
            print(f"ERROR: Tileset file not found: {os.path.abspath(path)}")
            return
        try:
            full_tileset = pygame.image.load(path).convert_alpha()
            width, height = full_tileset.get_size()
            for ty in range(0, height, 8):
                for tx in range(0, width, 8):
                    tile = pygame.Surface((8, 8), pygame.SRCALPHA)
                    tile.blit(full_tileset, (0, 0), (tx, ty, 8, 8))
                    target_list.append(tile)
            print(f"DEBUG: Loaded {len(target_list)} tiles from {path}.")
        except Exception as e:
            print(f"ERROR: Failed to load tileset {path}: {e}")

    def get_tile(self, index, color_idx, custom=False):
        t_list = self.custom_tiles if custom else self.tiles
        if not t_list or index >= len(t_list):
            return None
        tile = t_list[index].copy()
        color = C64_PALETTE[color_idx % 16]
        # Multiply the white pixels with the target color, preserving transparent background
        tile.fill(color + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        return tile

    def get_sprite(self, sprite_id):
        return self.sprites.get(sprite_id)
        
    def get_colored_sprite(self, sprite_id, color_idx):
        sprite = self.sprites.get(sprite_id)
        if not sprite: return None
        colored = sprite.copy()
        color = C64_PALETTE[color_idx % 16]
        colored.fill(color + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        return colored

