from .base import BaseComponent

class TeleportTargetComponent(BaseComponent):
    ASSET = ["[obj_color]●[/]"]
    def get_asset(self, tick):
        return self.ASSET

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
        target_colors = sorted(list(set(o.properties['color'] for o in room.objects if o.type == 'teleport_target')))
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
                    if tobj.type == 'teleport_target' and tobj.properties['color'] == tc:
                        player.is_teleporting = 20
                        player.target_room_id = rid
                        player.target_x, player.target_y = tobj.x, tobj.y + 32
                        return

    def get_asset(self, tick):
        return self.TEMPLATE
