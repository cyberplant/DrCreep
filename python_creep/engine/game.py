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
    def __init__(self, castle_file):
        log_engine(f"Starting engine with {castle_file}")
        self.parser = CastleParser(castle_file)
        self.state = GameState(self.parser)
        self.network = NetworkServer(self)
        self.running = False
        self.ticks_per_second = 50
        
        self.room_states = {}
        for rid, room in self.state.rooms.items():
            self.room_states[rid] = {'lightning': {}}
            for obj in room.objects:
                if obj.type == 'door':
                    obj.state = 0
                elif obj.type in ['lightning_machine', 'lightning_switch']:
                    sid = obj.properties.get('system_id', 0)
                    if sid not in self.room_states[rid]['lightning']:
                        self.room_states[rid]['lightning'][sid] = True 
                elif obj.type == 'forcefield':
                    obj.state = 1
                elif obj.type == 'mummy_release':
                    obj.state = 0

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
        for room in self.state.rooms.values():
            for obj in room.objects:
                if obj.type == 'door' and 0 < obj.state < 2:
                    if self.state.current_tick % 10 == 0: obj.state += 1
                if obj.type == 'forcefield_switch' and obj.timer > 0:
                    if self.state.current_tick % self.ticks_per_second == 0:
                        obj.timer -= 1
                        if obj.timer == 0:
                            for fobj in room.objects:
                                if fobj.type == 'forcefield': fobj.state = 1

        for m in self.state.mummies:
            target_p = next((p for p in self.state.players if p.room_id == m['room_id']), None)
            if target_p:
                if self.state.current_tick % 3 == 0:
                    if m['x'] < target_p.x: m['x'] += 1
                    elif m['x'] > target_p.x: m['x'] -= 1
            for p in self.state.players:
                if p.room_id == m['room_id'] and abs(p.x - m['x']) < 8 and abs(p.y - m['y']) < 8:
                    self._reset_player(p)

        for player in self.state.players:
            room = self.state.rooms.get(player.room_id)
            if not room: continue
            
            if player.is_acting > 0: player.is_acting -= 1

            room_lightning = self.room_states[player.room_id]['lightning']
            for obj in room.objects:
                if obj.type == 'lightning_machine':
                    if room_lightning.get(obj.properties.get('system_id', 0)):
                        if abs(player.x - (obj.x + 2)) < 12 and obj.y <= player.y <= obj.y + 160:
                            self._reset_player(player); return
                elif obj.type == 'mummy_release' and obj.state == 0:
                    if abs(player.x - obj.x) < 12 and abs(player.y - (obj.y - 8)) < 16:
                        obj.state = 1
                        self.state.mummies.append({'x': obj.properties['tomb_x'] + 12, 'y': obj.properties['tomb_y'] + 32, 'room_id': player.room_id})

            support = None
            if player.move_mode == 'walkway':
                for obj in room.objects:
                    if obj.type == 'walkway':
                        start_x, end_x = obj.x, obj.x + (obj.properties['length'] * 4)
                        if start_x <= player.x <= end_x and abs(player.y - obj.y) < 4:
                            support = obj; break
            else:
                for obj in room.objects:
                    if obj.type in ['ladder', 'pole']:
                        start_y = obj.y
                        max_w_y = start_y
                        for w in room.objects:
                            if w.type == 'walkway' and w.x <= obj.x <= w.x + w.properties.get('length', 0) * 4:
                                if w.y >= start_y and w.y > max_w_y:
                                    max_w_y = w.y
                        end_y = max_w_y if max_w_y > start_y else start_y + (obj.properties['length'] * 8)
                        
                        if start_y <= player.y <= end_y and abs(player.x - obj.x) < 4:
                            support = obj; break

            player.is_moving = (abs(player.vx) > 0.1 or abs(player.vy) > 0.1)

            if support:
                if player.move_mode == 'walkway':
                    player.y = support.y
                    next_x = player.x + player.vx
                    min_scr_x, max_scr_x = 16, 172
                    for obj in room.objects:
                        if obj.type == 'forcefield' and obj.state == 1:
                            if abs(player.y - obj.y) < 24:
                                if player.x < obj.x and next_x >= obj.x - 4: next_x = obj.x - 4
                                elif player.x > obj.x and next_x <= obj.x + 4: next_x = obj.x + 4
                    player.x = max(max(min_scr_x, support.x), min(min(max_scr_x, support.x + (support.properties['length'] * 4)), next_x))
                    
                    if player.vy < -0.1 and (self.state.current_tick - player.last_transition_tick) > 50:
                        for obj in room.objects:
                            if obj.type == 'door' and obj.state == 2:
                                if abs(player.x - (obj.x + 10)) < 12 and abs(player.y - (obj.y + 32)) < 8:
                                    target_room_id, target_door_idx = obj.properties['link_room'], obj.properties['link_door']
                                    target_room = self.state.rooms.get(target_room_id)
                                    if target_room:
                                        target_doors = [t for t in target_room.objects if t.type == 'door']
                                        if 0 <= target_door_idx < len(target_doors):
                                            tobj = target_doors[target_door_idx]
                                            player.room_id, player.x, player.y = target_room_id, tobj.x + 10, tobj.y + 32
                                            tobj.state, player.last_transition_tick = 2, self.state.current_tick
                                            return
                    if abs(player.vy) > 0.1:
                        for obj in room.objects:
                            if obj.type in ['ladder', 'pole'] and abs(player.x - obj.x) < 4:
                                if player.vy > 0 and abs(player.y - (obj.y + obj.properties['length']*8)) < 4: continue
                                if obj.type == 'pole' and player.vy < 0: continue
                                player.move_mode, player.x = 'ladder', obj.x; break
                else:
                    player.x = support.x
                    next_vy = player.vy
                    if support.type == 'pole' and next_vy < 0: next_vy = 0
                    
                    max_w_y = support.y
                    for w in room.objects:
                        if w.type == 'walkway' and w.x <= support.x <= w.x + w.properties.get('length', 0) * 4:
                            if w.y >= support.y and w.y > max_w_y:
                                max_w_y = w.y
                    end_y = max_w_y if max_w_y > support.y else support.y + (support.properties['length'] * 8)
                    
                    player.y = max(support.y, min(end_y, player.y + next_vy))
                    if abs(player.vx) > 0.1:
                        for obj in room.objects:
                            if obj.type == 'walkway' and abs(player.y - obj.y) < 4:
                                player.move_mode, player.y = 'walkway', obj.y; break
            
            player.vx *= 0.5
            player.vy *= 0.5

    def _reset_player(self, player):
        room = self.state.rooms.get(player.room_id)
        if room:
            for obj in room.objects:
                if obj.type == 'door' and obj.state == 2:
                    player.x, player.y, player.vx, player.vy, player.move_mode = obj.x + 10, obj.y + 32, 0, 0, 'walkway'
                    break

    def _broadcast(self):
        state_dict = {
            'tick': self.state.current_tick,
            'players': [{'id': p.id, 'x': p.x, 'y': p.y, 'room_id': p.room_id, 'keys': p.keys, 'is_moving': getattr(p, 'is_moving', False), 'is_acting': getattr(p, 'is_acting', 0)} for p in self.state.players],
            'mummies': [{'x': m['x'], 'y': m['y'], 'room_id': m['room_id']} for m in self.state.mummies],
            'rooms': {rid: {'lightning_systems': {str(k): v for k, v in self.room_states[rid]['lightning'].items()}, 'objects': [{'type': o.type, 'x': o.x, 'y': o.y, 'state': o.state, 'timer': o.timer, 'max_timer': o.max_timer, 'properties': o.properties} for o in r.objects]} for rid, r in self.state.rooms.items()}
        }
        self.network.broadcast_state(state_dict)

    def handle_input(self, player_id, commands):
        p = self.state.players[player_id]
        if commands.get('left'): p.vx = -2.0
        if commands.get('right'): p.vx = 2.0
        if commands.get('up'): p.vy = -2.0
        if commands.get('down'): p.vy = 2.0
        room = self.state.rooms.get(p.room_id)
        if not room: return
        if commands.get('action'):
            p.is_acting = 10
            room_doors = [obj for obj in room.objects if obj.type == 'door']
            for obj in room.objects:
                dist_x, dist_y = abs(p.x - obj.x), abs((p.y - 16) - obj.y)
                if dist_x < 16 and dist_y < 32:
                    if obj.type == 'doorbell':
                        target_id = obj.properties.get('target_door_idx')
                        if 0 <= target_id < len(room_doors):
                            if room_doors[target_id].state == 0: room_doors[target_id].state = 1
                    elif obj.type in ['lightning_switch', 'forcefield_switch']:
                        if obj.type == 'forcefield_switch' or p.room_id == 4:
                            obj.timer = 8
                            for fobj in room.objects:
                                if fobj.type == 'forcefield': fobj.state = 0
                        else:
                            sid = obj.properties.get('system_id', 0)
                            targets = obj.properties.get('targets', [])
                            rs = self.room_states[p.room_id]['lightning']
                            if sid not in rs: rs[sid] = True
                            rs[sid] = not rs[sid]
                            for tid in targets:
                                if tid != 0xFF: rs[tid] = rs[sid]
                    elif obj.type == 'key':
                        p.keys.append(obj.properties['color']); room.objects.remove(obj)
                    elif obj.type == 'lock':
                        color = obj.properties.get('color', 0)
                        if color in p.keys:
                            target_id = obj.properties.get('target_door_idx')
                            if 0 <= target_id < len(room_doors):
                                if room_doors[target_id].state == 0:
                                    room_doors[target_id].state = 1; p.keys.remove(color); break
                    elif obj.type == 'teleport':
                        tc = obj.state
                        for rid, rstate in self.state.rooms.items():
                            for tobj in rstate.objects:
                                if tobj.type == 'teleport_target' and tobj.properties['color'] == tc:
                                    p.room_id, p.x, p.y = rid, tobj.x, tobj.y; return

if __name__ == "__main__":
    import sys
    castle = sys.argv[1] if len(sys.argv) > 1 else "run/data/castles/ZTUTORIAL"
    engine = GameEngine(castle); engine.start()
