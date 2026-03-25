from .base import BaseComponent
from .environment import DoorComponent

class TeleportComponent(BaseComponent):
    TEMPLATE = [
        "[obj_color]======[/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]"
    ]
    def __init__(self, data):
        super().__init__(data)
        self.state = data.get('target', 0)

    def on_interact(self, engine, room, player, commands):
        target_colors = sorted(list(set(o.properties['color'] for o in room.objects if isinstance(o, TeleportTargetComponent))))
        if not target_colors: target_colors = [0]
        cur_idx = target_colors.index(self.state) if self.state in target_colors else 0
        if commands.get('up'):
            self.state = target_colors[(cur_idx - 1) % len(target_colors)]
            return
        if commands.get('down'):
            self.state = target_colors[(cur_idx + 1) % len(target_colors)]
            return
        
        if commands.get('action'):
            tc = self.state
            for rid, rstate in engine.state.rooms.items():
                for tobj in rstate.objects:
                    if isinstance(tobj, TeleportTargetComponent) and tobj.properties['color'] == tc:
                        player.is_teleporting = 20
                        player.target_room_id = rid
                        player.target_x, player.target_y = tobj.x, tobj.y + 32
                        return

    def get_asset(self, tick):
        return self.TEMPLATE

class TeleportTargetComponent(BaseComponent):
    ASSET = ["[obj_color]●[/]"]
    def get_asset(self, tick):
        return self.ASSET

class KeyComponent(BaseComponent):
    ASSET = ["[obj_color]k[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            player.keys.append(self.properties['color'])
            room.objects.remove(self)
    def get_asset(self, tick):
        return self.ASSET

class LockComponent(BaseComponent):
    ASSET = ["[obj_color]X[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            color = self.properties.get('color', 0)
            if color in player.keys:
                target_id = self.properties.get('target_door_idx')
                room_doors = [obj for obj in room.objects if isinstance(obj, DoorComponent)]
                if 0 <= target_id < len(room_doors):
                    if room_doors[target_id].state == 0:
                        room_doors[target_id].state = 1
                        player.keys.remove(color)
    def get_asset(self, tick):
        return self.ASSET

class TextComponent(BaseComponent):
    def get_asset(self, tick):
        color_map = {0x1D: "white", 0x1E: "yellow", 0x1F: "cyan", 0x20: "green"}
        color = color_map.get(self.properties.get('color'), "white")
        return [f"[{color}]{self.properties.get('text', '')}[/]"]
