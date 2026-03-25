
class BaseComponent:
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
        """Called every game tick. Handle movement, timers, AI here."""
        pass

    def on_collide(self, engine, room, entity):
        """Triggered when an entity (Player, Frankie, Mummy) overlaps the bounding box."""
        pass
        
    def on_interact(self, engine, room, player, commands):
        """Triggered when a player interacts with the object."""
        pass

    def filter_movement(self, engine, room, entity, dx, dy):
        """Allow components to modify or block movement intent."""
        return dx, dy, False # Returns modified dx, dy and a 'stop' flag

    def get_asset(self, tick):
        return None

    def serialize(self, tick=0):
        """Return a dictionary of state for network broadcast."""
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
