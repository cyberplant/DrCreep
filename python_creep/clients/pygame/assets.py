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
        self._load_sprites(sprite_dir)
        self._load_tiles(tileset_path, self.tiles)
        if custom_tileset_path:
            self._load_tiles(custom_tileset_path, self.custom_tiles)

    def _load_sprites(self, sprite_dir):
        if not os.path.exists(sprite_dir): return
        for filename in sorted(os.listdir(sprite_dir)):
            if filename.endswith(".png"):
                try:
                    sprite_id = int(filename.split("_")[1].split(".")[0])
                    path = os.path.join(sprite_dir, filename)
                    surface = pygame.image.load(path).convert_alpha()
                    self.sprites[sprite_id] = surface
                except: pass

    def _load_tiles(self, path, target_list):
        if not os.path.exists(path): return
        full_tileset = pygame.image.load(path).convert_alpha()
        w, h = full_tileset.get_size()
        for ty in range(0, h, 8):
            for tx in range(0, w, 8):
                tile = pygame.Surface((8, 8), pygame.SRCALPHA)
                tile.blit(full_tileset, (0, 0), (tx, ty, 8, 8))
                target_list.append(tile)

    def get_tile(self, index, color_idx, custom=False):
        t_list = self.custom_tiles if custom else self.tiles
        if not t_list or index >= len(t_list): return None
        tile = t_list[index].copy()
        color = C64_PALETTE[color_idx % 16]
        tile.fill(color + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        return tile

    def get_sprite(self, sprite_id):
        return self.sprites.get(sprite_id)
        
    def get_colored_sprite(self, sprite_id, color_idx):
        sprite = self.sprites.get(sprite_id)
        if not sprite: return None
        colored = sprite.copy()
        
        # ESPECIAL: Si es la momia, forzamos blanco
        if 75 <= sprite_id <= 80:
            color_idx = 1
            
        color = C64_PALETTE[color_idx % 16]
        colored.fill(color + (255,), special_flags=pygame.BLEND_RGBA_MULT)
        return colored
