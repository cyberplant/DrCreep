from .base import BaseComponent

class FrankieEntity:
    """
    Frankenstein AI Entity.
    Logic:
    - Tracks player horizontally.
    - Can use ladders and poles if player is at a different Y level.
    - Resets player on contact.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.room_id = data['room_id']
        self.vx = data.get('vx', 0.5)
        self.is_moving = data.get('is_moving', True)
        self.facing_left = data.get('facing_left', False)
        self.move_mode = data.get('move_mode', 'walkway')

    def update(self, engine, tick):
        """Pathfinding logic for Frankenstein's monster."""
        room = engine.state.rooms.get(self.room_id)
        target_p = next((p for p in engine.state.players if p.room_id == self.room_id), None)
        self.is_moving = True
        
        if target_p:
            dx = target_p.x - self.x
            dy = target_p.y - self.y
            if abs(dy) < 8:
                # Same level: track horizontally
                self.vx = 0.5 if dx > 0 else -0.5
                self.move_mode = 'walkway'
            else:
                # Different level: look for ladders or poles nearby
                on_ladder = False
                for obj in room.objects:
                    if obj.type in ('ladder', 'pole') and abs(self.x - obj.x) < 4:
                        if dy > 0: self.y += 1
                        else:
                            if obj.type == 'ladder': self.y -= 1
                        on_ladder = True
                        self.move_mode = 'ladder'
                        break
                if not on_ladder: 
                    # If no ladder found, keep tracking horizontally
                    self.vx = 0.5 if dx > 0 else -0.5
                    self.move_mode = 'walkway'

        # Horizontal movement and boundary bounce
        if self.move_mode != 'ladder':
            self.x += self.vx
            if self.x < 20: self.vx = 0.5
            if self.x > 180: self.vx = -0.5
            self.facing_left = (self.vx < 0)

        # Contact damage
        for p in engine.state.players:
            if p.room_id == self.room_id and abs(p.x - self.x) < 12 and abs(p.y - self.y) < 12:
                engine._reset_player(p)

    def serialize(self):
        """Entity state serialization."""
        return {
            'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'is_moving': self.is_moving, 'facing_left': self.facing_left
        }

class FrankieComponent(BaseComponent):
    """Trigger component that spawns Frankenstein when player is on the same floor."""
    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=sleeping, 1=released

    def on_collide(self, engine, room, entity):
        """Detect player presence on the same level."""
        if self.state == 0:
            if abs(entity.y - (self.y + 32)) < 24:
                self.state = 1
                engine.state.frankies.append(FrankieEntity({
                    'x': self.x + 12, 
                    'y': self.y + 32, 
                    'room_id': entity.room_id
                }))
