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

    def on_collide(self, engine, room, entity):
        """Reset player if they walk into an active lightning bolt."""
        if engine.room_states[entity.room_id]['lightning'].get(self.system_id):
            # Check for vertical beam contact
            if abs(entity.x - (self.x + 2)) < 12 and self.y <= entity.y <= self.y + 160:
                engine._reset_player(entity)

    def get_asset(self, tick):
        return self.ASSET

class LightningSwitchComponent(BaseComponent):
    """
    Toggles lightning systems in the room.
    - sid: ID of the system it controls directly.
    - targets: IDs of other systems that will match the new state.
    """
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)
        self.targets = data.get('targets', [])

    def on_interact(self, engine, room, player, commands):
        """Toggle system state on action button press."""
        if commands.get('action'):
            if player.room_id == 4: # Special logic for tutorial room 4
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
                # Sync target systems
                for tid in targets:
                    if tid != 0xFF: rs[tid] = rs[sid]
    def get_asset(self, tick):
        return ["[cyan][[yellow]T[/]][/]"]
