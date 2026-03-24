import socket
import json
import threading
import time
import sys
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
        keys_str = ", ".join([C64_COLOR_NAMES.get(k & 0xF, str(k)) for k in player.get('keys', [])])
        self.update(f"Tick: {state['tick']} | Room: {room_id} | Pos: {player['x']:.1f},{player['y']:.1f} | Keys: [{keys_str}]")

class GameBoard(Static):
    def update_board(self, state):
        if not state:
            self.update("Waiting for initial state...")
            return

        player = state['players'][0]
        room_id = str(player['room_id'])
        room = state['rooms'].get(room_id)
        
        if not room:
            self.update(f"Player in unknown room {room_id}")
            return

        # 2X scale: 80x50 content
        width, height = 80, 50
        grid = [[(' ', 1) for _ in range(width)] for _ in range(height)]
        floor_color = 1 
        lightning_systems = room.get('lightning_systems', {})

        def py(y): return (int(y) // 4)
        def px(x): return 2*((int(x) >> 2) - 4)

        # 1. Walkways (Fixed at y // 4)
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
                        # Height is 8. bottom is gy + 8. Walkway is gy.
                        # Original: Door top=160 (gy=40), Walkway=192 (gy=48).
                        # So door should draw from 40 to 47.
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
                                    else: c = ' '
                            grid[ty][tx] = (c, color)
            elif type in ['ladder', 'pole']:
                char = '#' if type == 'ladder' else '|'
                for i in range(props['length'] * 2):
                    ty = gy + i
                    if 0 <= ty < height and 0 <= gx < width:
                        if grid[ty][gx][0] == ' ': grid[ty][gx] = (char, floor_color)
            elif type == 'key':
                if 0 <= gy + 7 < height: grid[gy+7][gx] = ('k', props['color'])
            elif type == 'lock':
                if 0 <= gy + 5 < height: grid[gy+5][gx] = ('X', props['color'])
            elif type == 'teleport':
                if 0 <= gy + 3 < height: grid[gy+3][gx] = ('T', (obj_state + 2) % 16)
            elif type == 'teleport_target':
                if 0 <= gy + 7 < height: grid[gy+7][gx] = ('t', props['color'])
            elif type == 'doorbell':
                if 0 <= gy + 5 < height: grid[gy+5][gx] = ('●', floor_color)
            elif type == 'forcefield_switch':
                if 0 <= gy + 5 < height:
                    grid[gy+5][gx] = ('S', 3)
                    if obj.get('timer', 0) > 0:
                        status = f"[{obj['timer']}]"
                        for i, c in enumerate(status):
                            if 0 <= gy+5 < height and 0 <= gx + 1 + i < width:
                                grid[gy+5][gx+1+i] = (c, 3)
            elif type == 'forcefield':
                for dy in range(0, 8):
                    ty = gy + dy
                    if 0 <= ty < height:
                        grid[ty][gx] = ('z' if dy == 0 else ('.' if obj_state == 1 else ' '), 3)
            elif type == 'mummy_release':
                if 0 <= gy + 7 < height: grid[gy+7][gx] = ('M', 1)
            elif type == 'mummy_tomb':
                for dy in range(4):
                    for dx in range(-2, 3):
                        ty, tx = gy + 4 + dy, gx + dx
                        if 0 <= ty < height and 0 <= tx < width:
                            grid[ty][tx] = ('#', 2)
            elif type == 'lightning_machine':
                sys_id_str = str(props.get('system_id', 0))
                if 0 <= gy + 7 < height: grid[gy+7][gx] = ('L', 3)
                if lightning_systems.get(sys_id_str):
                    import random
                    chars = ["\\", "|", "Y", "/"]
                    for dy in range(8, 24):
                        ty = gy + dy
                        if 0 <= ty < height and 0 <= gx < width:
                            if grid[ty][gx][0] == '=': break
                            grid[ty][gx] = (random.choice(chars), 7)
            elif type == 'lightning_switch':
                if 0 <= gy + 5 < height:
                    grid[gy+5][gx] = ('S', 3)
                    is_on = lightning_systems.get(str(props.get('system_id', 0)))
                    status = "(ON)" if is_on else "(OFF)"
                    for i, c in enumerate(status):
                        if 0 <= gy+5 < height and 0 <= gx + 1 + i < width:
                            grid[gy+5][gx+1+i] = (c, 3)

        # 3. Mummies
        for m in state.get('mummies', []):
            if str(m['room_id']) == room_id:
                mx, my = px(m['x']), py(m['y'])
                if 0 <= mx < width and 0 <= my < height:
                    for dy in range(6):
                        ty = my - 5 + dy
                        if 0 <= ty < height:
                            grid[ty][mx] = ('O' if dy==0 else ('|' if dy<5 else '^'), 1)

        # 4. Player (3 wide, 6 high, stick-man style)
        pgx, pgy = px(player['x']), py(player['y'])
        tick = state['tick']
        is_moving = player.get('is_moving', False)
        is_acting = player.get('is_acting', 0) > 0
        
        def safe_set(ty, tx, char, col):
            if 0 <= ty < height and 0 <= tx < width:
                grid[ty][tx] = (char, col)

        # Head (Centered at pgx)
        safe_set(pgy-5, pgx, 'O', 7)
        # Torso & Arms
        arm_l, arm_r = '/', '\\'
        if is_acting: 
            # Toggle arm direction for wave
            arm_r = '/' if (tick % 2 == 0) else '\\'
        safe_set(pgy-4, pgx-1, arm_l, 6)
        safe_set(pgy-4, pgx,   '|', 6)
        safe_set(pgy-4, pgx+1, arm_r, 6)
        safe_set(pgy-3, pgx, '|', 6)
        safe_set(pgy-2, pgx, '|', 6)
        # Legs
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
            self.query_one(GameBoard).update_board(self.state)

    def action_move(self, direction: str) -> None:
        commands = {'up': False, 'down': False, 'left': False, 'right': False, 'action': False}
        commands[direction] = True; self._send_input(commands)

    def action_action(self) -> None:
        self._send_input({'up': False, 'down': False, 'left': False, 'right': False, 'action': True})

    def _send_input(self, commands):
        if self.sock:
            msg = {'type': 'INPUT', 'player_id': 0, 'commands': commands}
            try: self.sock.sendall((json.dumps(msg) + "\n").encode())
            except: self.running = False

    def compose(self) -> ComposeResult:
        yield Header(); yield GameStatus(); yield Vertical(GameBoard()); yield Footer()

if __name__ == "__main__":
    app = CreepApp(); app.run()
