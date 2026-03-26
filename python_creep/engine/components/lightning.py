from .base import BaseComponent

class LightningMachineComponent(BaseComponent):
    """
    Lightning hazard that kills player on contact.
    - Controlled by lightning switches.
    - Can only kill if the system state is ON.
    """
    ASSET = ["[cyan](O)[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)

    def process_proposal(self, engine, room, current_state, proposal):
        """Check for contact with an active lightning bolt."""
        if engine.room_states[proposal['room_id']]['lightning'].get(self.system_id):
            # Check for vertical beam contact: same X, within Y range
            if abs(proposal['x'] - (self.x + 2)) < 12 and self.y <= proposal['y'] <= self.y + 160:
                proposal['is_dead'] = True

    def get_asset(self, tick):
        return self.ASSET

class LightningSwitchComponent(BaseComponent):
    """
    Toggles lightning systems in the room.
    """
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)
        self.targets = data.get('targets', [])

    def process_proposal(self, engine, room, current_state, proposal):
        """Handle interaction via pipeline."""
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            if proposal.get('commands', {}).get('action'):
                # Special logic for tutorial room 4
                if proposal['room_id'] == 4:
                    self.timer = 8
                    for fobj in room.objects:
                        if fobj.type == 'forcefield':
                            fobj.state = 0
                else:
                    sid = self.system_id
                    targets = self.targets
                    rs = engine.room_states[proposal['room_id']]['lightning']
                    if sid not in rs: rs[sid] = True
                    rs[sid] = not rs[sid]
                    for tid in targets:
                        if tid != 0xFF: rs[tid] = rs[sid]

    def get_asset(self, tick):
        return ["[cyan][[yellow]T[/]][/]"]
