import time
import json
import random
import sys
import traceback

from .parser import CastleParser
from .state import GameState
from .network import NetworkServer

def log_engine(msg):
    with open("engine.log", "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

class GameEngine:
    def __init__(self, castle_file, debug_mode=False):
        log_engine(f"Starting engine with {castle_file} (debug: {debug_mode})")
        self.parser = CastleParser(castle_file)
        self.state = GameState(self.parser)
        self.network = NetworkServer(self)
        self.running = False
        self.ticks_per_second = 50
        self.pending_commands = {} # player_id -> commands
        self.debug_mode = debug_mode
        
        self.room_states = {}
        for rid, room in self.state.rooms.items():
            self.room_states[rid] = {'lightning': {}}
            for obj in room.objects:
                if obj.type in ['lightning_machine', 'lightning_switch']:
                    sid = obj.properties.get('system_id', 0)
                    if sid not in self.room_states[rid]['lightning']:
                        self.room_states[rid]['lightning'][sid] = True 

        start_room_idx = self.parser.data[3]
        start_door_idx = self.parser.data[5] 
        if start_room_idx >= len(self.state.rooms): start_room_idx = 0
            
        start_x, start_y = 20, 192
        room = self.state.rooms.get(start_room_idx)
        if room:
            found = False
            doors_in_room = [obj for obj in room.objects if obj.type == 'door']
            if 0 <= start_door_idx < len(doors_in_room):
                obj = doors_in_room[start_door_idx]
                start_x, start_y, obj.state, found = obj.x + 10, obj.y + 32, 2, True
            if not found:
                for obj in room.objects:
                    if obj.type == 'walkway':
                        start_x, start_y = obj.x + 4, obj.y; break
                    
        self.state.add_player(0, start_room_idx, start_x, start_y)
        p = self.state.players[0]
        p.move_mode = 'walkway'
        p.is_moving = False
        p.is_acting = 0

    def start(self):
        self.running = True
        self.network.start()
        try:
            self._main_loop()
        except Exception:
            err = traceback.format_exc()
            log_engine(f"CRITICAL ENGINE ERROR:\n{err}")
            print(err, file=sys.stderr)

    def _main_loop(self):
        tick_duration = 1.0 / self.ticks_per_second
        while self.running:
            start_time = time.time()
            self._update()
            self._broadcast()
            elapsed = time.time() - start_time
            sleep_time = max(0, tick_duration - elapsed)
            time.sleep(sleep_time)

    def _update(self):
        self.state.current_tick += 1
        
        # 1. Update all static objects first (animations, timers)
        for room in self.state.rooms.values():
            for obj in room.objects:
                obj.update(self, room, self.state.current_tick)

        # 2. Update dynamic autonomous entities (Mummies, Frankies, Proj)
        for m in self.state.mummies: m.update(self, self.state.current_tick)
        for f in self.state.frankies: f.update(self, self.state.current_tick)
        self.state.projectiles = [p for p in self.state.projectiles if p.active]
        for proj in self.state.projectiles: proj.update(self, self.state.current_tick)

        # 3. Process Players via Pipeline
        for player in self.state.players:
            cmds = self.pending_commands.get(player.id, {})
            
            # Initial intent (discrete movement, no acceleration)
            dx, dy = 0, 0
            if cmds.get('left'): dx = -2.0
            elif cmds.get('right'): dx = 2.0
            if cmds.get('up'): dy = -2.0
            elif cmds.get('down'): dy = 2.0

            proposal = {
                'x': player.x + dx,
                'y': player.y + dy,
                'room_id': player.room_id,
                'move_mode': player.move_mode,
                'keys': player.keys[:],
                'is_dead': False,
                'is_moving': (dx != 0 or dy != 0),
                'is_acting': 10 if cmds.get('action') else max(0, player.is_acting - 1),
                'facing_left': (dx < 0) if dx != 0 else player.facing_left,
                'commands': cmds,
                'has_support': False # Must be validated by components
            }

            room = self.state.rooms.get(player.room_id)
            if room:
                # Pipeline through all room objects
                for obj in room.objects:
                    obj.process_proposal(self, room, player, proposal)
                
                # Pipeline through other entities
                for m in self.state.mummies:
                    if hasattr(m, 'process_proposal'): m.process_proposal(self, room, player, proposal)
                for f in self.state.frankies:
                    if hasattr(f, 'process_proposal'): f.process_proposal(self, room, player, proposal)
                for proj in self.state.projectiles:
                    if hasattr(proj, 'process_proposal'): proj.process_proposal(self, room, player, proposal)

            # Resolve Death (Immediate Respawn)
            if proposal['is_dead']:
                player.room_id = 0
                player.x, player.y = 20, 192
                player.move_mode = 'walkway'
                player.is_moving = False
                continue

            # Fall if no support (discrete fall)
            if not proposal['has_support']:
                proposal['y'] += 4
                proposal['move_mode'] = 'walkway'

            # World Boundaries
            proposal['x'] = max(16, min(304, proposal['x']))
            proposal['y'] = max(0, min(200, proposal['y']))

            # Apply final state
            player.apply_proposal(proposal)
        
        self.pending_commands = {}

    def _reset_player(self, player):
        room = self.state.rooms.get(player.room_id)
        if room:
            for obj in room.objects:
                from .components.door import DoorComponent
                if isinstance(obj, DoorComponent) and obj.state == 2:
                    player.x, player.y, player.vx, player.vy, player.move_mode = obj.x + 10, obj.y + 32, 0, 0, 'walkway'
                    break

    def _broadcast(self):
        state_dict = {
            'tick': self.state.current_tick,
            'victory': self.state.victory,
            'debug_mode': self.debug_mode,
            'players': [{'id': p.id, 'x': p.x, 'y': p.y, 'room_id': p.room_id, 'keys': p.keys, 'is_moving': getattr(p, 'is_moving', False), 'is_acting': getattr(p, 'is_acting', 0), 'is_teleporting': getattr(p, 'is_teleporting', 0), 'facing_left': getattr(p, 'facing_left', False)} for p in self.state.players],
            'mummies': [m.serialize() for m in self.state.mummies],
            'frankies': [f.serialize() for f in self.state.frankies],
            'projectiles': [p.serialize() for p in self.state.projectiles],
            'rooms': {rid: {'lightning_systems': {str(k): v for k, v in self.room_states[rid]['lightning'].items()}, 'objects': [o.serialize(self.state.current_tick) for o in r.objects]} for rid, r in self.state.rooms.items()}
        }
        self.network.broadcast_state(state_dict)

    def handle_input(self, player_id, commands):
        if commands.get('restart'):
            self.__init__(self.parser.name)
            return
        if self.state.victory: return
        self.pending_commands[player_id] = commands

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("castle", nargs="?", default="run/data/castles/ZTUTORIAL")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    engine = GameEngine(args.castle, debug_mode=args.debug); engine.start()
