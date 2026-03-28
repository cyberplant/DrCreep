from .base import BaseComponent

class FrankieEntity:
    """
    Frankenstein AI Entity.
    Logic:
    - Tracks player horizontally.
    - Can use ladders and poles if player is at a different Y level.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.room_id = data['room_id']
        self.is_moving = False
        self.facing_left = data.get('facing_left', False)
        self.move_mode = data.get('move_mode', 'walkway')
        self.is_acting = 0
        self.type = 'frankie_entity'

    def update(self, engine, tick):
        """AI intent logic: returns commands for the unified pipeline."""
        target_p = next((p for p in engine.state.players if p.room_id == self.room_id), None)
        cmds = {}
        
        if target_p:
            dx = target_p.x - self.x
            dy = target_p.y - self.y
            
            if abs(dy) > 8:
                # Different level: try to find vertical path
                room = engine.state.rooms.get(self.room_id)
                
                # Are we already ON a ladder/pole?
                if self.move_mode == 'ladder':
                    if dy > 0: cmds['down'] = True
                    else: cmds['up'] = True
                    return cmds

                # Find nearest ladder/pole
                best_v = None
                min_dist = 9999
                for obj in room.objects:
                    if obj.type in ('ladder', 'pole'):
                        # Poles only for going DOWN
                        if obj.type == 'pole' and dy < 0: continue
                        
                        dist = abs(self.x - obj.x)
                        if dist < min_dist:
                            min_dist = dist
                            best_v = obj
                
                if best_v:
                    # If we are aligned with the vertical structure, use it
                    if abs(self.x - best_v.x) < 4:
                        if dy > 0: cmds['down'] = True
                        else:
                            if best_v.type == 'ladder': cmds['up'] = True
                    else:
                        # Move towards it
                        if best_v.x > self.x: cmds['right'] = True
                        else: cmds['left'] = True
            else:
                # Same level: track horizontally
                if dx > 4: cmds['right'] = True
                elif dx < -4: cmds['left'] = True
        
        return cmds

    def process_proposal(self, engine, room, entity, proposal):
        """Kill player on contact via the pipeline."""
        if proposal['room_id'] == self.room_id:
            # We check the distance between Frankenstein and the entity in the proposal
            if abs(proposal['x'] - self.x) < 12 and abs(proposal['y'] - self.y) < 12:
                proposal['is_dead'] = True

    def serialize(self):
        """Entity state serialization."""
        return {
            'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'is_moving': self.is_moving, 'facing_left': self.facing_left,
            'is_acting': self.is_acting
        }

class FrankieComponent(BaseComponent):
    """Trigger component that spawns Frankenstein when player is on the same floor."""
    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=sleeping, 1=released

    def process_proposal(self, engine, room, entity, proposal):
        """Detect player presence on the same level to trigger spawn."""
        if self.state == 0:
            # Check if it's a player entering the trigger zone
            if abs(proposal['y'] - (self.y + 32)) < 24:
                self.state = 1
                engine.state.frankies.append(FrankieEntity({
                    'x': self.x + 12, 
                    'y': self.y + 32, 
                    'room_id': proposal['room_id']
                }))
    
    def get_asset(self, tick):
        return None # Invisible trigger
