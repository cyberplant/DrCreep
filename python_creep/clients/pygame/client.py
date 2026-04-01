import pygame
import socket
import json
import threading
import sys
import os
import argparse
from datetime import datetime

# Add current directory to path to import engine modules
sys.path.append(os.getcwd())

from clients.pygame.assets import C64_PALETTE
from clients.pygame.renderer import PygameRenderer

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
        self._screenshot_requested = False
        
        self.renderer = PygameRenderer(debug_mode=debug)

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

    def render(self):
        if self.audio_enabled:
            for ev in self.state.get('events', []):
                if ev in self.sounds: self.sounds[ev].play()

        world_surface = self.renderer.render_state(self.state)

        scaled = pygame.transform.scale(world_surface, self.screen.get_size())
        self.screen.blit(scaled, (0, 0))
        if self._screenshot_requested: self._take_screenshot()
        pygame.display.flip()

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
