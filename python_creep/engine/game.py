import time
import json
import random
from .parser import CastleParser
from .state import GameState
from .network import NetworkServer

class GameEngine:
    def __init__(self, castle_file):
        self.parser = CastleParser(castle_file)
        self.state = GameState(self.parser)
        self.network = NetworkServer(self)
        self.running = False
        self.ticks_per_second = 50
        
        # Room-specific global states: rid -> {system_id: bool}
        self.room_states = {}

        for rid, room in self.state.rooms.items():
            self.room_states[rid] = {}
            for obj in room.objects:
                if obj.type == 'door':
                    obj.state = 0
                elif obj.type == 'lightning_machine':
                    sys_id = obj.properties.get('system_id', 0)
                    self.room_states[rid][sys_id] = True # Default ON

        start_room_idx = self.parser.data[3]
        start_door_id = self.parser.data[5] 
        if start_room_idx >= len(self.state.rooms):
            start_room_idx = 0
            
        start_x, start_y = 20, 100
        room = self.state.rooms.get(start_room_idx)
        if room:
            found = False
            doors_in_room = [obj for obj in room.objects if obj.type == 'door']
            if 0 <= start_door_id < len(doors_in_room):
                obj = doors_in_room[start_door_id]
                start_x = obj.x + 10
                start_y = obj.y + 32
                obj.state = 2
                found = True
            if not found:
                for obj in room.objects:
                    if obj.type == 'walkway':
                        start_x = obj.x + 4
                        start_y = obj.y
                        break
                    
        p = self.state.add_player(0, start_room_idx, start_x, start_y)
        p.move_mode = 'walkway'

    def start(self):
        self.running = True
        self.network.start()
        self._main_loop()

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
        for room in self.state.rooms.values():
            for obj in room.objects:
                if obj.type == 'door' and 0 < obj.state < 2:
                    if self.state.current_tick % 5 == 0:
                        obj.state += 1

        for player in self.state.players:
            room = self.state.rooms.get(player.room_id)
            if not room: continue

            # Lightning collision check
            room_sys_states = self.room_states.get(player.room_id, {})
            for obj in room.objects:
                if obj.type == 'lightning_machine':
                    sys_id = obj.properties.get('system_id', 0)
                    if room_sys_states.get(sys_id):
                        # Doubled ray height: ~80 px (10 chars)
                        lx_start, lx_end = obj.x - 4, obj.x + 8
                        ly_start, ly_end = obj.y, obj.y + 80
                        
                        py_top = player.y - 32
                        py_bottom = player.y
                        
                        if lx_start <= player.x <= lx_end and ly_start <= py_bottom and py_top <= ly_end:
                            print(f"[{self.state.castle_name}] Player {player.id} disintegrated in Room {player.room_id}!")
                            self._reset_player(player)
                            return

            support = None
            if player.move_mode == 'walkway':
                for obj in room.objects:
                    if obj.type == 'walkway':
                        start_x = obj.x
                        end_x = obj.x + (obj.properties['length'] * 4)
                        if start_x <= player.x <= end_x and abs(player.y - obj.y) < 4:
                            support = obj
                            break
            else:
                for obj in room.objects:
                    if obj.type in ['ladder', 'pole']:
                        start_y = obj.y
                        end_y = obj.y + (obj.properties['length'] * 8)
                        if start_y <= player.y <= end_y and abs(player.x - obj.x) < 4:
                            support = obj
                            break

            if support:
                if player.move_mode == 'walkway':
                    player.y = support.y
                    next_x = player.x + player.vx
                    min_scr_x, max_scr_x = 16, 168
                    start_x = max(min_scr_x, support.x)
                    end_x = min(max_scr_x, support.x + (support.properties['length'] * 4))
                    player.x = max(start_x, min(next_x, end_x))
                    
                    if player.vy < -0.1 and (self.state.current_tick - player.last_transition_tick) > 50:
                        for obj in room.objects:
                            if obj.type == 'door' and obj.state == 2:
                                if abs(player.x - (obj.x + 10)) < 12 and abs(player.y - (obj.y + 32)) < 8:
                                    target_room_id = obj.properties['link_room']
                                    target_door_idx = obj.properties['link_door']
                                    target_room = self.state.rooms.get(target_room_id)
                                    if target_room:
                                        target_doors = [t for t in target_room.objects if t.type == 'door']
                                        if 0 <= target_door_idx < len(target_doors):
                                            tobj = target_doors[target_door_idx]
                                            player.room_id = target_room_id
                                            player.x = tobj.x + 10
                                            player.y = tobj.y + 32
                                            tobj.state = 2
                                            player.last_transition_tick = self.state.current_tick
                                            return
                                    break
                    
                    if abs(player.vy) > 0.1:
                        for obj in room.objects:
                            if obj.type in ['ladder', 'pole']:
                                if abs(player.x - obj.x) < 4:
                                    if player.vy > 0 and abs(player.y - (obj.y + obj.properties['length']*8)) < 4:
                                        continue
                                    if obj.type == 'pole' and player.vy < 0:
                                        continue
                                    player.move_mode = 'ladder'
                                    player.x = obj.x
                                    break
                else:
                    player.x = support.x
                    next_vy = player.vy
                    if support.type == 'pole' and next_vy < 0: next_vy = 0
                    next_y = player.y + next_vy
                    start_y, end_y = max(0, support.y), min(192, support.y + (support.properties['length'] * 8))
                    player.y = max(start_y, min(next_y, end_y))
                    
                    if abs(player.vx) > 0.1:
                        for obj in room.objects:
                            if obj.type == 'walkway':
                                if abs(player.y - obj.y) < 4:
                                    player.move_mode = 'walkway'
                                    player.y = obj.y
                                    break
            
            player.vx *= 0.5
            player.vy *= 0.5

    def _reset_player(self, player):
        room = self.state.rooms.get(player.room_id)
        if room:
            # Return to the door player most likely came from (open one)
            for obj in room.objects:
                if obj.type == 'door' and obj.state == 2:
                    player.x = obj.x + 10
                    player.y = obj.y + 32
                    player.vx = 0
                    player.vy = 0
                    player.move_mode = 'walkway'
                    break

    def _broadcast(self):
        state_dict = {
            'tick': self.state.current_tick,
            'players': [{'id': p.id, 'x': p.x, 'y': p.y, 'room_id': p.room_id} for p in self.state.players],
            'rooms': {
                rid: {
                    'lightning_systems': self.room_states[rid],
                    'objects': [{'type': o.type, 'x': o.x, 'y': o.y, 'state': o.state, 'properties': o.properties} for o in r.objects]
                } for rid, r in self.state.rooms.items()
            }
        }
        self.network.broadcast_state(state_dict)

    def handle_input(self, player_id, commands):
        p = self.state.players[player_id]
        speed = 2.0
        if commands.get('left'): p.vx = -speed
        if commands.get('right'): p.vx = speed
        if commands.get('up'): p.vy = -speed
        if commands.get('down'): p.vy = speed
        
        if commands.get('action'):
            action_found = False
            room = self.state.rooms.get(p.room_id)
            print(f"[{self.state.castle_name}] Room {p.room_id} | Player {player_id} pressed button at {p.x:.1f},{p.y:.1f}")
            doors_in_room = [obj for obj in room.objects if obj.type == 'door']
            for obj in room.objects:
                if obj.type == 'doorbell':
                    dist_x, dist_y = abs(p.x - obj.x), abs((p.y - 16) - obj.y)
                    if dist_x < 12 and dist_y < 24:
                        target_id = obj.properties.get('target_door_idx')
                        if 0 <= target_id < len(doors_in_room):
                            dobj = doors_in_room[target_id]
                            if dobj.state == 0: dobj.state = 1
                            action_found = True
                elif obj.type == 'lightning_switch':
                    dist_x, dist_y = abs(p.x - obj.x), abs((p.y - 16) - obj.y)
                    if dist_x < 12 and dist_y < 24:
                        sys_id = obj.properties.get('system_id', 0)
                        room_sys = self.room_states[p.room_id]
                        if sys_id not in room_sys and 0 in room_sys:
                            sys_id = 0 # Fallback to 0 if 1-based index not found
                        
                        if sys_id in room_sys:
                            room_sys[sys_id] = not room_sys[sys_id]
                            print(f"    Action: lightning system {sys_id} toggled to {room_sys[sys_id]}")
                            action_found = True
            if not action_found:
                print(f"    Action: none")

if __name__ == "__main__":
    import sys
    castle = sys.argv[1] if len(sys.argv) > 1 else "run/data/castles/ZTUTORIAL"
    engine = GameEngine(castle)
    engine.start()
