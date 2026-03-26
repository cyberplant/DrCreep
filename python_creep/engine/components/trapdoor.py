from .base import BaseComponent

class TrapdoorComponent(BaseComponent):
    """
    Openable hole in a walkway.
    - state 0: Closed (acts as normal floor).
    - state 1: Open (causes entity to fall, handled in filter_movement).
    """
    STATES = {
        0: ["[white]__________[/]"], # Closed
        1: ["[white]          [/]"]  # Open (Hole)
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1 if data.get('is_open') else 0

    def filter_movement(self, engine, room, entity, dx, dy):
        """Signals a fall if the entity is over an open trapdoor."""
        if self.state == 1:
            # Check overlap between entity and the hole (using 8-unit thickness range)
            if self.y <= (entity.y - 32) <= self.y + 8 and self.x - 4 <= entity.x <= self.x + 12:
                return dx, dy, True # STOP/FALL
        return dx, dy, False

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[0])

class TrapdoorSwitchComponent(BaseComponent):
    """Toggles a specific trapdoor in the room."""
    def process_proposal(self, engine, room, current_state, proposal):
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            if proposal.get('commands', {}).get('action') and proposal.get('is_acting') == 10:
                target_id = self.properties.get('target_idx')
                if 0 <= target_id < len(room.objects):
                    t_obj = room.objects[target_id]
                    t_obj.state = 1 if t_obj.state == 0 else 0
    def get_asset(self, tick):
        return ["[cyan]o[/]"]
