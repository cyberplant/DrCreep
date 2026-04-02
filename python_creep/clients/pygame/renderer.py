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

    def draw_entity_sprite(self, etype, x, y, facing_left, is_moving=False, tick=0, color_idx=None, move_mode='walkway', shrink=1.0):
        sprite_id = 0
        draw_x = self.px(x)
        if etype == 'player':
            if move_mode == 'ladder':
                # Ladder Climbing: 46, 47, 48
                frame = (tick // 4) % 3 if is_moving else 0
                sprite_id = 46 + frame
                draw_x += 4 # +2 world units = +4 pixels
            elif move_mode == 'pole':
                # Pole Sliding: Use static frame 49 to avoid flickering
                sprite_id = 49
                draw_x += 4
            else:
                base = 3 if facing_left else 0
                frame = (tick // 2) % 3 if is_moving else 0
                sprite_id = base + frame
        elif etype == 'mummy': sprite_id = 0x4B if facing_left else 0x4E
        elif etype == 'frankie': sprite_id = 0x87 if facing_left else 0x84
        
        y_offset = -21
        if move_mode == 'walkway': y_offset = -17
        
        sprite = self.assets.get_colored_sprite(sprite_id, color_idx) if color_idx is not None else self.assets.get_sprite(sprite_id)
        if sprite:
            if shrink < 1.0:
                sw, sh = int(sprite.get_width() * shrink), int(sprite.get_height() * shrink)
                if sw > 0 and sh > 0:
                    sprite = pygame.transform.scale(sprite, (sw, sh))
            # Center horizontally relative to x
            self.world_surface.blit(sprite, (draw_x - (sprite.get_width() // 2), self.py(y) + y_offset))
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
        if not all_rooms: return self.world_surface

        # Find min/max map coordinates to normalize
        min_mx = min(r.get('map_x', 255) for r in all_rooms.values())
        min_my = min(r.get('map_y', 255) for r in all_rooms.values())
        
        ROOM_W, ROOM_H = 12, 8
        SCALE_X, SCALE_Y = 2, 2
        MARGIN_X, MARGIN_Y = 40, 40

        for r_id_str, r_data in all_rooms.items():
            r_id = int(r_id_str)
            is_target = (r_id == target_room_id)
            is_discovered = (r_id in discovered)
            
            if not is_discovered and not is_target:
                continue
            
            mx, my = r_data.get('map_x', 0), r_data.get('map_y', 0)
            rx = MARGIN_X + (mx - min_mx) * SCALE_X
            ry = MARGIN_Y + (my - min_my) * SCALE_Y

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
            if state.get('transition', {}).get('phase') == 'map':
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

                # Pass 1: Environmental objects (EXCEPT Ladders/Poles)
                for obj in room['objects']:
                    ot = obj['type']
                    if ot in ('ladder', 'pole'): continue
                    
                    px, py = self.px(obj['x']), self.py(obj['y'])
                    props = obj.get('properties', {})
                    obj_state = obj.get('state', 0)
                    
                    if ot == 'walkway':
                        length = props.get('length', 0)
                        ladder_xs = set()
                        for other in room['objects']:
                            if other['type'] == 'ladder':
                                l_py = self.py(other['y'])
                                l_len = other.get('properties', {}).get('length', 0)
                                if l_py <= py <= l_py + l_len * 8:
                                    ladder_xs.add(self.px(other['x']))

                        for i in range(length):
                            sid = 28 # Middle (0x1C)
                            if i == 0: sid = 27 # Left (0x1B)
                            elif i == length - 1: sid = 29 # Right (0x1D)
                            
                            seg_x = px + i * 8
                            self.draw_env_sprite(sid, seg_x, py, room_color)
                            
                            # Draw brown depth edge under the walkway
                            pygame.draw.line(self.world_surface, C64_PALETTE[9], (seg_x, py + 8), (seg_x + 7, py + 8))
                            # Draw brown depth edge on the right edge of the last segment
                            if i == length - 1:
                                pygame.draw.line(self.world_surface, C64_PALETTE[9], (seg_x + 8, py), (seg_x + 8, py + 8))
                                
                            # Cut the walkway visually where a ladder intersects
                            if seg_x in ladder_xs:
                                pygame.draw.rect(self.world_surface, C64_PALETTE[0], (seg_x + 2, py, 4, 8))
                    elif ot == 'door':
                        color_idx = 2 if props.get('is_exit') else 4
                        frame_sprite = self.assets.get_colored_sprite(6, color_idx)
                        if frame_sprite: self.world_surface.blit(frame_sprite, (px, py))
                        int_offset = (px + 8, py + 17)
                        
                        open_timer = obj.get('open_timer', 0)
                        if obj_state == 0:
                            int_sprite = self.assets.get_colored_sprite(7, 1)
                            if int_sprite: self.world_surface.blit(int_sprite, int_offset)
                        elif obj_state == 1:
                            # Animation from bottom to top
                            closed_sprite = self.assets.get_colored_sprite(7, 1)
                            nr_id = str(props.get('link_room', ''))
                            nr_data = state['rooms'].get(nr_id)
                            nr_color_id = nr_data.get('color', 1) if nr_data else 1
                            open_sprite = self.assets.get_colored_sprite(8, nr_color_id)
                            
                            if closed_sprite and open_sprite:
                                h = closed_sprite.get_height()
                                progress = min(1.0, open_timer / 30.0)
                                reveal_h = int(h * progress)
                                if h - reveal_h > 0:
                                    self.world_surface.blit(closed_sprite, int_offset, (0, 0, closed_sprite.get_width(), h - reveal_h))
                                if reveal_h > 0:
                                    self.world_surface.blit(open_sprite, (int_offset[0], int_offset[1] + h - reveal_h), (0, h - reveal_h, open_sprite.get_width(), reveal_h))
                        elif obj_state >= 2:
                            nr_id = str(props.get('link_room', ''))
                            nr_data = state['rooms'].get(nr_id)
                            nr_color_id = nr_data.get('color', 1) if nr_data else 1
                            int_sprite = self.assets.get_colored_sprite(8, nr_color_id)
                            if int_sprite: self.world_surface.blit(int_sprite, int_offset)
                    elif ot == 'text':
                        font_id = props.get('font', 0)
                        scale_w = 2 if font_id in (33, 34) else 1
                        scale_h = 2 if font_id == 34 else 1
                        char_w = 8 * scale_w
                        char_h = 8 * scale_h
                        
                        for i, char in enumerate(props.get('text', "")):
                            code = self.ascii_to_screen_code(char)
                            tile = self.assets.get_tile(code, props.get('color', 1))
                            if tile:
                                if scale_w > 1 or scale_h > 1:
                                    tile = pygame.transform.scale(tile, (char_w, char_h))
                                self.world_surface.blit(tile, (px + i * char_w, py))
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
                        l_len = props.get('length', 4)
                        for i in range(l_len):
                            self.draw_env_sprite(50, px, py + i * 8, 12) # Poles (0x32)
                        self.draw_env_sprite(51, px - 4, py + l_len * 8, 12) # Spheres (0x33)
                        if is_on:
                            # Bolt Animation (Flickering)
                            if (tick // 2) % 2 == 0:
                                bolt_frame = 94 + (tick % 3) # 94, 95, 96
                                for j in range(l_len + 1):
                                    self.draw_env_sprite(bolt_frame, px, py + j * 8, 1)
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
                        bell_sprite = self.assets.get_colored_sprite(9, target_room_color)
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
                    elif ot == 'trapdoor_switch': self.draw_env_sprite(128, px, py, 3) # Switch (0x80 approx)
                    elif ot == 'conveyor':
                        for i in range(10): self.draw_env_sprite(125, px + i * 8, py, 6)
                    elif ot == 'conveyor_switch': self.draw_env_sprite(130, px, py, 1) # Conveyor switch (0x82)
                    elif ot == 'raygun':
                        self.draw_env_sprite(95, px, py, 2) # Gun base (0x5F)
                    elif ot == 'raygun_switch':
                        self.draw_env_sprite(54, px, py, 1) # Same base as lightning

                # Pass 2: Entities
                for m in state.get('mummies', []):
                    if str(m['room_id']) == room_id:
                        self.draw_entity_sprite('mummy', m['x'], m['y'], m.get('facing_left'), m.get('is_moving'), tick, color_idx=1)
                for f in state.get('frankies', []):
                    if str(f['room_id']) == room_id:
                        self.draw_entity_sprite('frankie', f['x'], f['y'], f.get('facing_left'), f.get('is_moving'), tick)
                
                # Player Rendering (with transition shrink support)
                transition = state.get('transition') or {}
                shrink_val = 1.0
                p_x, p_y = player['x'], player['y']
                p_mode = player.get('move_mode', 'walkway')
                
                if transition.get('phase') == 'entering':
                    timer = transition.get('timer', 0)
                    shrink_val = max(0.0, 1.0 - (timer / 50.0))
                    p_x = transition.get('door_x', p_x) + 5
                    p_y = transition.get('door_y', p_y) + 32
                    p_mode = 'walkway' # Always use walkway pose for door entry
                
                self.draw_entity_sprite('player', p_x, p_y, player.get('facing_left'), player.get('is_moving'), tick, color_idx=player.get('color', 1), move_mode=p_mode, shrink=shrink_val)
                
                # Pass 3: Ladders and Poles (on top of player)
                for obj in room['objects']:
                    ot = obj['type']
                    if ot not in ('ladder', 'pole'): continue
                    
                    px, py = self.px(obj['x']), self.py(obj['y'])
                    props = obj.get('properties', {})
                    
                    if ot == 'ladder':
                        length = props.get('length', 0)
                        for i in range(length + 1): # +1 to reach bottom path
                            sid = 40 if i < length else 43 # 0x28 or 0x2B
                            self.draw_env_sprite(sid, px, py + i * 8, 1) # White
                    elif ot == 'pole':
                        length = props.get('length', 0)
                        for i in range(length + 1):
                            sid = 36 # 0x24
                            self.draw_env_sprite(sid, px, py + i * 8, 1)
                
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
