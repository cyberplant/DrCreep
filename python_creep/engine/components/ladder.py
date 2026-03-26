from .base import BaseComponent

class LadderComponent(BaseComponent):
    """
    Vertical movement structure.
    - length: Number of tiles (each tile is 8 world units high).
    - End Y = y + (length * 8)
    """
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)
        self.end_y = self.y + (self.length * 8)

    def process_proposal(self, engine, room, current_state, proposal):
        """Handle mode switching and vertical snapping."""
        if abs(proposal['x'] - self.x) < 4:
            if self.y <= proposal['y'] <= self.end_y:
                if proposal['move_mode'] == 'ladder':
                    proposal['x'] = self.x
                    proposal['has_support'] = True
                elif abs(current_state.get('vy', 0)) > 0.1:
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
                if proposal['move_mode'] == 'ladder':
                    proposal['x'] = self.x
                    proposal['has_support'] = True
                    # Block UP movement on poles
                    if current_state.get('vy', 0) < -0.1: 
                        proposal['y'] = current_state['y']
                elif current_state.get('vy', 0) > 0.1:
                    proposal['move_mode'] = 'ladder'
                    proposal['x'] = self.x
                    proposal['has_support'] = True
