
class BaseComponent:
    """
    Base class for all game objects. Defines the standard interface
    for lifecycle, interaction, physics, and serialization.
    """
    def __init__(self, data):
        self.type = data.get('type')
        self.x = data.get('x', 0)
        self.y = data.get('y', 0)
        self.state = 0
        self.timer = 0
        self.max_timer = 0
        self.active = True
        self.properties = data

    def update(self, engine, room, tick):
        """Standard per-tick logic (animations, state changes)."""
        pass

    def on_collide(self, engine, room, entity):
        """Triggered when a mobile entity (Player, Mummy, etc.) enters the object's bounds."""
        pass
        
    def on_interact(self, engine, room, player, commands):
        """Triggered when the player attempts to use or interact with the object."""
        pass

    def process_proposal(self, engine, room, current_state, proposal):
        """
        Allows the component to inspect and modify a proposed state change.
        proposal: { 'x': new_x, 'y': new_y, 'room_id': new_room_id, 'is_dead': bool, ... }
        """
        pass

    def get_asset(self, tick):
        """Returns the current ASCII frame for rendering."""
        return None

    def serialize(self, tick=0):
        """Serializes the component state for network broadcasting."""
        res = {
            'type': self.type,
            'x': self.x,
            'y': self.y,
            'state': self.state,
            'timer': self.timer,
            'max_timer': self.max_timer,
            'properties': self.properties,
            'asset_frame': self.get_asset(tick)
        }
        return res
