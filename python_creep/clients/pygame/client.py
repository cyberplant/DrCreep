import pygame
import socket
import json
import threading
import sys
import os
import time
import argparse

from python_creep.clients.pygame.assets import C64_PALETTE, C64Assets

# Add current directory to path to import engine modules
sys.path.append(os.getcwd())

class PygameClient:
    def __init__(self, host='127.0.0.1', port=4242, debug=False):
        pygame.init()
        self.screen = pygame.display.set_mode((640, 400))
        pygame.display.set_caption("The Castles of Dr. Creep (Pygame)")
        self.clock = pygame.time.Clock()
        
        self.host, self.port = host, port
        self.sock = None
        self.state = {}
        self.running = True
        self.debug_mode = debug
        self._reported_fallbacks = set()
        self._last_room_id = None
        
        # Robust Pathing
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        
        sprite_path = os.path.join(project_root, "data", "extracted_sprites")
        tile_path = os.path.join(project_root, "data", "tileset.png")
        custom_tile_path = os.path.join(project_root, "data", "custom_tileset.png")
        
        # Load assets
        print(f"DEBUG: Project Root identified as: {project_root}")
        self.assets = C64Assets(sprite_path, tile_path, custom_tile_path)
        
        # Scaling
        self.scale = 2
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
        if self.sock:
            msg = {'type': 'INPUT', 'player_id': 0, 'commands': commands}
            try:
                self.sock.sendall((json.dumps(msg) + "\n").encode())
            except Exception as e:
                print(f"ERROR: Failed to send input: {e}")
                self.running = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    self._take_screenshot()
        
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
        filename = f"screenshot_{int(time.time())}.png"
        # Save the composed world surface, scaled up
        scaled = pygame.transform.scale(self.world_surface, (320 * self.scale, 200 * self.scale))
        pygame.image.save(scaled, filename)
        print(f"DEBUG: Screenshot saved to {filename}")

    def px(self, x): return (int(x) - 16) * 2
    def py(self, y): return int(y)

    def ascii_to_screen_code(self, char):
        c = ord(char)
        if 64 <= c <= 95: return c - 64
        if 32 <= c <= 63: return c
        if 96 <= c <= 127: return c - 64
        return c & 0x3F

    def draw_char(self, char, x_px, y_px, color_idx):
        code = self.ascii_to_screen_code(char) if isinstance(char, str) else char
        tile = self.assets.get_tile(code, color_idx)
        if tile:
            self.world_surface.blit(tile, (x_px, y_px))

    def draw_custom_char(self, char_idx, x_px, y_px, color_idx):
        tile = self.assets.get_tile(char_idx, color_idx, custom=True)
        if tile:
            self.world_surface.blit(tile, (x_px, y_px))

    def render(self):
        self.world_surface.fill(C64_PALETTE[0])
        
        if not self.state:
            font = pygame.font.SysFont(None, 24)
            img = font.render("Waiting for server state...", True, (255, 255, 255))
            self.world_surface.blit(img, (80, 90))
        else:
            try:
                player = self.state['players'][0]
                room_id = str(player['room_id'])
                room = self.state['rooms'].get(room_id)
                if room:
                    if room_id != self._last_room_id:
                        self._log_room_objects(room_id, room)
                        self._last_room_id = room_id

                    room_color = room.get('color', 1)
                    tick = self.state.get('tick', 0)

                    # Draw Objects
                    for obj in room['objects']:
                        ot = obj['type']
                        ox, oy = obj['x'], obj['y']
                        props = obj.get('properties', {})
                        obj_state = obj.get('state', 0)
                        px, py = self.px(ox), self.py(oy)
                        
                        if ot == 'walkway':
                            for i in range(props.get('length', 0)):
                                self.draw_char(64, px + i * 8, py, room_color)
                                self.draw_char(105, px + i * 8, py + 8, room_color)
                        elif ot == 'ladder':
                            for i in range(max(0, props.get('length', 0) * 2 - 2)):
                                self.draw_char('#', px, py + i * 8, room_color)
                        elif ot == 'pole':
                            for i in range(props.get('length', 0) * 2):
                                self.draw_char(']', px, py + i * 8, room_color)
                        elif ot == 'door':
                            color_idx = 2 if props.get('is_exit') else room_color
                            frame_sprite = self.assets.get_colored_sprite(6, color_idx)
                            if frame_sprite: self.world_surface.blit(frame_sprite, (px, py))
                            
                            if obj_state == 0: # Closed
                                int_sprite = self.assets.get_colored_sprite(7, 1)
                                if int_sprite: self.world_surface.blit(int_sprite, (px, py))
                            elif obj_state >= 1: # Open
                                nr_id = str(props.get('link_room', ''))
                                nr_data = self.state['rooms'].get(nr_id)
                                nr_color_id = nr_data.get('color', 1) if nr_data else 1
                                int_sprite = self.assets.get_colored_sprite(8, nr_color_id)
                                if int_sprite: self.world_surface.blit(int_sprite, (px, py))

                        elif ot == 'text':
                            font_id = props.get('font', 0)
                            text_scale = 4 if font_id < 8 else 2
                            char_w = 8 * text_scale
                            for i, char in enumerate(props.get('text', "")):
                                code = self.ascii_to_screen_code(char)
                                tile = self.assets.get_tile(code, props.get('color', 1))
                                if tile:
                                    scaled_tile = pygame.transform.scale(tile, (char_w, 8 * text_scale))
                                    self.world_surface.blit(scaled_tile, (px + i * char_w, py))
                        elif ot in ['key', 'lock', 'doorbell', 'teleport', 'teleport_target', 'mummy_tomb', 'mummy_release', 'trapdoor_switch', 'conveyor', 'conveyor_switch']:
                            if ot == 'doorbell':
                                bell_sprite = self.assets.get_colored_sprite(9, room_color)
                                if bell_sprite: self.world_surface.blit(bell_sprite, (px, py))
                            elif ot == 'key': self.draw_char('K', px, py, props.get('color', 1))
                            elif ot == 'lock': self.draw_char('X', px, py, props.get('color', 1))
                            elif ot == 'teleport': self.draw_char('T', px, py, obj_state)
                            elif ot == 'teleport_target': self.draw_char('t', px, py, props.get('color', 1))
                            elif ot == 'mummy_tomb':
                                for dy in range(3):
                                    for dx in range(5): self.draw_char('#', px + dx * 8, py + dy * 8, 2)
                            elif ot == 'mummy_release': self.draw_char('M', px, py, 1)
                            elif ot == 'trapdoor_switch': self.draw_char('o', px, py, 3)
                            elif ot == 'conveyor':
                                for i in range(10): self.draw_char(64, px + i * 8, py, 6)
                            elif ot == 'conveyor_switch': self.draw_char(81, px, py, 1)

                    # Draw Entities
                    for m in self.state.get('mummies', []):
                        if str(m['room_id']) == room_id:
                            self.draw_entity_sprite('mummy', m['x'], m['y'], m.get('facing_left'), m.get('is_moving'), tick)

                    for f in self.state.get('frankies', []):
                        if str(f['room_id']) == room_id:
                            self.draw_entity_sprite('frankie', f['x'], f['y'], f.get('facing_left'), f.get('is_moving'), tick)

                    self.draw_entity_sprite('player', player['x'], player['y'], player.get('facing_left'), player.get('is_moving'), tick)
                    
                    if self.debug_mode:
                        self._draw_grid()

            except Exception as e:
                print(f"ERROR: Render exception: {e}")

        # Scale and blit
        scaled = pygame.transform.scale(self.world_surface, (320 * self.scale, 200 * self.scale))
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def _draw_grid(self):
        # Draw every 16 world units (32 pixels)
        for wx in range(16, 177, 10):
            px = self.px(wx)
            pygame.draw.line(self.world_surface, (40, 40, 40), (px, 0), (px, 200))
        for wy in range(0, 201, 10):
            pygame.draw.line(self.world_surface, (40, 40, 40), (0, wy), (320, wy))

    def _log_room_objects(self, room_id, room):
        print(f"\n--- ROOM {room_id} OBJECTS ---")
        for i, obj in enumerate(room['objects']):
            print(f"ID {i:02}: {obj['type'].upper()} at ({obj['x']:.1f}, {obj['y']:.1f})")

    def draw_entity_sprite(self, etype, x, y, facing_left, is_moving=False, tick=0):
        sprite_id = 0
        if etype == 'player':
            base = 3 if facing_left else 0
            frame = (tick // 8) % 3 if is_moving else 0
            sprite_id = base + frame
        elif etype == 'mummy':
            sprite_id = 0x4B if facing_left else 0x4E
        elif etype == 'frankie':
            sprite_id = 0x87 if facing_left else 0x84
        
        sprite = self.assets.get_sprite(sprite_id)
        if sprite:
            self.world_surface.blit(sprite, (self.px(x) - 8, self.py(y) - 21))
        else:
            if etype not in self._reported_fallbacks:
                print(f"DEBUG: Using fallback for {etype} (Sprite ID {sprite_id})")
                self._reported_fallbacks.add(etype)
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
