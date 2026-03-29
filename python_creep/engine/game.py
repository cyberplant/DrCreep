import time
import json
import random
import sys
import traceback
import os

from .parser import CastleParser
from .state import GameState
from .network import NetworkServer
from rich.console import Console

console = Console()

def log_engine(msg):
    with open("engine.log", "a") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

def log(msg, style="white"):
    log_engine(msg)
    console.print(f"[bold blue]ENGINE[/] [ {time.strftime('%H:%M:%S')} ] {msg}", style=style)

class GameEngine:
    def __init__(self, castle_file, debug_mode=False):
        self.castle_file = castle_file
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
            console.print(err, style="bold red")

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
        self.state.events = []
        
        if getattr(self.state, 'transition', None):
            cmds = self.pending_commands.get(0, {})
            if cmds.get('action'):
                tr = self.state.transition
                p = self.state.players[0]
                p.room_id = tr['to_room']
                p.x, p.y = tr['target_x'], tr['target_y']
                if 'target_door' in tr:
                    tr['target_door'].state = tr['target_state']
                p.is_acting = 0
                self.state.transition = None
            self.pending_commands = {}
            return

        # 1. Update all static objects first (animations, timers)
        for room in self.state.rooms.values():
            for obj in room.objects:
                obj.update(self, room, self.state.current_tick)

        # 2. Projectiles update
        self.state.projectiles = [p for p in self.state.projectiles if p.active]
        for proj in self.state.projectiles: proj.update(self, self.state.current_tick)

        # 3. Unified Entity Pipeline (Players, Mummies, Frankies)
        all_entities = []
        for p in self.state.players: all_entities.append(('player', p))
        for m in self.state.mummies: all_entities.append(('mummy', m))
        for f in self.state.frankies: all_entities.append(('frankie', f))

        for etype, ent in all_entities:
            cmds = {}
            if etype == 'player':
                cmds = self.pending_commands.get(ent.id, {})
                if self.debug_mode and cmds:
                    log(f"Player {ent.id} Input: {cmds}", style="yellow")
            else:
                cmds = ent.update(self, self.state.current_tick)

            # Resolve discrete intent
            dx, dy = 0, 0
            if cmds.get('left'): dx = -1.5
            elif cmds.get('right'): dx = 1.5
            if cmds.get('up'): dy = -1.5
            elif cmds.get('down'): dy = 1.5

            proposal = {
                'x': ent.x + dx,
                'y': ent.y + dy,
                'room_id': ent.room_id,
                'move_mode': ent.move_mode,
                'keys': getattr(ent, 'keys', [])[:],
                'is_dead': False,
                'is_moving': (dx != 0 or dy != 0),
                'is_acting': 10 if cmds.get('action') else max(0, getattr(ent, 'is_acting', 0) - 1),
                'facing_left': (dx < 0) if dx != 0 else ent.facing_left,
                'commands': cmds,
                'has_support': False
            }

            if self.debug_mode and etype == 'player' and (dx != 0 or dy != 0 or cmds.get('action')):
                log(f"  Proposal BEFORE: x={proposal['x']}, y={proposal['y']}, mode={proposal['move_mode']}")

            room = self.state.rooms.get(ent.room_id)
            if room:
                for obj in room.objects:
                    obj.process_proposal(self, room, ent, proposal)
                
                # Cross-entity collision (only if player)
                if etype == 'player':
                    for m in self.state.mummies: m.process_proposal(self, room, ent, proposal)
                    for f in self.state.frankies: f.process_proposal(self, room, ent, proposal)
                    for proj in self.state.projectiles: proj.process_proposal(self, room, ent, proposal)

            # Resolve Physics: STRICT NO GRAVITY
            if proposal['is_dead']:
                if etype == 'player':
                    if self.debug_mode: log(f"  Player {ent.id} DIED", style="bold red")
                    ent.room_id = 0
                    ent.x, ent.y = 20, 192
                    ent.move_mode = 'walkway'
                    ent.is_moving = False
                continue

            # If no support, entity is blocked (revert to old position)
            if not proposal['has_support']:
                proposal['y'] = ent.y
                proposal['x'] = ent.x
                proposal['move_mode'] = ent.move_mode
                proposal['is_moving'] = False

            # World Boundaries: Match Play Area (16 to 176 world units = 0 to 320 pixels)
            proposal['x'] = max(16, min(176, proposal['x']))
            proposal['y'] = max(0, min(200, proposal['y']))

            # Apply final state to entity
            if hasattr(ent, 'apply_proposal'):
                if self.debug_mode and etype == 'player':
                    if ent.x != proposal['x'] or ent.y != proposal['y']:
                        log(f"Player {ent.id} moved: ({ent.x:.1f}, {ent.y:.1f}) -> ({proposal['x']:.1f}, {proposal['y']:.1f})", style="green")
                ent.apply_proposal(proposal)
            else:
                ent.x, ent.y, ent.room_id, ent.move_mode = proposal['x'], proposal['y'], proposal['room_id'], proposal['move_mode']
                ent.facing_left, ent.is_moving = proposal['facing_left'], proposal['is_moving']
                ent.is_acting = proposal['is_acting']
        
        self.pending_commands = {}

    def _broadcast(self):
        # Sanitize transition for broadcast (remove non-serializable objects)
        trans = getattr(self.state, 'transition', None)
        if trans:
            trans = {k: v for k, v in trans.items() if k != 'target_door'}

        state_dict = {
            'tick': self.state.current_tick,
            'events': getattr(self.state, 'events', []),
            'transition': trans,
            'victory': self.state.victory,
            'debug_mode': self.debug_mode,
            'players': [{'id': p.id, 'x': p.x, 'y': p.y, 'room_id': p.room_id, 'keys': p.keys, 'is_moving': getattr(p, 'is_moving', False), 'is_acting': getattr(p, 'is_acting', 0), 'is_teleporting': getattr(p, 'is_teleporting', 0), 'facing_left': getattr(p, 'facing_left', False)} for p in self.state.players],
            'mummies': [m.serialize() for m in self.state.mummies],
            'frankies': [f.serialize() for f in self.state.frankies],
            'projectiles': [p.serialize() for p in self.state.projectiles],
            'rooms': {rid: {
                'color': r.color & 0xF,
                'lightning_systems': {str(k): v for k, v in self.room_states[rid]['lightning'].items()}, 
                'objects': [o.serialize(self.state.current_tick) for o in r.objects]
            } for rid, r in self.state.rooms.items()}
        }
        self.network.broadcast_state(state_dict)

    def handle_input(self, player_id, commands):
        if commands.get('restart'):
            self.__init__(self.castle_file, debug_mode=self.debug_mode)
            return
        
        # Developer Tweaks
        if 'tweak' in commands:
            t = commands['tweak']
            room_id = t.get('room_id')
            obj_idx = t.get('obj_idx')
            attr = t.get('attr')
            delta = t.get('delta', 0)
            
            room = self.state.rooms.get(int(room_id))
            if room and 0 <= obj_idx < len(room.objects):
                obj = room.objects[obj_idx]
                if attr == 'x': obj.x += delta
                elif attr == 'y': obj.y += delta
                log(f"TWEAK: Room {room_id} Obj {obj_idx} {attr} += {delta} (New: {getattr(obj, attr)})", style="bold green")
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
