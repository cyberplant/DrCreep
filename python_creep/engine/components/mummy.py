from .base import BaseComponent

class MummyEntity:
    """
    Mummy AI Entity.
    Logic:
    - Only moves if player is in the same room and at similar Y level.
    - Moves slower than the player (every 3 ticks).
    - Resets player on contact.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.room_id = data['room_id']
        self.is_moving = data.get('is_moving', False)
        self.facing_left = data.get('facing_left', False)

    def update(self, engine, tick):
        """Simple horizontal tracking of the player."""
        target_p = next((p for p in engine.state.players if p.room_id == self.room_id), None)
        self.is_moving = False
        if target_p and abs(target_p.y - self.y) < 16:
            if tick % 3 == 0:
                self.is_moving = True
                if self.x < target_p.x: 
                    self.x += 1
                    self.facing_left = False
                elif self.x > target_p.x: 
                    self.x -= 1
                    self.facing_left = True
        
        # Damage check
        for p in engine.state.players:
            if p.room_id == self.room_id and abs(p.x - self.x) < 12 and abs(p.y - self.y) < 12:
                engine._reset_player(p)

    def serialize(self):
        """Standard serialization for entity broadcast."""
        return {
            'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'is_moving': self.is_moving, 'facing_left': self.facing_left
        }

class MummyReleaseComponent(BaseComponent):
    """Component that spawns a Mummy when the player walks nearby."""
    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=sleeping, 1=released

    def on_collide(self, engine, room, entity):
        """Detect player proximity and trigger spawn."""
        if self.state == 0:
            if abs(entity.x - self.x) < 16 and abs((entity.y - 16) - self.y) < 32:
                self.state = 1
                engine.state.mummies.append(MummyEntity({
                    'x': self.properties['tomb_x'] + 12, 
                    'y': self.properties['tomb_y'] + 32, 
                    'room_id': entity.room_id
                }))

    def get_asset(self, tick):
        return ["[white]M[/]"]

class MummyTombComponent(BaseComponent):
    """Visual placeholder for a mummy's tomb."""
    def get_asset(self, tick):
        return ["[red]#####[/]", "[red]#####[/]", "[red]#####[/]"]
