from .base import BaseComponent

class MummyEntity:
    """
    Mummy AI Entity.
    Logic:
    - Only moves if player is in the same room and at similar Y level.
    - Moves slower than the player (every 3 ticks).
    - Resets player on contact via process_proposal.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.room_id = data['room_id']
        self.is_moving = data.get('is_moving', False)
        self.facing_left = data.get('facing_left', False)
        self.type = 'mummy_entity'

    def update(self, engine, tick):
        """Horizontal tracking of the player with walkway support."""
        room = engine.state.rooms.get(self.room_id)
        target_p = next((p for p in engine.state.players if p.room_id == self.room_id), None)
        self.is_moving = False
        
        has_support = False
        for obj in room.objects:
            if obj.type == 'walkway':
                if obj.x - 4 <= self.x <= obj.x + (obj.length * 4) + 4:
                    if obj.y <= self.y <= obj.y + 8:
                        self.y = obj.y
                        has_support = True
                        break
        
        if has_support and target_p and abs(target_p.y - self.y) < 16:
            if tick % 3 == 0:
                self.is_moving = True
                vx = 1 if self.x < target_p.x else -1
                
                # Check walkway ahead
                next_x = self.x + vx * 8
                can_move = False
                for obj in room.objects:
                    if obj.type == 'walkway' and obj.y == self.y:
                        if obj.x <= next_x <= obj.x + (obj.length * 4):
                            can_move = True
                            break
                
                if can_move:
                    self.x += vx
                    self.facing_left = (vx < 0)
                else:
                    self.is_moving = False

    def process_proposal(self, engine, room, current_state, proposal):
        """Check for contact with player and kill if touching."""
        if proposal['room_id'] == self.room_id:
            if abs(proposal['x'] - self.x) < 12 and abs(proposal['y'] - self.y) < 12:
                proposal['is_dead'] = True

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

    def process_proposal(self, engine, room, current_state, proposal):
        """Detect player proximity and trigger spawn."""
        if self.state == 0:
            if abs(proposal['x'] - self.x) < 16 and abs((proposal['y'] - 16) - self.y) < 32:
                self.state = 1
                engine.state.mummies.append(MummyEntity({
                    'x': self.properties['tomb_x'] + 12, 
                    'y': self.properties['tomb_y'] + 24, 
                    'room_id': proposal['room_id']
                }))

    def get_asset(self, tick):
        return ["[white]M[/]"]

class MummyTombComponent(BaseComponent):
    """Visual placeholder for a mummy's tomb."""
    def process_proposal(self, engine, room, current_state, proposal):
        pass

    def get_asset(self, tick):
        return ["[red]#####[/]", "[red]#####[/]", "[red]#####[/]"]
