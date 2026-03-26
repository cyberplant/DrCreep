from .base import BaseComponent

class TeleportTargetComponent(BaseComponent):
    """Visual destination point for a teleporter."""
    ASSET = ["[obj_color]●[/]"]
    def get_asset(self, tick):
        return self.ASSET

class TeleportComponent(BaseComponent):
    """
    Teleportation Cabin.
    """
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
        self.state = data.get('color', 1)

    def process_proposal(self, engine, room, current_state, proposal):
        """Handle interaction via pipeline."""
        dist_x, dist_y = abs(proposal['x'] - self.x), abs(proposal['y'] - (self.y + 32))
        if dist_x < 16 and dist_y < 48:
            cmds = proposal.get('commands', {})
            
            # 1. Target cycling
            target_colors = sorted(list(set(o.properties['color'] for o in room.objects if o.type == 'teleport_target')))
            if not target_colors: target_colors = [self.state]
            
            if cmds.get('up'):
                cur_idx = target_colors.index(self.state) if self.state in target_colors else 0
                self.state = target_colors[(cur_idx - 1) % len(target_colors)]
            elif cmds.get('down'):
                cur_idx = target_colors.index(self.state) if self.state in target_colors else 0
                self.state = target_colors[(cur_idx + 1) % len(target_colors)]
            
            # 2. Teleport trigger
            if cmds.get('action'):
                tc = self.state
                for rid, rstate in engine.state.rooms.items():
                    for tobj in rstate.objects:
                        if tobj.type == 'teleport_target' and tobj.properties['color'] == tc:
                            proposal['room_id'] = rid
                            proposal['x'] = tobj.x
                            proposal['y'] = tobj.y + 32
                            proposal['has_support'] = True
                            return

    def get_asset(self, tick):
        return self.TEMPLATE
