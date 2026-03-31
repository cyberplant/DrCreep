import pygame
import socket
import json
import threading
import sys
import os
import time
import argparse
from datetime import datetime

from python_creep.clients.pygame.assets import C64_PALETTE, C64Assets

# Add current directory to path to import engine modules
sys.path.append(os.getcwd())

class PygameClient:
    def __init__(self, host='127.0.0.1', port=4242, debug=False):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        # Set to 3x C64 resolution (960x600)
        self.scale = 3
        self.screen = pygame.display.set_mode((320 * self.scale, 200 * self.scale))
        pygame.display.set_caption("The Castles of Dr. Creep (Pygame)")
        
        self.audio_enabled = True
        try:
            pygame.mixer.init()
            print("DEBUG: Pygame Audio Mixer initialized.")
        except Exception as e:
            print(f"WARNING: Audio mixer failed to init: {e}")
            self.audio_enabled = False
            
        self.sounds = {}
        self.clock = pygame.time.Clock()
        
        self.host, self.port = host, port
        self.sock = None
        self.state = {}
        self.running = True
        self.debug_mode = debug
        self._reported_fallbacks = set()
        self._last_room_id = None
        self._screenshot_requested = False
        
        # Robust Pathing
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        
        sprite_path = os.path.join(project_root, "data", "extracted_sprites")
        tile_path = os.path.join(project_root, "data", "tileset.png")
        custom_tile_path = os.path.join(project_root, "data", "custom_tileset.png")
        
        # Load assets
        self.assets = C64Assets(sprite_path, tile_path, custom_tile_path)
        
        # Scaling (Native internal, Scaled display)
        self.world_surface = pygame.Surface((320, 200))

    def connect(self):
        print(f"DEBUG: Connecting to {self.host}:{self.port}...")
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print("DEBUG: Connection established.")
            threading.Thread(target=self._receive_loop, daemon=True).start()
        except Exception as e:
            print(f"ERROR: Could not connect to server: {e}")
            self.running = False

    def _receive_loop(self):
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(4096).decode()
                if not data: break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.state = json.loads(line)
            except:
                break
        self.running = False

    def _send_input(self, commands):
        self._send_command({'type': 'INPUT', 'player_id': 0, 'commands': commands})

    def _send_command(self, msg):
        if self.sock:
            try:
                self.sock.sendall((json.dumps(msg) + "\n").encode())
            except Exception as e:
                print(f"ERROR: Failed to send command: {e}")
                self.running = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    self._screenshot_requested = True
                elif event.key == pygame.K_q:
                    self.running = False
                elif event.key == pygame.K_k:
                    self._send_input({'respawn': True})
                elif event.key == pygame.K_r:
                    self._send_input({'restart': True})
        
        keys = pygame.key.get_pressed()
        cmds = {
            'up': keys[pygame.K_w] or keys[pygame.K_UP],
            'down': keys[pygame.K_s] or keys[pygame.K_DOWN],
            'left': keys[pygame.K_a] or keys[pygame.K_LEFT],
            'right': keys[pygame.K_d] or keys[pygame.K_RIGHT],
            'action': keys[pygame.K_SPACE] or keys[pygame.K_RETURN]
        }
        if any(cmds.values()):
            self._send_input(cmds)

    def _take_screenshot(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"screenshot_{timestamp}.png"
        pygame.image.save(self.screen, filename)
        print(f"DEBUG: Screenshot saved to {filename}")
        self._screenshot_requested = False

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

    def _render_map_view(self):
        self.world_surface.fill((0, 0, 0))
        font = pygame.font.SysFont(None, 24)
        title = font.render("CASTLE MAP", True, (255, 255, 255))
        self.world_surface.blit(title, (110, 5))

        transition = self.state.get('transition') or {}
        target_room_id = transition.get('to_room')
        discovered = self.state.get('discovered_rooms', [])
        
        all_rooms = self.state.get('rooms', {})
        ROOM_W, ROOM_H = 30, 20
        # map_x and map_y are grid indices, so scale them to space the rooms out
        SCALE_X, SCALE_Y = ROOM_W + 10, ROOM_H + 10
        MARGIN_X, MARGIN_Y = 40, 40
        
        if self.debug_mode:
            print(f"\n--- MAP VIEW DEBUG (Tick {self.state.get('tick')}) ---")
            print(f"Target Room: {target_room_id}")
            print(f"Discovered: {discovered}")

        for r_id_str, r_data in all_rooms.items():
            r_id = int(r_id_str)
            is_target = (r_id == target_room_id)
            is_discovered = (r_id in discovered)
            
            if not is_discovered and not is_target:
                continue
            
            mx, my = r_data.get('map_x', 0), r_data.get('map_y', 0)
            rx = MARGIN_X + mx * SCALE_X
            ry = MARGIN_Y + my * SCALE_Y
            
            if self.debug_mode:
                status = "TARGET" if is_target else "DISCOVERED"
                print(f"Room {r_id:02}: map_pos=({mx},{my}) screen_pos=({int(rx)},{int(ry)}) status={status}")

            color = C64_PALETTE[r_data.get('color', 1)]
            pygame.draw.rect(self.world_surface, color, (rx, ry, ROOM_W, ROOM_H), 1)
            
            # Draw door holes
            for obj in r_data.get('objects', []):
                if obj['type'] == 'door':
                    ox, oy = obj['x'], obj['y']
                    # Draw a black line to create a "hole" in the colored box
                    if oy < 10: pygame.draw.line(self.world_surface, (0,0,0), (rx+10, ry), (rx+20, ry), 2) # Top
                    elif oy > 180: pygame.draw.line(self.world_surface, (0,0,0), (rx+10, ry+ROOM_H-1), (rx+20, ry+ROOM_H-1), 2) # Bottom
                    elif ox < 20: pygame.draw.line(self.world_surface, (0,0,0), (rx, ry+5), (rx, ry+15), 2) # Left
                    elif ox > 170: pygame.draw.line(self.world_surface, (0,0,0), (rx+ROOM_W-1, ry+5), (rx+ROOM_W-1, ry+15), 2) # Right

            if is_target:
                tick = self.state.get('tick', 0)
                if (tick // 10) % 2 == 0:
                    ddir = transition.get('door_dir', 0)
                    # Dr. Creep directions: 0=From Left, 1=From Right, 2=From Top, 3=From Bottom
                    ax, ay = rx + ROOM_W//2, ry + ROOM_H//2
                    if ddir == 0: ax, ay = rx - 8, ry + ROOM_H//2 # Enter from LEFT wall
                    elif ddir == 1: ax, ay = rx + ROOM_W + 8, ry + ROOM_H//2 # Enter from RIGHT wall
                    elif ddir == 2: ax, ay = rx + ROOM_W//2, ry - 8 # Enter from TOP wall
                    elif ddir == 3: ax, ay = rx + ROOM_W//2, ry + ROOM_H + 8 # Enter from BOTTOM wall
                    
                    pts = [(ax, ay)]
                    if ddir == 0: pts += [(ax-5, ay-5), (ax-5, ay+5)] # Pointing RIGHT into left door
                    elif ddir == 1: pts += [(ax+5, ay-5), (ax+5, ay+5)] # Pointing LEFT into right door
                    elif ddir == 2: pts += [(ax-5, ay-5), (ax+5, ay-5)] # Pointing DOWN into top door
                    elif ddir == 3: pts += [(ax-5, ay+5), (ax+5, ay+5)] # Pointing UP into bottom door
                    pygame.draw.polygon(self.world_surface, (255, 255, 255), pts)

        font_small = pygame.font.SysFont(None, 16)
        msg = font_small.render("Press ACTION (Space) to enter", True, (200, 200, 200))
        self.world_surface.blit(msg, (80, 185))

        scaled = pygame.transform.scale(self.world_surface, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))
        if self._screenshot_requested: self._take_screenshot()
        pygame.display.flip()

    def render(self):
        self.world_surface.fill(C64_PALETTE[0])
        if not self.state:
            font = pygame.font.SysFont(None, 24)
            img = font.render("Waiting for server state...", True, (255, 255, 255))
            self.world_surface.blit(img, (80, 90))
            scaled = pygame.transform.scale(self.world_surface, self.screen.get_size())
            self.screen.blit(scaled, (0, 0)); pygame.display.flip()
            return

        if self.state.get('victory'):
            font = pygame.font.SysFont(None, 36)
            title = font.render("YOU HAVE ESCAPED!", True, (255, 255, 255))
            font_small = pygame.font.SysFont(None, 18)
            msg = font_small.render("Press R to restart or Q to quit", True, (200, 200, 200))
            self.world_surface.blit(title, (40, 80))
            self.world_surface.blit(msg, (60, 120))
            scaled = pygame.transform.scale(self.world_surface, self.screen.get_size())
            self.screen.blit(scaled, (0, 0)); pygame.display.flip()
            return
            
        if self.state.get('transition'):
            self._render_map_view()
            return

        try:
            if self.audio_enabled:
                for ev in self.state.get('events', []):
                    if ev in self.sounds: self.sounds[ev].play()

            player = self.state['players'][0]
            room_id = str(player['room_id'])
            room = self.state['rooms'].get(room_id)
            if room:
                if room_id != self._last_room_id:
                    self._last_room_id = room_id

                room_color = room.get('color', 1)
                tick = self.state.get('tick', 0)

                for obj in room['objects']:
                    ot = obj['type']
                    px, py = self.px(obj['x']), self.py(obj['y'])
                    props = obj.get('properties', {})
                    obj_state = obj.get('state', 0)
                    
                    # Environment rendering using ACTUAL C64 sprites from OBJECT file
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
                            nr_data = self.state['rooms'].get(nr_id)
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
                            if link_room_str in self.state['rooms']:
                                target_room_color = self.state['rooms'][link_room_str].get('color', 1)
                        # Draw solid background color for the ring
                        pygame.draw.rect(self.world_surface, C64_PALETTE[target_room_color], (px+8, py+8, 8, 8))
                        # Draw white mask doorbell sprite on top
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
                        # The belt is sprite 125 (0x7D)
                        for i in range(10): self.draw_env_sprite(125, px + i * 8, py, 6)
                    elif ot == 'conveyor_switch': self.draw_env_sprite(130, px, py, 1) # Conveyor switch (0x82)
                    elif ot == 'raygun':
                        self.draw_env_sprite(95, px, py, 2) # Gun base (0x5F)
                    elif ot == 'raygun_switch':
                        self.draw_env_sprite(54, px, py, 1) # Same base as lightning

                # Entities
                for m in self.state.get('mummies', []):
                    if str(m['room_id']) == room_id:
                        self.draw_entity_sprite('mummy', m['x'], m['y'], m.get('facing_left'), m.get('is_moving'), tick)
                for f in self.state.get('frankies', []):
                    if str(f['room_id']) == room_id:
                        self.draw_entity_sprite('frankie', f['x'], f['y'], f.get('facing_left'), f.get('is_moving'), tick)
                self.draw_entity_sprite('player', player['x'], player['y'], player.get('facing_left'), player.get('is_moving'), tick, color_idx=player.get('color', 1))
                
                # Projectiles
                for proj in self.state.get('projectiles', []):
                    if str(proj['room_id']) == room_id:
                        # Draw red laser bolt (approx)
                        pygame.draw.rect(self.world_surface, C64_PALETTE[2], (self.px(proj['x']), self.py(proj['y']), 8, 2))

                if self.debug_mode: self._draw_grid()
        except Exception as e: print(f"ERROR: Render exception: {e}")

        scaled = pygame.transform.scale(self.world_surface, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))
        if self._screenshot_requested: self._take_screenshot()
        pygame.display.flip()

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

    def _log_room_objects(self, room_id, room):
        print(f"\n--- ROOM {room_id} OBJECTS ---")
        for i, obj in enumerate(room['objects']):
            print(f"ID {i:02}: {obj['type'].upper()} at ({obj['x']:.1f}, {obj['y']:.1f})")

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

    def run(self):
        self.connect()
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(50)
        pygame.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4242)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    client = PygameClient(host=args.host, port=args.port, debug=args.debug)
    client.run()
