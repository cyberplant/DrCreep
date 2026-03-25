from .base import BaseComponent

class LightningMachineComponent(BaseComponent):
    ASSET = ["[cyan](O)[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)

    def on_collide(self, engine, room, entity):
        if engine.room_states[entity.room_id]['lightning'].get(self.system_id):
            if abs(entity.x - (self.x + 2)) < 12 and self.y <= entity.y <= self.y + 160:
                engine._reset_player(entity)

    def get_asset(self, tick):
        return self.ASSET

class LightningSwitchComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)
        self.targets = data.get('targets', [])

    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            # This relies on ForcefieldComponent being available via Duck Typing or import
            if player.room_id == 4:
                self.timer = 8
                for fobj in room.objects:
                    if fobj.type == 'forcefield':
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
