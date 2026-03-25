from .base import BaseComponent
from .environment import DoorComponent, TrapdoorComponent, ConveyorComponent
from .hazards import ForcefieldComponent, RaygunComponent

class DoorbellComponent(BaseComponent):
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_door_idx')
            room_doors = [obj for obj in room.objects if isinstance(obj, DoorComponent)]
            if 0 <= target_id < len(room_doors):
                if room_doors[target_id].state == 0:
                    room_doors[target_id].state = 1
    def get_asset(self, tick):
        return ["[white]●[/]"]

class LightningSwitchComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)
        self.targets = data.get('targets', [])

    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            if player.room_id == 4:
                self.timer = 8
                for fobj in room.objects:
                    if isinstance(fobj, ForcefieldComponent):
                        fobj.state = 0
            else:
                sid = self.system_id
                targets = self.targets
                rs = engine.room_states[player.room_id]['lightning']
                if sid not in rs: rs[sid] = True
                rs[sid] = not rs[sid]
                for tid in targets:
                    if tid != 0xFF: rs[tid] = rs[sid]
    def get_asset(self, tick):
        return ["[cyan][[yellow]T[/]][/]"]

class ForcefieldSwitchComponent(BaseComponent):
    def update(self, engine, room, tick):
        if self.timer > 0:
            if tick % engine.ticks_per_second == 0:
                self.timer -= 1
                if self.timer == 0:
                    for obj in room.objects:
                        if isinstance(obj, ForcefieldComponent):
                            obj.state = 1

    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            self.timer = 8
            for fobj in room.objects:
                if isinstance(fobj, ForcefieldComponent):
                    fobj.state = 0
    def get_asset(self, tick):
        return ["[cyan]S[/]"]

class TrapdoorSwitchComponent(BaseComponent):
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_idx')
            if 0 <= target_id < len(room.objects):
                t_obj = room.objects[target_id]
                t_obj.state = 1 if t_obj.state == 0 else 0
    def get_asset(self, tick):
        return ["[cyan]o[/]"]

class ConveyorSwitchComponent(BaseComponent):
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_idx')
            if 0 <= target_id < len(room.objects):
                c_obj = room.objects[target_id]
                states = [0, 1, 2, 1]
                cur_idx = states.index(c_obj.state) if c_obj.state in states else 1
                c_obj.state = states[(cur_idx + 1) % 4]
    def get_asset(self, tick):
        return ["[cyan]o[/]"]

class RaygunSwitchComponent(BaseComponent):
    def on_interact(self, engine, room, player, commands):
        for rgun in room.objects:
            if isinstance(rgun, RaygunComponent):
                if commands.get('up'): rgun.y -= 2; return
                if commands.get('down'): rgun.y += 2; return
                if commands.get('action'):
                    if rgun.timer == 0:
                        rgun.timer = 100
                        engine.state.projectiles.append({'x': rgun.x + 16, 'y': rgun.y, 'vx': 3.0, 'room_id': player.room_id})
                    return
    def get_asset(self, tick):
        return [
            " [cyan]^[/] ",
            " [cyan]O[/] ",
            " [cyan]v[/] "
        ]
