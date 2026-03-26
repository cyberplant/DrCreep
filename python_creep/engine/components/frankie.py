from .base import BaseComponent

class FrankieEntity:
    """
    Frankenstein AI Entity.
    Logic:
    - Tracks player horizontally.
    - Can use ladders and poles if player is at a different Y level.
    - Resets player on contact via process_proposal.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.room_id = data['room_id']
        self.vx = data.get('vx', 0.5)
        self.is_moving = data.get('is_moving', True)
        self.facing_left = data.get('facing_left', False)
        self.move_mode = data.get('move_mode', 'walkway')
        self.type = 'frankie_entity'

    def update(self, engine, tick):
        """Pathfinding logic for Frankenstein's monster."""
        room = engine.state.rooms.get(self.room_id)
        target_p = next((p for p in engine.state.players if p.room_id == self.room_id), None)
        self.is_moving = True
        
        has_support = False
        on_ladder = False
        
        # 1. Check for ladders/poles if at different Y level
        if target_p and abs(target_p.y - self.y) > 8:
            for obj in room.objects:
                if obj.type in ('ladder', 'pole') and abs(self.x - obj.x) < 4:
                    if target_p.y > self.y: self.y += 1
                    else:
                        if obj.type == 'ladder': self.y -= 1
                    on_ladder = True
                    self.move_mode = 'ladder'
                    break

        # 2. Horizontal tracking
        if not on_ladder:
            self.move_mode = 'walkway'
            
            # Check for walkway support
            for obj in room.objects:
                if obj.type == 'walkway':
                    if obj.x - 4 <= self.x <= obj.x + (obj.length * 4) + 4:
                        if obj.y <= self.y <= obj.y + 8:
                            self.y = obj.y # Snap to top
                            has_support = True
                            break
            
            if has_support and target_p:
                dx = target_p.x - self.x
                self.vx = 0.5 if dx > 0 else -0.5
                
                # Check if we can move in vx direction without falling
                next_x = self.x + self.vx * 10 # Look ahead
                can_move = False
                for obj in room.objects:
                    if obj.type == 'walkway' and obj.y == self.y:
                        if obj.x <= next_x <= obj.x + (obj.length * 4):
                            can_move = True
                            break
                if can_move:
                    self.x += self.vx
                else:
                    self.is_moving = False
            
            # World Boundaries
            self.x = max(16, min(304, self.x))
            self.y = min(200, self.y)
            self.facing_left = (self.vx < 0)

    def process_proposal(self, engine, room, current_state, proposal):
        """Check for contact with player and kill if touching."""
        if proposal['room_id'] == self.room_id:
            if abs(proposal['x'] - self.x) < 12 and abs(proposal['y'] - self.y) < 12:
                proposal['is_dead'] = True

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

    def process_proposal(self, engine, room, current_state, proposal):
        """Detect player presence on the same level."""
        if self.state == 0:
            if abs(proposal['y'] - (self.y + 32)) < 24:
                self.state = 1
                engine.state.frankies.append(FrankieEntity({
                    'x': self.x + 12, 
                    'y': self.y + 32, 
                    'room_id': proposal['room_id']
                }))
    
    def get_asset(self, tick):
        return None # Invisible trigger
