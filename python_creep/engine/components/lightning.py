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
        self.state = 0

    def update(self, engine, room, tick):
        rs = engine.room_states[room.id]['lightning']
        self.state = 1 if rs.get(self.system_id) else 0

    def process_proposal(self, engine, room, current_state, proposal):
        """Handle interaction via pipeline."""
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            cmds = proposal.get('commands', {})
            rs = engine.room_states[proposal['room_id']]['lightning']
            current_on = rs.get(self.system_id, False)
            
            should_toggle = False
            if cmds.get('action'):
                should_toggle = True
            elif cmds.get('up') and not current_on:
                should_toggle = True
            elif cmds.get('down') and current_on:
                should_toggle = True

            if should_toggle:
                # Toggle logic
                # Special logic for tutorial room 4
                if proposal['room_id'] == 4:
                    self.timer = 8
                    for fobj in room.objects:
                        if fobj.type == 'forcefield':
                            fobj.state = 0
                else:
                    sid = self.system_id
                    targets = self.targets
                    rs[sid] = not current_on
                    for tid in targets:
                        if tid != 0xFF: rs[tid] = rs[sid]
                
                # Play sound event
                if not hasattr(engine.state, 'events'): engine.state.events = []
                engine.state.events.append('switch_toggle')

            # Block vertical movement if we are at the switch
            if cmds.get('up') or cmds.get('down'):
                proposal['y'] = current_state.y
                proposal['has_support'] = True

    def get_asset(self, tick):
        return ["[cyan][[yellow]T[/]][/]"]
