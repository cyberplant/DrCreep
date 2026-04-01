import pygame
import os

from clients.pygame.assets import C64_PALETTE, C64Assets

class PygameRenderer:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.world_surface = pygame.Surface((320, 200))
        self._last_room_id = None
        
        # Robust Pathing
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        
        sprite_path = os.path.join(project_root, "data", "extracted_sprites")
        tile_path = os.path.join(project_root, "data", "tileset.png")
        custom_tile_path = os.path.join(project_root, "data", "custom_tileset.png")
        
        # Load assets
        self.assets = C64Assets(sprite_path, tile_path, custom_tile_path)

    def px(self, x): return (int(x) - 16) * 2
    def py(self, y): return int(y)

    def ascii_to_screen_code(self, char):
        c = ord(char) if isinstance(char, str) else char
        if 64 <= c <= 95: return c - 64
        if 32 <= c <= 63: return c
        if 96 <= c <= 127: return c - 64
        return c & 0x3F

    def draw_char(self, char, x_px, y_px, color_idx):
        code = self.ascii_to_screen_code(char)
        tile = self.assets.get_tile(code, color_idx)
        if tile:
            self.world_surface.blit(tile, (x_px, y_px))

    def draw_env_sprite(self, sprite_id, x_px, y_px, color_idx=1):
        sprite = self.assets.get_colored_sprite(sprite_id, color_idx)
        if sprite:
            self.world_surface.blit(sprite, (x_px, y_px))

    def draw_entity_sprite(self, etype, x, y, facing_left, is_moving=False, tick=0, color_idx=None):
        sprite_id = 0
        if etype == 'player':
            base = 3 if facing_left else 0
            frame = (tick // 2) % 3 if is_moving else 0
            sprite_id = base + frame
        elif etype == 'mummy': sprite_id = 0x4B if facing_left else 0x4E
        elif etype == 'frankie': sprite_id = 0x87 if facing_left else 0x84
        
        sprite = self.assets.get_colored_sprite(sprite_id, color_idx) if color_idx is not None else self.assets.get_sprite(sprite_id)
        if sprite: self.world_surface.blit(sprite, (self.px(x) - 8, self.py(y) - 21))
        else:
            color = C64_PALETTE[1]
            if etype == 'mummy': color = C64_PALETTE[15]
            elif etype == 'frankie': color = C64_PALETTE[5]
            pygame.draw.rect(self.world_surface, color, (self.px(x), self.py(y) - 24, 8, 24))

    def _draw_grid(self):
        font = pygame.font.SysFont(None, 12)
        for wx in range(16, 177, 10):
            px = self.px(wx)
            pygame.draw.line(self.world_surface, (40, 40, 40), (px, 0), (px, 200))
            if px > 0:
                txt = font.render(str(wx), True, (100, 100, 100))
                self.world_surface.blit(txt, (px + 2, 2))
        for wy in range(0, 201, 10):
            pygame.draw.line(self.world_surface, (40, 40, 40), (0, wy), (320, wy))
            if wy > 0:
                txt = font.render(str(wy), True, (100, 100, 100))
                self.world_surface.blit(txt, (2, wy + 2))

    def render_map_view(self, state):
        self.world_surface.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 24)
        title = font.render("CASTLE MAP", True, (255, 255, 255))
        self.world_surface.blit(title, (110, 5))

        transition = state.get('transition') or {}
        target_room_id = transition.get('to_room')
        discovered = state.get('discovered_rooms', [])
        
        all_rooms = state.get('rooms', {})
        ROOM_W, ROOM_H = 30, 20
        SCALE_X, SCALE_Y = ROOM_W + 10, ROOM_H + 10
        MARGIN_X, MARGIN_Y = 40, 40

        for r_id_str, r_data in all_rooms.items():
            r_id = int(r_id_str)
            is_target = (r_id == target_room_id)
            is_discovered = (r_id in discovered)
            
            if not is_discovered and not is_target:
                continue
            
            mx, my = r_data.get('map_x', 0), r_data.get('map_y', 0)
            rx = MARGIN_X + mx * SCALE_X
            ry = MARGIN_Y + my * SCALE_Y

            color = C64_PALETTE[r_data.get('color', 1)]
            pygame.draw.rect(self.world_surface, color, (rx, ry, ROOM_W, ROOM_H), 1)
            
            for obj in r_data.get('objects', []):
                if obj['type'] == 'door':
                    ox, oy = obj['x'], obj['y']
                    if oy < 10: pygame.draw.line(self.world_surface, (0,0,0), (rx+10, ry), (rx+20, ry), 2)
                    elif oy > 180: pygame.draw.line(self.world_surface, (0,0,0), (rx+10, ry+ROOM_H-1), (rx+20, ry+ROOM_H-1), 2)
                    elif ox < 20: pygame.draw.line(self.world_surface, (0,0,0), (rx, ry+5), (rx, ry+15), 2)
                    elif ox > 170: pygame.draw.line(self.world_surface, (0,0,0), (rx+ROOM_W-1, ry+5), (rx+ROOM_W-1, ry+15), 2)

            if is_target:
                tick = state.get('tick', 0)
                if (tick // 10) % 2 == 0:
                    ddir = transition.get('door_dir', 0)
                    ax, ay = rx + ROOM_W//2, ry + ROOM_H//2
                    if ddir == 0: ax, ay = rx - 8, ry + ROOM_H//2
                    elif ddir == 1: ax, ay = rx + ROOM_W + 8, ry + ROOM_H//2
                    elif ddir == 2: ax, ay = rx + ROOM_W//2, ry - 8
                    elif ddir == 3: ax, ay = rx + ROOM_W//2, ry + ROOM_H + 8
                    
                    pts = [(ax, ay)]
                    if ddir == 0: pts += [(ax-5, ay-5), (ax-5, ay+5)]
                    elif ddir == 1: pts += [(ax+5, ay-5), (ax+5, ay+5)]
                    elif ddir == 2: pts += [(ax-5, ay-5), (ax+5, ay-5)]
                    elif ddir == 3: pts += [(ax-5, ay+5), (ax+5, ay+5)]
                    pygame.draw.polygon(self.world_surface, (255, 255, 255), pts)

        font_small = pygame.font.SysFont(None, 16)
        msg = font_small.render("Press ACTION (Space) to enter", True, (200, 200, 200))
        self.world_surface.blit(msg, (80, 185))
        return self.world_surface

    def render_state(self, state):
        self.world_surface.fill(C64_PALETTE[0])
        
        if not state:
            font = pygame.font.SysFont(None, 24)
            img = font.render("Waiting for server state...", True, (255, 255, 255))
            self.world_surface.blit(img, (80, 90))
            return self.world_surface

        if state.get('victory'):
            font = pygame.font.SysFont(None, 36)
            title = font.render("YOU HAVE ESCAPED!", True, (255, 255, 255))
            font_small = pygame.font.SysFont(None, 18)
            msg = font_small.render("Press R to restart or Q to quit", True, (200, 200, 200))
            self.world_surface.blit(title, (40, 80))
            self.world_surface.blit(msg, (60, 120))
            return self.world_surface
            
        if state.get('transition'):
            return self.render_map_view(state)

        try:
            player = state['players'][0]
            room_id = str(player['room_id'])
            room = state['rooms'].get(room_id)
            if room:
                if room_id != self._last_room_id:
                    self._last_room_id = room_id

                room_color = room.get('color', 1)
                tick = state.get('tick', 0)

                for obj in room['objects']:
                    ot = obj['type']
                    px, py = self.px(obj['x']), self.py(obj['y'])
                    props = obj.get('properties', {})
                    obj_state = obj.get('state', 0)
                    
                    if ot == 'walkway':
                        length = props.get('length', 0)
                        for i in range(length):
                            sid = 28 # Middle (0x1C)
                            if i == 0: sid = 27 # Left (0x1B)
                            elif i == length - 1: sid = 29 # Right (0x1D)
                            self.draw_env_sprite(sid, px + i * 8, py, room_color)
                    elif ot == 'ladder':
                        length = props.get('length', 0)
                        for i in range(length + 1): # +1 to reach bottom path
                            sid = 40 if i < length else 43 # 0x28 or 0x2B
                            self.draw_env_sprite(sid, px, py + i * 8, 1) # White
                    elif ot == 'pole':
                        length = props.get('length', 0)
                        for i in range(length + 1):
                            sid = 36 # 0x24
                            self.draw_env_sprite(sid, px, py + i * 8, 1)
                    elif ot == 'door':
                        color_idx = 2 if props.get('is_exit') else room_color
                        frame_sprite = self.assets.get_colored_sprite(6, color_idx)
                        if frame_sprite: self.world_surface.blit(frame_sprite, (px, py))
                        int_offset = (px + 8, py + 17)
                        if obj_state == 0:
                            int_sprite = self.assets.get_colored_sprite(7, 1)
                            if int_sprite: self.world_surface.blit(int_sprite, int_offset)
                        elif obj_state >= 1:
                            nr_id = str(props.get('link_room', ''))
                            nr_data = state['rooms'].get(nr_id)
                            nr_color_id = nr_data.get('color', 1) if nr_data else 1
                            int_sprite = self.assets.get_colored_sprite(8, nr_color_id)
                            if int_sprite: self.world_surface.blit(int_sprite, int_offset)
                    elif ot == 'text':
                        char_w = 8
                        for i, char in enumerate(props.get('text', "")):
                            code = self.ascii_to_screen_code(char)
                            tile = self.assets.get_tile(code, props.get('color', 1))
                            if tile: self.world_surface.blit(tile, (px + i * char_w, py))
                    elif ot == 'forcefield':
                        if obj_state > 0:
                            self.draw_env_sprite(62, px - 4, py, 1) # Top laser emitter (0x3E)
                            for i in range(4): # Draw vertical laser segments (fallback to rects for fidelity if sprite unknown)
                                pygame.draw.rect(self.world_surface, C64_PALETTE[1], (px+2, py + 6 + i*8, 2, 8))
                    elif ot == 'forcefield_switch':
                        self.draw_env_sprite(63, px, py, 1) # Outer timer (0x3F)
                        self.draw_env_sprite(64, px+4, py+8, 1) # Inner timer (0x40)
                    elif ot == 'lightning_machine':
                        sys_id = props.get('system_id', 0)
                        is_on = room.get('lightning_systems', {}).get(str(sys_id), False)
                        for i in range(props.get('length', 4)):
                            self.draw_env_sprite(50, px, py + i * 8, 12) # Poles (0x32)
                        self.draw_env_sprite(51, px - 4, py + props.get('length', 4) * 8, 12) # Spheres (0x33)
                        if is_on and (tick // 2) % 2 == 0:
                            self.draw_env_sprite(94, px, py + props.get('length', 4) * 8 + 8, 1) # Sparks (approx 0x5E)
                    elif ot == 'lightning_switch':
                        self.draw_env_sprite(54, px, py, 1) # Switch Base (0x36)
                        self.draw_env_sprite(55, px + 4, py + 8, 1) # Switch Lever (0x37)
                    elif ot == 'doorbell':
                        target_id = props.get('target_door_idx')
                        target_room_color = 1
                        if target_id is not None and target_id < len(room['objects']):
                            link_room_str = str(room['objects'][target_id].get('properties', {}).get('link_room', ''))
                            if link_room_str in state['rooms']:
                                target_room_color = state['rooms'][link_room_str].get('color', 1)
                        pygame.draw.rect(self.world_surface, C64_PALETTE[target_room_color], (px+8, py+8, 8, 8))
                        bell_sprite = self.assets.get_colored_sprite(9, 1)
                        if bell_sprite: self.world_surface.blit(bell_sprite, (px, py))
                    elif ot == 'key': self.draw_env_sprite(13, px, py, props.get('color', 1)) # Key (0x0D)
                    elif ot == 'lock': self.draw_env_sprite(14, px, py, props.get('color', 1)) # Lock (0x0E)
                    elif ot == 'teleport': 
                        if obj_state > 0: self.draw_env_sprite(22, px, py, 1) # Active
                        else: self.draw_env_sprite(21, px, py, 1) # Base
                    elif ot == 'teleport_target': self.draw_env_sprite(23, px, py, props.get('color', 1))
                    elif ot == 'mummy_tomb':
                        for dy in range(3):
                            for dx in range(5): self.draw_env_sprite(66, px + dx * 8, py + dy * 8, 2) # Tomb Blocks (0x42)
                    elif ot == 'mummy_release': self.draw_env_sprite(68, px, py, 1) # Button (0x44)
                    elif ot == 'trapdoor_switch': self.draw_env_sprite(46, px, py, 3) # Switch (0x2E)
                    elif ot == 'conveyor':
                        for i in range(10): self.draw_env_sprite(125, px + i * 8, py, 6)
                    elif ot == 'conveyor_switch': self.draw_env_sprite(130, px, py, 1) # Conveyor switch (0x82)
                    elif ot == 'raygun':
                        self.draw_env_sprite(95, px, py, 2) # Gun base (0x5F)
                    elif ot == 'raygun_switch':
                        self.draw_env_sprite(54, px, py, 1) # Same base as lightning

                # Entities
                for m in state.get('mummies', []):
                    if str(m['room_id']) == room_id:
                        self.draw_entity_sprite('mummy', m['x'], m['y'], m.get('facing_left'), m.get('is_moving'), tick)
                for f in state.get('frankies', []):
                    if str(f['room_id']) == room_id:
                        self.draw_entity_sprite('frankie', f['x'], f['y'], f.get('facing_left'), f.get('is_moving'), tick)
                self.draw_entity_sprite('player', player['x'], player['y'], player.get('facing_left'), player.get('is_moving'), tick, color_idx=player.get('color', 1))
                
                # Projectiles
                for proj in state.get('projectiles', []):
                    if str(proj['room_id']) == room_id:
                        pygame.draw.rect(self.world_surface, C64_PALETTE[2], (self.px(proj['x']), self.py(proj['y']), 8, 2))

                if self.debug_mode: self._draw_grid()
        except Exception as e: 
            print(f"ERROR: Render exception: {e}")
            import traceback
            traceback.print_exc()

        return self.world_surface
