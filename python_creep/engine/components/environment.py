from .base import BaseComponent

class WalkwayComponent(BaseComponent):
    """
    Horizontal platform for players and entities.
    - length: Number of tiles the walkway covers (each tile is 4 world units wide).
    - End X = x + (length * 4)
    """
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)
        self.end_x = self.x + (self.length * 4)

    def process_proposal(self, engine, room, current_state, proposal):
        """If player is within X bounds and close to Y, treat as support."""
        if proposal['move_mode'] == 'walkway':
            if self.x <= proposal['x'] <= self.end_x:
                if abs(proposal['y'] - self.y) < 4:
                    proposal['y'] = self.y
                    proposal['has_support'] = True

class LadderComponent(BaseComponent):
    """
    Vertical movement structure.
    - length: Number of tiles (each tile is 8 world units high).
    - End Y = y + (length * 8)
    """
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)
        # In Dr. Creep, ladders often go DOWN from their Y position
        self.end_y = self.y + (self.length * 8)

    def process_proposal(self, engine, room, current_state, proposal):
        """Handle mode switching and vertical snapping."""
        if abs(proposal['x'] - self.x) < 4:
            if self.y <= proposal['y'] <= self.end_y:
                proposal['can_climb'] = True
                if proposal['move_mode'] == 'ladder':
                    proposal['x'] = self.x
                    proposal['has_support'] = True
                elif abs(proposal['vy']) > 0.1:
                    # Switch to ladder mode if intending to climb
                    proposal['move_mode'] = 'ladder'
                    proposal['x'] = self.x
                    proposal['has_support'] = True

class PoleComponent(BaseComponent):
    """
    Vertical slide structure. Allows DOWN movement only.
    """
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)
        self.end_y = self.y + (self.length * 8)

    def process_proposal(self, engine, room, current_state, proposal):
        if abs(proposal['x'] - self.x) < 4:
            if self.y <= proposal['y'] <= self.end_y:
                proposal['can_slide'] = True
                if proposal['move_mode'] == 'ladder':
                    proposal['x'] = self.x
                    proposal['has_support'] = True
                    # Block UP movement on poles
                    if proposal['vy'] < 0: proposal['y'] = current_state['y']
                elif proposal['vy'] > 0.1:
                    proposal['move_mode'] = 'ladder'
                    proposal['x'] = self.x
                    proposal['has_support'] = True
