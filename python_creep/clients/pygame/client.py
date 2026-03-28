import pygame
import socket
import json
import threading
import sys
import os

from python_creep.clients.pygame.assets import C64_PALETTE, C64Assets

# Add current directory to path to import engine modules
sys.path.append(os.getcwd())

class PygameClient:
    def __init__(self, host='127.0.0.1', port=4242):
        pygame.init()
        self.screen = pygame.display.set_mode((640, 480))
        pygame.display.set_caption("The Castles of Dr. Creep (Pygame)")
        self.clock = pygame.time.Clock()
        
        self.host, self.port = host, port
        self.sock = None
        self.state = {}
        self.running = True
        self._reported_fallbacks = set()
        
        # Robust Pathing
        # Assuming script is in /clients/pygame/client.py
        # data is in /data/
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        
        sprite_path = os.path.join(project_root, "data", "extracted_sprites")
        tile_path = os.path.join(project_root, "data", "tileset.png")
        
        # Load assets
        print(f"DEBUG: Project Root identified as: {project_root}")
        self.assets = C64Assets(sprite_path, tile_path)
        
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
                if not data: 
                    print("DEBUG: Server closed connection.")
                    break
                buffer += data
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.state = json.loads(line)
                    if not hasattr(self, '_received_first_tick'):
                        print(f"DEBUG: Received first state update. Tick: {self.state.get('tick')}")
                        self._received_first_tick = True
            except Exception as e:
                print(f"ERROR: Receive loop exception: {e}")
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
                    filename = f"screenshot_{int(time.time())}.png"
                    pygame.image.save(self.screen, filename)
                    print(f"DEBUG: Screenshot saved to {filename}")
        
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

    def ascii_to_screen_code(self, char):
        c = ord(char)
        if 64 <= c <= 95: return c - 64
        if 32 <= c <= 63: return c
        if 96 <= c <= 127: return c - 64
        return c & 0x3F

    def draw_char(self, char, x_char, y_char, color_idx):
        code = self.ascii_to_screen_code(char) if isinstance(char, str) else char
        tile = self.assets.get_tile(code, color_idx)
        if tile:
            self.world_surface.blit(tile, (x_char * 8, y_char * 8))

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
                    room_color = room.get('color', 1)

                    # Draw Objects
                    for obj in room['objects']:
                        ot = obj['type']
                        ox, oy = obj['x'], obj['y']
                        props = obj.get('properties', {})
                        obj_state = obj.get('state', 0)
                        
                        # Tile coordinates: engine coordinates are already in pixel units (0-320)
                        # tx = x / 8, ty = y / 8
                        tx, ty = int(ox) // 8, int(oy) // 8
                        
                        if ot == 'walkway':
                            for i in range(props.get('length', 0)):
                                self.draw_char(64, tx + i, ty, room_color)
                                self.draw_char(105, tx + i, ty + 1, room_color)
                        elif ot == 'ladder':
                            for i in range(props.get('length', 0) * 2):
                                self.draw_char('#', tx, ty + i, room_color)
                        elif ot == 'pole':
                            for i in range(props.get('length', 0) * 2):
                                self.draw_char(']', tx, ty + i, room_color)
                        elif ot == 'door':
                            color = 2 if props.get('is_exit') else room_color
                            for dy in range(4):
                                for dx in range(5):
                                    char = '#'
                                    if dx == 0: char = '['
                                    elif dx == 4: char = ']'
                                    elif dy == 0 or dy == 3: char = '-'
                                    self.draw_char(char, tx + dx, ty + dy, color)
                        elif ot in ['key', 'lock', 'doorbell', 'teleport', 'teleport_target', 'text', 'mummy_tomb', 'mummy_release', 'trapdoor_switch', 'conveyor', 'conveyor_switch']:
                            # Simplified bulk handling for now
                            if ot == 'key': self.draw_char('K', tx, ty, props.get('color', 1))
                            elif ot == 'lock': self.draw_char('X', tx, ty, props.get('color', 1))
                            elif ot == 'doorbell': self.draw_char(81, tx, ty, room_color)
                            elif ot == 'teleport': self.draw_char('T', tx, ty, obj_state)
                            elif ot == 'teleport_target': self.draw_char('t', tx, ty, props.get('color', 1))
                            elif ot == 'text':
                                for i, char in enumerate(props.get('text', "")):
                                    self.draw_char(char, tx + i, ty, props.get('color', 1))
                            elif ot == 'mummy_tomb':
                                for dy in range(3):
                                    for dx in range(5):
                                        self.draw_char('#', tx + dx, ty + dy, 2)
                            elif ot == 'mummy_release': self.draw_char('M', tx, ty, 1)
                            elif ot == 'trapdoor_switch': self.draw_char('o', tx, ty, 3)
                            elif ot == 'conveyor':
                                for i in range(10): self.draw_char(64, tx + i, ty, 6)
                            elif ot == 'conveyor_switch': self.draw_char(81, tx, ty, 1)

                    # Draw Entities
                    for m in self.state.get('mummies', []):
                        if str(m['room_id']) == room_id:
                            self.draw_entity_sprite('mummy', m['x'], m['y'], m.get('facing_left'))

                    for f in self.state.get('frankies', []):
                        if str(f['room_id']) == room_id:
                            self.draw_entity_sprite('frankie', f['x'], f['y'], f.get('facing_left'))

                    self.draw_entity_sprite('player', player['x'], player['y'], player.get('facing_left'))
                    if self.state.get('tick', 0) % 50 == 0:
                        print(f"DEBUG: Player Pos: ({player['x']:.1f}, {player['y']:.1f})")
                else:
                    if not hasattr(self, '_reported_missing_room'):
                        print(f"DEBUG: Current room {room_id} not found in state data.")
                        self._reported_missing_room = True
            except Exception as e:
                print(f"ERROR: Render exception: {e}")
                # traceback.print_exc()

        # Scale and blit to main screen
        scaled = pygame.transform.scale(self.world_surface, (320 * self.scale, 200 * self.scale))
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def draw_entity_sprite(self, etype, x, y, facing_left):
        sprite_id = 0
        if etype == 'player':
            # Swap: was 3 if facing_left else 0
            sprite_id = 0 if facing_left else 3
        elif etype == 'mummy':
            sprite_id = 0x4B if facing_left else 0x4E
        elif etype == 'frankie':
            sprite_id = 0x87 if facing_left else 0x84
        
        sprite = self.assets.get_sprite(sprite_id)
        if sprite:
            self.world_surface.blit(sprite, (x - 8, y - 21))
        else:
            if etype not in self._reported_fallbacks:
                print(f"DEBUG: Using fallback for {etype} (Sprite ID {sprite_id} not found in {len(self.assets.sprites)} loaded sprites)")
                self._reported_fallbacks.add(etype)
            
            color = C64_PALETTE[1]
            if etype == 'mummy': color = C64_PALETTE[15]
            elif etype == 'frankie': color = C64_PALETTE[5]
            pygame.draw.rect(self.world_surface, color, (x, y - 24, 8, 24))

    def run(self):
        self.connect()
        while self.running:
            self.handle_events()
            self.render()
            self.clock.tick(50)
        pygame.quit()

if __name__ == "__main__":
    client = PygameClient()
    client.run()
