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

C64_COLORS = {
    0: "black", 1: "white", 2: "red", 3: "cyan", 4: "purple", 5: "green",
    6: "blue", 7: "yellow", 8: "dark_orange", 9: "brown", 10: "orange_red1",
    11: "grey37", 12: "grey50", 13: "light_green", 14: "light_sky_blue1", 15: "grey82",
}

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
        
        if not room:
            self.update(f"Player in unknown room {room_id}")
            return

        width, height = 80, 50
        grid = [[(' ', 1) for _ in range(width)] for _ in range(height)]
        floor_color = 1 
        lightning_systems = room.get('lightning_systems', {})

        def py(y): return (int(y) // 4)
        def px(x): return 2*((int(x) >> 2) - 4)

        # 1. Walkways
        for obj in room['objects']:
            if obj['type'] == 'walkway':
                gx, gy = px(obj['x']), py(obj['y'])
                if 0 <= gy < height:
                    for i in range(obj['properties']['length'] * 2):
                        if 0 <= gx + i < width: grid[gy][gx+i] = ('=', floor_color)

        # 2. Objects
        for obj in room['objects']:
            type = obj['type']
            props = obj['properties']
            obj_state = obj['state']
            
            if type == 'text':
                gx, gy = px(props['x']), py(props['y'])
                for i, char in enumerate(props['text']):
                    if 0 <= gy < height and 0 <= gx + i*2 < width:
                        grid[gy][gx + i*2] = (char, props['color'])
                continue

            gx, gy = px(obj['x']), py(obj['y'])
            if type == 'walkway': continue

            if type == 'door':
                color = 2 if props['is_exit'] else floor_color
                for dy in range(8):
                    for dx in range(10):
                        ty, tx = gy + dy, gx + dx
                        if 0 <= ty < height and 0 <= tx < width:
                            c = ' '
                            if props['is_exit']:
                                labels = ["----------", " EXIT DOOR ", "----------"]
                                if 1 <= dy <= 3: c = labels[dy-1][dx]
                            else:
                                if dx in [0,9]: c = '[' if dx == 0 else ']'
                                elif dy in [0,7]: c = '-'
                                else:
                                    if obj_state == 0: c = '░'
                                    elif obj_state == 1: c = ' ' if dy >= 4 else '░'
                                    else:
                                        if dy == 4: c = '_' if dx > 4 else ' '
                                        elif dy == 5: c = ' ' if dx == 5 else ('\\' if dx == 6 else ' ')
                                        elif dy == 6: c = ' ' if dx <= 6 else ('\\' if dx == 7 else ' ')
                                        else: c = ' '
                            grid[ty][tx] = (c, color)
            elif type in ['ladder', 'pole']:
                char = '#' if type == 'ladder' else '|'
                for i in range(props['length'] * 2):
                    ty = gy + i
                    if 0 <= ty < height and 0 <= gx < width:
                        if grid[ty][gx][0] == ' ': grid[ty][gx] = (char, floor_color)
            elif type == 'key':
                if 0 <= gy < height: grid[gy][gx] = ('k', props['color'])
            elif type == 'lock':
                if 0 <= gy < height: grid[gy][gx] = ('X', props['color'])
            elif type == 'teleport':
                # Cabin style
                color = (obj_state + 2) % 16
                for dy in range(8):
                    for dx in range(6):
                        ty, tx = gy + dy, gx + dx - 1
                        if 0 <= ty < height and 0 <= tx < width:
                            if dy == 0: grid[ty][tx] = ('=', color)
                            elif dx == 0: grid[ty][tx] = ('[', color)
                            elif dx == 5: grid[ty][tx] = (']', color)
            elif type == 'teleport_target':
                if 0 <= gy < height: grid[gy][gx] = ('●', props['color'])
            elif type == 'doorbell':
                if 0 <= gy < height: grid[gy][gx] = ('●', floor_color)
            elif type == 'forcefield_switch':
                if 0 <= gy < height:
                    grid[gy][gx] = ('S', 3)
                    if obj.get('timer', 0) > 0:
                        status = f"[{obj['timer']}]"
                        for i, c in enumerate(status):
                            if 0 <= gy < height and 0 <= gx + 1 + i < width:
                                grid[gy][gx+1+i] = (c, 3)
            elif type == 'forcefield':
                for dy in range(0, 8):
                    ty = gy + dy
                    if 0 <= ty < height:
                        grid[ty][gx] = ('z' if dy == 0 else ('.' if obj_state == 1 else ' '), 3)
            elif type == 'mummy_release':
                if 0 <= gy < height: grid[gy][gx] = ('M', 1)
            elif type == 'mummy_tomb':
                for dy in range(4):
                    for dx in range(-2, 3):
                        ty, tx = gy + dy, gx + dx
                        if 0 <= ty < height and 0 <= tx < width:
                            grid[ty][tx] = ('#', 2)
            elif type == 'lightning_machine':
                sys_id_str = str(props.get('system_id', 0))
                if 0 <= gy < height: grid[gy][gx] = ('L', 3)
                if lightning_systems.get(sys_id_str):
                    import random
                    chars = ["\\", "|", "Y", "/"]
                    for dy in range(1, 24):
                        ty = gy + dy
                        if 0 <= ty < height:
                            for dx_off in range(-1, 2):
                                tx = gx + dx_off
                                if 0 <= tx < width:
                                    if grid[ty][tx][0] == '=': continue
                                    grid[ty][tx] = (random.choice(chars), 7)
            elif type == 'trapdoor':
                if obj_state == 1:
                    for dx in range(4):
                        if 0 <= gy + 8 < height and 0 <= gx + dx < width:
                            grid[gy+8][gx+dx] = (' ', 1)
            elif type == 'trapdoor_switch':
                if 0 <= gy < height: grid[gy][gx] = ('o', 3)
            elif type == 'conveyor':
                # Slower animation
                c_char = ' '
                frame = (state['tick'] // 4) % 4
                if obj_state == 0: # Left
                    c_char = '\\' if (gx + frame) % 4 < 2 else ' '
                elif obj_state == 2: # Right
                    c_char = '/' if (gx - frame) % 4 < 2 else ' '
                else:
                    c_char = '-'
                for dx in range(10):
                    if 0 <= gy < height and 0 <= gx + dx < width:
                        grid[gy][gx+dx] = (c_char if obj_state != 1 else ('/' if dx%2==0 else '\\'), 6)
            elif type == 'conveyor_switch':
                if 0 <= gy < height:
                    switch_str = "<< O >>"
                    col = 5 if obj_state == 2 else (2 if obj_state == 0 else 1)
                    for i, c in enumerate(switch_str):
                        if 0 <= gx + i < width: grid[gy][gx+i] = (c, col)
            elif type == 'raygun':
                if 0 <= gy < height:
                    for i, c in enumerate(">====>"):
                        if 0 <= gx + i < width: grid[gy][i] = (c, 2)
            elif type == 'raygun_switch':
                if 0 <= gy < height:
                    for dy, row in enumerate([" ^ ", " O ", " v "]):
                        for i, c in enumerate(row):
                            if 0 <= gy + dy < height and 0 <= gx + i < width:
                                grid[gy+dy][gx+i] = (c, 3)
            elif type == 'lightning_switch':
                if 0 <= gy < height:
                    grid[gy][gx] = ('S', 3)
                    is_on = lightning_systems.get(str(props.get('system_id', 0)))
                    status = "(ON)" if is_on else "(OFF)"
                    for i, c in enumerate(status):
                        if 0 <= gy < height and 0 <= gx + 1 + i < width:
                            grid[gy][gx+1+i] = (c, 3)

        # 3. Mummies and Frankensteins
        for m in state.get('mummies', []):
            if str(m['room_id']) == room_id:
                mx, my = px(m['x']), py(m['y'])
                if 0 <= mx < width and 0 <= my < height:
                    for dy in range(6):
                        ty = my - 5 + dy
                        if 0 <= ty < height:
                            grid[ty][mx] = ('O' if dy==0 else ('|' if dy<5 else '^'), 1)

        for f in state.get('frankies', []):
            if str(f['room_id']) == room_id:
                fx, fy = px(f['x']), py(f['y'])
                def safe_set_f(ty, tx, char):
                    if 0 <= ty < height and 0 <= tx < width:
                        grid[ty][tx] = (char, 5) # Green
                safe_set_f(fy-5, fx, 'O')
                safe_set_f(fy-4, fx-1, '/')
                safe_set_f(fy-4, fx, '|')
                safe_set_f(fy-4, fx+1, '\\')
                safe_set_f(fy-3, fx, '|')
                safe_set_f(fy-2, fx, '|')
                is_f_moving = state['tick'] % 4 < 2
                safe_set_f(fy-1, fx-1, '(' if is_f_moving else '/')
                safe_set_f(fy-1, fx+1, ')' if is_f_moving else '\\')

        for p in state.get('projectiles', []):
            if str(p['room_id']) == room_id:
                px_p, py_p = px(p['x']), py(p['y'])
                if 0 <= py_p < height:
                    for dx in range(-1, 2):
                        if 0 <= px_p + dx < width:
                            grid[py_p][px_p+dx] = ('-', 2)

        # 4. Player (Stick-man)
        pgx, pgy = px(player['x']), py(player['y'])
        tick = state['tick']
        is_moving = player.get('is_moving', False)
        is_acting = player.get('is_acting', 0) > 0
        teleport_stage = player.get('is_teleporting', 0)
        
        def safe_set(ty, tx, char, col):
            if 0 <= ty < height and 0 <= tx < width:
                if teleport_stage > 0:
                    visible_rows = (teleport_stage * 6) // 20
                    if (pgy - ty) > visible_rows: return
                grid[ty][tx] = (char, col)

        safe_set(pgy-5, pgx, 'O', 7)
        arm_l, arm_r = '/', '\\'
        if is_acting: arm_r = '/'
        safe_set(pgy-4, pgx-1, arm_l, 6)
        safe_set(pgy-4, pgx,   '|', 6)
        safe_set(pgy-4, pgx+1, arm_r, 6)
        safe_set(pgy-3, pgx, '|', 6)
        safe_set(pgy-2, pgx, '|', 6)
        leg_l, leg_r = '/', '\\'
        if is_moving and tick % 4 < 2:
            leg_l, leg_r = '(', ')'
        safe_set(pgy-1, pgx-1, leg_l, 5)
        safe_set(pgy-1, pgx+1, leg_r, 5)

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

class CreepApp(App):
    CSS = """
    GameStatus {
        background: $boost;
        color: white;
        height: 1;
        padding: 0 1;
    }
    GameBoard {
        width: 84;
        height: 54;
        border: solid green;
        margin: 0 2;
        content-align: left top;
    }
    VictoryScreen {
        width: 84;
        height: 54;
        border: solid yellow;
        margin: 0 2;
        content-align: center middle;
        display: none;
    }
    """
    BINDINGS = [
        Binding("w", "move('up')", "Up"),
        Binding("s", "move('down')", "Down"),
        Binding("a", "move('left')", "Left"),
        Binding("d", "move('right')", "Right"),
        Binding("up", "move('up')", "Up", show=False),
        Binding("down", "move('down')", "Down", show=False),
        Binding("left", "move('left')", "Left", show=False),
        Binding("right", "move('right')", "Right", show=False),
        Binding("space", "action", "Action"),
        Binding("enter", "action", "Action"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, host='127.0.0.1', port=4242):
        super().__init__()
        self.host, self.port, self.sock, self.state, self.running = host, port, None, {}, False

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
                if not line: 
                    self.running = False; self.exit(); break
                self.state = json.loads(line)
            except: break

    def _refresh_ui(self):
        if self.state:
            self.query_one(GameStatus).update_status(self.state)
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
        if self.state.get('victory'):
            self._send_input({'restart': True})
        else:
            self._send_input({'up': False, 'down': False, 'left': False, 'right': False, 'action': True})

    def _send_input(self, commands):
        if self.sock:
            msg = {'type': 'INPUT', 'player_id': 0, 'commands': commands}
            try: self.sock.sendall((json.dumps(msg) + "\n").encode())
            except: self.running = False

    def compose(self) -> ComposeResult:
        yield Header(); yield GameStatus(); yield Vertical(GameBoard(), VictoryScreen()); yield Footer()

if __name__ == "__main__":
    try:
        app = CreepApp()
        app.run()
    except Exception:
        with open("client.log", "a") as f:
            f.write(traceback.format_exc())
        traceback.print_exc(file=sys.stderr)
