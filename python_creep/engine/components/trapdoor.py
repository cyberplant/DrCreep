from .base import BaseComponent

class TrapdoorComponent(BaseComponent):
    """
    Openable hole in a walkway.
    - state 0: Closed (acts as normal floor).
    - state 1: Open (denies support, blocking movement).
    """
    STATES = {
        0: ["[white]__________[/]"], # Closed
        1: ["[white]          [/]"]  # Open (Hole)
    }
    def __init__(self, data):
        super().__init__(data)
        # Respect map default: data['is_open'] from parser
        self.state = 1 if data.get('is_open') else 0

    def process_proposal(self, engine, room, entity, proposal):
        """Denies support if the entity is over an open trapdoor."""
        if self.state == 1:
            # Check if entity's center is over the hole (within the 8-unit thickness range)
            if self.y <= proposal['y'] <= self.y + 8 and self.x - 4 <= proposal['x'] <= self.x + 12:
                # DENY support. In our pipeline, this blocks movement or causes 'no support' logic.
                proposal['has_support'] = False

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[0])

class TrapdoorSwitchComponent(BaseComponent):
    """Toggles a specific trapdoor in the room on proximity."""
    def process_proposal(self, engine, room, entity, proposal):
        dist_x, dist_y = abs(proposal['x'] - self.x), abs(proposal['y'] - self.y)
        
        # Proximity-based trigger (walk-over)
        if dist_x < 8 and dist_y < 8:
            target_id = self.properties.get('target_idx')
            if 0 <= target_id < len(room.objects):
                t_obj = room.objects[target_id]
                
                # Use a tick-based debounce to prevent rapid flickering
                if not hasattr(self, '_last_trigger_tick') or (engine.state.current_tick - self._last_trigger_tick) > 30:
                    t_obj.state = 1 if t_obj.state == 0 else 0
                    self.state = 1 if self.state == 0 else 0 # Visual state
                    self._last_trigger_tick = engine.state.current_tick

    def get_asset(self, tick):
        # Change appearance based on toggle state
        char = "O" if self.state == 1 else "o"
        col = "yellow" if self.state == 1 else "cyan"
        return [f"[{col}]{char}[/]"]
