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

class GameStatus(Static):
    def update_status(self, state):
        if not state:
            self.update("Connecting...")
            return
        player = state['players'][0]
        room_id = str(player['room_id'])
        self.update(f"Tick: {state['tick']} | Room: {room_id} | Pos: {player['x']:.1f},{player['y']:.1f}")

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

        width, height = 40, 25
        grid = [[(' ', 1) for _ in range(width)] for _ in range(height)]
        floor_color = 1 
        lightning_systems = room.get('lightning_systems', {})

        for obj in room['objects']:
            type = obj['type']
            props = obj['properties']
            obj_state = obj['state']
            
            if type == 'text':
                x_grid, y_grid = (props['x'] >> 2) - 4, props['y'] >> 3
                for i, char in enumerate(props['text']):
                    if 0 <= y_grid < height and 0 <= x_grid + i < width:
                        grid[y_grid][x_grid+i] = (char, props['color'])
                continue

            x_grid, y_grid = (obj['x'] >> 2) - 4, obj['y'] >> 3
            if type in ['frankie', 'mummy']: y_grid += 2
            
            if not (0 <= x_grid < width and 0 <= y_grid < height):
                continue

            if type == 'walkway':
                for i in range(props['length']):
                    if 0 <= x_grid + i < width: grid[y_grid][x_grid+i] = ('=', floor_color)
            elif type in ['ladder', 'pole']:
                char = '#' if type == 'ladder' else '|'
                for i in range(props['length']):
                    if 0 <= y_grid + i < height: grid[y_grid+i][x_grid] = (char, floor_color)
            elif type == 'door':
                is_exit = props['is_exit']
                color = 2 if is_exit else floor_color
                for dy in range(4):
                    for dx in range(5):
                        if 0 <= y_grid + dy < height and 0 <= x_grid + dx < width:
                            c = ' '
                            if is_exit:
                                c = ["-----", "EXIT ", " DOOR", "-----"][dy][dx]
                            else:
                                if dx in [0,4]: c = '[' if dx == 0 else ']'
                                elif dy == 0 or dy == 3: c = '-'
                                else:
                                    if obj_state == 0: c = '░'
                                    elif obj_state == 1: c = ' ' if dy >= 2 else '░'
                                    else: c = ' '
                            grid[y_grid+dy][x_grid+dx] = (c, color)

            elif type == 'key': grid[y_grid][x_grid] = ('k', props['color'])
            elif type == 'lock': grid[y_grid][x_grid] = ('X', floor_color)
            elif type == 'mummy': grid[y_grid][x_grid] = ('M', 1)
            elif type == 'frankie': grid[y_grid][x_grid] = ('F', 1)
            elif type == 'teleport': grid[y_grid][x_grid] = ('T', props['color'])
            elif type == 'teleport_target': grid[y_grid][x_grid] = ('t', props['color'])
            elif type == 'doorbell': grid[y_grid][x_grid] = ('●', floor_color)
            elif type == 'lightning_machine':
                sys_id = str(props.get('system_id', 0))
                grid[y_grid][x_grid] = ('L', 3)
                if lightning_systems.get(sys_id):
                    # Animated rays reaching floor (approx 10 chars)
                    import random
                    chars = ["\\", "|", "Y", "/"]
                    for dy in range(1, 11):
                        for dx in range(0, 2):
                            if 0 <= y_grid + dy < height and 0 <= x_grid + dx < width:
                                grid[y_grid+dy][x_grid+dx] = (random.choice(chars), 7)
            elif type == 'lightning_switch':
                sys_id = str(props.get('system_id', 0))
                grid[y_grid][x_grid] = ('S', 3)
                is_on = lightning_systems.get(sys_id)
                status = "(ON)" if is_on else "(OFF)"
                for i, c in enumerate(status):
                    if 0 <= y_grid < height and 0 <= x_grid + 1 + i < width:
                        grid[y_grid][x_grid+1+i] = (c, 3)

        px, py = (int(player['x']) >> 2) - 4, int(player['y']) >> 3
        chars = ['O', '|', '|', '^']
        for i, char in enumerate(reversed(chars)):
            target_y = py - i
            if 0 <= px < width and 0 <= target_y < height:
                grid[target_y][px] = (char, 1)

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
        width: 44;
        height: 29;
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
        Binding("space", "action", "Action"),
        Binding("enter", "action", "Action"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, host='127.0.0.1', port=4242):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self.state = {}
        self.running = False

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
                    self.running = False
                    self.exit()
                    break
                self.state = json.loads(line)
            except:
                break

    def _refresh_ui(self):
        if self.state:
            self.query_one(GameStatus).update_status(self.state)
            self.query_one(GameBoard).update_board(self.state)

    def action_move(self, direction: str) -> None:
        commands = {'up': False, 'down': False, 'left': False, 'right': False, 'action': False}
        commands[direction] = True
        self._send_input(commands)

    def action_action(self) -> None:
        self._send_input({'up': False, 'down': False, 'left': False, 'right': False, 'action': True})

    def _send_input(self, commands):
        if self.sock:
            msg = {'type': 'INPUT', 'player_id': 0, 'commands': commands}
            try:
                self.sock.sendall((json.dumps(msg) + "\n").encode())
            except:
                self.running = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield GameStatus()
        yield Vertical(GameBoard())
        yield Footer()

if __name__ == "__main__":
    app = CreepApp()
    app.run()
