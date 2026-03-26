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

    def process_proposal(self, engine, room, player, proposal):
        """Handle mode switching and vertical snapping."""
        # Calculate vertical intent
        dy = proposal['y'] - player.y

        if abs(proposal['x'] - self.x) < 4:
            if self.y <= proposal['y'] <= self.end_y:
                if proposal['move_mode'] == 'ladder':
                    proposal['x'] = self.x
                    proposal['has_support'] = True
                elif abs(dy) > 0.1:
                    # Switch to ladder mode if intending to move vertically
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

    def process_proposal(self, engine, room, player, proposal):
        # Calculate vertical intent
        dy = proposal['y'] - player.y

        if abs(proposal['x'] - self.x) < 4:
            if self.y <= proposal['y'] <= self.end_y:
                if proposal['move_mode'] == 'ladder':
                    proposal['x'] = self.x
                    proposal['has_support'] = True
                    # Block UP movement on poles: if moving up, revert to player.y
                    if dy < -0.1: 
                        proposal['y'] = player.y
                elif dy > 0.1:
                    # Switch to ladder mode only if moving DOWN
                    proposal['move_mode'] = 'ladder'
                    proposal['x'] = self.x
                    proposal['has_support'] = True
