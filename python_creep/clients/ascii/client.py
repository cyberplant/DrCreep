import socket
import json
import threading
import time
import sys
import traceback
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.containers import Container, Vertical
from textual.binding import Binding
from rich.text import Text
from rich.style import Style

from python_creep.engine.assets import ASSETS

C64_COLORS = {
    0: "black", 1: "white", 2: "red", 3: "cyan", 4: "purple", 5: "green",
    6: "blue", 7: "yellow", 8: "dark_orange", 9: "dark_orange3", 10: "orange_red1",
    11: "grey37", 12: "grey50", 13: "light_green", 14: "light_sky_blue1", 15: "grey82",
}

# Reverse lookup for markup to C64 ID
COLOR_NAME_TO_ID = {v: k for k, v in C64_COLORS.items()}

C64_COLOR_NAMES = {
    0: "black", 1: "white", 2: "red", 3: "cyan", 4: "purple", 5: "green",
    6: "blue", 7: "yellow", 8: "orange", 9: "brown", 10: "light_red",
    11: "dark_grey", 12: "grey", 13: "light_green", 14: "light_blue", 15: "light_grey",
}

class GameStatus(Static):
    def update_status(self, state):
        if not state:
            self.update("Connecting...")
            return
        player = state['players'][0]
        room_id = str(player['room_id'])
        keys_str = ", ".join([C64_COLOR_NAMES.get(int(k) & 0xF, str(k)) for k in player.get('keys', [])])
        self.update(f"Tick: {state['tick']} | Room: {room_id} | Pos: {player['x']:.1f},{player['y']:.1f} | Keys: [{keys_str}]")

class VictoryScreen(Static):
    def compose(self) -> ComposeResult:
        art = """
                                                                                
                                                                                
                               /\\                                             
                              /  \\                                            
                             /____\\                                           
                            |      |                                            
                            |      |                                            
                           _|______|_                                           
                          |          |                                          
                          |          |                                          
         /\\               |  [   ]   |               /\\                       
        /  \\              |          |              /  \\                      
       /____\\             |          |             /____\\                     
      |      |            |          |            |      |                      
      |      |            |          |            |      |                      
     _|______|_           |          |           _|______|_                     
    |          |          |          |          |          |                    
    |          |          |          |          |          |                    
    |          |          |          |          |          |                    
    |          |          |          |          |          |                    
    |          |__________|__________|__________|          |                    
    |                                                      |                    
    |                                                      |                    
    |                 YOU ESCAPED THE CASTLE!              |                    
    |                                                      |                    
    |                  Press ACTION to Restart             |                    
    |______________________________________________________|                    
        """
        yield Static(Text(art, style="bold yellow", justify="center"))

class GameBoard(Static):
    def draw_asset(self, grid, gx, gy, asset_name, state=None, anim_name=None, tick=0, room_color="white", next_room_color="white", obj_color="white"):
        asset = ASSETS.get(asset_name)
        if not asset: return
        
        frame_markup = None
        if anim_name and "animations" in asset:
            anim = asset["animations"].get(anim_name)
            if anim:
                frames = anim["frames"]
                speed = anim.get("speed", 0)
                idx = (tick // speed) % len(frames) if speed > 0 else 0
                frame_markup = frames[idx]
            else:
                anim = asset["animations"].get("idle") or next(iter(asset["animations"].values()))
                frame_markup = anim["frames"][0]
        elif state is not None:
            if "frames" in asset:
                frames = asset["frames"]
                if state == 0: frame_markup = frames[0]
                elif state == 2: frame_markup = frames[-1]
                else: frame_markup = frames[min(1, len(frames)-1)]
            elif "states" in asset:
                frame_markup = asset["states"].get(state)
        elif "template" in asset:
            frame_markup = asset["template"]
            
        if not frame_markup: return
        
        from rich.console import Console
        dummy_console = Console()
        width, height = len(grid[0]), len(grid)
        for dy, row_markup in enumerate(frame_markup):
            ty = gy + dy
            if 0 <= ty < height:
                # Replace semantic tags
                row_markup = row_markup.replace("[room_color]", f"[{room_color}]")
                row_markup = row_markup.replace("[next_room_color]", f"[{next_room_color}]")
                row_markup = row_markup.replace("[obj_color]", f"[{obj_color}]")
                
                rich_text = Text.from_markup(row_markup)
                plain_text = rich_text.plain
                for dx, char in enumerate(plain_text):
                    tx = gx + dx
                    if 0 <= tx < width and char != ' ':
                        style = rich_text.get_style_at_offset(dummy_console, dx)
                        col_id = 1
                        if style and style.color:
                            col_id = COLOR_NAME_TO_ID.get(style.color.name, 1)
                        grid[ty][tx] = (char, col_id)

    def update_board(self, state):
        if not state:
            self.update("Waiting for initial state...")
            return
        if state.get('victory'):
            self.update("")
            return

        player = state['players'][0]
        room_id = str(player['room_id'])
        room = state['rooms'].get(room_id)
        if not room: return

        width, height = 80, 50
        grid = [[(' ', 1) for _ in range(width)] for _ in range(height)]
        debug_mode = state.get('debug_mode', False)
        room_color_id = room.get('color', 1)
        room_color_name = C64_COLOR_NAMES.get(room_color_id, "white")
        lightning_systems = room.get('lightning_systems', {})
        tick = state['tick']

        def py(y): return (int(y) * 50) // 200
        def px(x): return 2*((int(x) >> 2) - 4)

        if debug_mode:
            # Draw Grid every 10 world units
            for wy in range(0, 201, 10):
                gy = py(wy)
                if 0 <= gy < height:
                    for gx in range(width):
                        if grid[gy][gx][0] == ' ': grid[gy][gx] = ('·', 11)
            for wx in range(0, 321, 10):
                gx = px(wx)
                if 0 <= gx < width:
                    for gy in range(height):
                        if grid[gy][gx][0] == ' ': grid[gy][gx] = ('·', 11)
            
            # Draw Horizontal Ruler (Top)
            for wx in range(0, 321, 20):
                gx = px(wx)
                if 0 <= gx < width:
                    txt = str(wx)
                    for i, char in enumerate(txt):
                        if gx + i < width: grid[0][gx+i] = (char, 7) # Yellow ruler
            
            # Draw Vertical Ruler (Left)
            for wy in range(0, 201, 20):
                gy = py(wy)
                if 0 <= gy < height:
                    txt = str(wy)
                    for i, char in enumerate(txt):
                        if i < width: grid[gy][i] = (char, 7)

        # 1. Walkways
        for obj in room['objects']:
            if obj['type'] == 'walkway':
                gx, gy = px(obj['x']), py(obj['y'])
                if 0 <= gy < height:
                    for i in range(obj['properties']['length'] * 2):
                        if 0 <= gx + i < width: grid[gy][gx+i] = ('=', room_color_id)

        # 2. Objects
        for obj in room['objects']:
            type = obj['type']
            props = obj['properties']
            obj_state = obj['state']
            gx, gy = px(obj['x']), py(obj['y'])
            
            if type == 'text':
                for i, char in enumerate(props['text']):
                    if 0 <= gy < height and 0 <= gx + i*2 < width:
                        grid[gy][gx + i*2] = (char, props['color'])
            elif type == 'door':
                # Get linked room color for [next_room_color]
                nr_id = str(props.get('link_room', ''))
                nr_color = "white"
                nr_data = state['rooms'].get(nr_id)
                # Note: Currently rooms in state dict don't have 'color' field broadcasted.
                # I will assume white for now and we should update broadcast if we want it perfect.
                
                self.draw_asset(grid, gx, gy, "door", state=obj_state, room_color=room_color_name, next_room_color=nr_color)
            elif type in ['ladder', 'pole']:
                char = '#' if type == 'ladder' else '|'
                l_len = props['length'] * 2
                for i in range(l_len):
                    ty = gy + i
                    if 0 <= ty < height and 0 <= gx < width:
                        if grid[ty][gx][0] == ' ': grid[ty][gx] = (char, 1)
            elif type == 'key':
                obj_col = C64_COLOR_NAMES.get(int(props['color']) & 0xF, "white")
                self.draw_asset(grid, gx, gy, "key", obj_color=obj_col)
            elif type == 'lock':
                obj_col = C64_COLOR_NAMES.get(int(props['color']) & 0xF, "white")
                self.draw_asset(grid, gx, gy, "lock", obj_color=obj_col)
            elif type == 'teleport':
                obj_col = C64_COLOR_NAMES.get(obj_state, "white")
                self.draw_asset(grid, gx, gy, "teleport_cabin", obj_color=obj_col)
            elif type == 'teleport_target':
                obj_col = C64_COLOR_NAMES.get(int(props['color']) & 0xF, "white")
                self.draw_asset(grid, gx, gy, "teleport_target", obj_color=obj_col)
            elif type == 'doorbell':
                self.draw_asset(grid, gx, gy, "doorbell", room_color=room_color_name)
            elif type == 'forcefield_switch':
                self.draw_asset(grid, gx, gy, "forcefield_switch")
            elif type == 'forcefield':
                self.draw_asset(grid, gx, gy, "forcefield", state=obj_state)
            elif type == 'mummy_release':
                self.draw_asset(grid, gx, gy, "mummy_release", room_color=room_color_name)
            elif type == 'mummy_tomb':
                self.draw_asset(grid, gx, gy, "mummy_tomb")
            elif type == 'lightning_machine':
                self.draw_asset(grid, gx, gy, "lightning_machine")
                if lightning_systems.get(str(props.get('system_id', 0))):
                    import random
                    chars = ["\\", "|", "Y", "/"]
                    for ty in range(gy, height):
                        if grid[ty][gx][0] == '=' and ty > gy: break
                        for dx_off in range(-1, 2):
                            tx = gx + dx_off
                            if 0 <= tx < width:
                                if grid[ty][tx][0] == '=' and ty > gy: continue
                                grid[ty][tx] = (random.choice(chars), 7)
            elif type == 'trapdoor':
                if obj_state == 1:
                    for dx in range(4):
                        if 0 <= gy < height and 0 <= gx + dx < width: grid[gy][gx+dx] = (' ', 0)
            elif type == 'trapdoor_switch':
                self.draw_asset(grid, gx, gy, "trapdoor_switch")
            elif type == 'conveyor':
                anim_type = "right" if obj_state == 2 else ("left" if obj_state == 0 else "off")
                self.draw_asset(grid, gx, gy, "conveyor", anim_name=anim_type, tick=tick)
            elif type == 'conveyor_switch':
                self.draw_asset(grid, gx, gy, "conveyor_switch", obj_color=C64_COLOR_NAMES.get(5 if obj_state == 2 else (2 if obj_state == 0 else 1)))
            elif type == 'raygun':
                self.draw_asset(grid, gx, gy, "raygun")
            elif type == 'raygun_switch':
                self.draw_asset(grid, gx, gy, "raygun_switch")
            elif type == 'lightning_switch':
                self.draw_asset(grid, gx, gy, "lightning_switch")

        # 3. Mummies and Frankensteins
        for m in state.get('mummies', []):
            if str(m['room_id']) == room_id:
                mx, my = px(m['x']), py(m['y'])
                m_anim = "idle"
                if m.get('is_moving'):
                    m_anim = "walk_left" if m.get('facing_left') else "walk_right"
                self.draw_asset(grid, mx - 1, my - 6, "mummy", anim_name=m_anim, tick=tick)

        for f in state.get('frankies', []):
            if str(f['room_id']) == room_id:
                fx, fy = px(f['x']), py(f['y'])
                f_anim = "idle"
                if f.get('is_moving'):
                    f_anim = "walk_left" if f.get('facing_left') else "walk_right"
                self.draw_asset(grid, fx - 1, fy - 6, "frankie", anim_name=f_anim, tick=tick)

        for p in state.get('projectiles', []):
            if str(p['room_id']) == room_id:
                px_p, py_p = px(p['x']), py(p['y'])
                if 0 <= py_p < height:
                    for dx in range(-1, 2):
                        if 0 <= px_p + dx < width: grid[py_p][px_p+dx] = ('-', 2)

        # 4. Player
        pgx, pgy = px(player['x']), py(player['y'])
        if player.get('is_dead'):
            # Disintegration effect
            import random
            chars = ["*", ".", " ", "x", "+"]
            for dy in range(-6, 0):
                for dx in range(-2, 3):
                    if random.random() > 0.3:
                        tx, ty = pgx + dx, pgy + dy
                        if 0 <= ty < height and 0 <= tx < width:
                            grid[ty][tx] = (random.choice(chars), random.choice([1, 7, 11, 15]))
        else:
            p_anim = "idle"
            if player.get('is_acting', 0) > 0: p_anim = "action"
            elif player.get('is_moving', False): p_anim = "walk_left" if player.get('facing_left') else "walk_right"
            self.draw_asset(grid, pgx - 1, pgy - 6, "player", anim_name=p_anim, tick=tick)

        res = Text()
        border = "+" + "-" * width + "+\n"
        res.append(border)
        for row in grid:
            res.append("|")
            for char, color_idx in row:
                res.append(char, style=C64_COLORS.get(color_idx & 0xF, "white"))
            res.append("|\n")
        res.append(border)
        self.update(res)

class DebugSidebar(Static):
    def update_info(self, state):
        if not state or not state.get('debug_mode'):
            self.styles.display = "none"
            return
        
        self.styles.display = "block"
        player = state['players'][0]
        room_id = str(player['room_id'])
        room = state['rooms'].get(room_id)
        if not room: return

        res = Text("--- DEBUG: ROOM OBJECTS ---\n", style="bold yellow")
        
        # Room global systems
        l_sys = room.get('lightning_systems', {})
        if l_sys:
            res.append("Lightning Systems State:\n", style="bold cyan")
            for sid, status in l_sys.items():
                res.append(f"  ID {sid}: {'ON' if status else 'OFF'}\n", style="green" if status else "red")

        for i, obj in enumerate(room['objects']):
            # Basic Header
            res.append(f"\n{i:02}: {obj['type'].upper()}\n", style="bold white underline")
            res.append(f"  Pos: ({obj['x']}, {obj['y']})  State: {obj['state']}\n", style="white")
            
            # End position calculation for environment
            props = obj.get('properties', {})
            if 'length' in props:
                length = props['length']
                if obj['type'] == 'walkway':
                    res.append(f"  End X: {obj['x'] + (length * 4)}\n", style="yellow")
                elif obj['type'] in ('ladder', 'pole'):
                    res.append(f"  End Y: {obj['y'] + (length * 8)}\n", style="yellow")

            # Dump ALL properties
            for k, v in props.items():
                if k not in ('x', 'y', 'type', 'obj_index'):
                    res.append(f"  - {k}: {v}\n", style="cyan")
            
            if obj.get('timer', 0) > 0:
                res.append(f"  - TIMER: {obj['timer']}\n", style="bold red")
        
        self.update(res)

class CreepApp(App):
    CSS = """
    GameStatus { background: $boost; color: white; height: 1; padding: 0 1; }
    #game-container { layout: horizontal; }
    GameBoard { width: 84; height: 54; border: solid green; margin: 0 2; content-align: left top; }
    DebugSidebar { width: 60; height: 54; border: solid blue; padding: 1; overflow-y: scroll; }
    VictoryScreen { width: 84; height: 54; border: solid yellow; margin: 0 2; content-align: center middle; display: none; }
    """
    BINDINGS = [
        Binding("w", "move('up')", "Up"), Binding("s", "move('down')", "Down"),
        Binding("a", "move('left')", "Left"), Binding("d", "move('right')", "Right"),
        Binding("space", "action", "Action"), Binding("enter", "action", "Action"), Binding("q", "quit", "Quit"),
    ]

    def __init__(self, host='127.0.0.1', port=4242):
        super().__init__()
        self.host, self.port, self.sock, self.state, self.running = host, port, None, {}, False

    def compose(self) -> ComposeResult:
        yield Header()
        yield GameStatus()
        with Container(id="game-container"):
            yield GameBoard()
            yield DebugSidebar()
            yield VictoryScreen()
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            self.running = True
            threading.Thread(target=self._receive_loop, daemon=True).start()
            self.set_interval(0.05, self._refresh_ui)
        except Exception as e:
            self.notify(f"Connection failed: {e}", severity="error")

    def _receive_loop(self):
        f = self.sock.makefile('r')
        while self.running:
            try:
                line = f.readline()
                if not line: self.running = False; self.exit(); break
                self.state = json.loads(line)
            except: break

    def _refresh_ui(self):
        if self.state:
            self.query_one(GameStatus).update_status(self.state)
            self.query_one(DebugSidebar).update_info(self.state)
            is_victory = self.state.get('victory', False)
            if is_victory:
                self.query_one(GameBoard).styles.display = "none"
                self.query_one(VictoryScreen).styles.display = "block"
            else:
                self.query_one(VictoryScreen).styles.display = "none"
                self.query_one(GameBoard).styles.display = "block"
                self.query_one(GameBoard).update_board(self.state)

    def action_move(self, direction: str) -> None:
        commands = {'up': False, 'down': False, 'left': False, 'right': False, 'action': False}
        commands[direction] = True; self._send_input(commands)

    def action_action(self) -> None:
        if self.state.get('victory'): self._send_input({'restart': True})
        else: self._send_input({'up': False, 'down': False, 'left': False, 'right': False, 'action': True})

    def _send_input(self, commands):
        if self.sock:
            msg = {'type': 'INPUT', 'player_id': 0, 'commands': commands}
            try: self.sock.sendall((json.dumps(msg) + "\n").encode())
            except: self.running = False

if __name__ == "__main__":
    try:
        app = CreepApp()
        app.run()
    except Exception:
        with open("client.log", "a") as f:
            f.write(traceback.format_exc())
        traceback.print_exc(file=sys.stderr)
