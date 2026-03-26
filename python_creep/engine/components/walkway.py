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
                # Check if player is within the walkway's vertical range (8 units)
                if self.y <= proposal['y'] <= self.y + 8:
                    proposal['y'] = self.y # Snap to top surface
                    proposal['has_support'] = True
