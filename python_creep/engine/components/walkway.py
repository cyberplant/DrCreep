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
        # Detect horizontal movement intent
        has_horizontal_intent = abs(proposal['x'] - current_state.x) > 0.1
        # Detect vertical intent
        has_vertical_intent = proposal['commands'].get('up') or proposal['commands'].get('down')

        if self.x <= proposal['x'] <= self.end_x:
            # Check if player is within the walkway's vertical range (8 units)
            if self.y <= proposal['y'] <= self.y + 8:
                # Provide support if already in walkway mode OR if transitioning from ladder
                # Crucial: Don't snap Y if the player is trying to move vertically (entering ladder)
                if proposal['move_mode'] == 'walkway' or (has_horizontal_intent and abs(proposal['y'] - self.y) < 4):
                    if not has_vertical_intent or proposal['move_mode'] == 'walkway':
                        if not has_vertical_intent:
                            proposal['y'] = self.y # Snap to top surface
                        proposal['move_mode'] = 'walkway'
                        proposal['has_support'] = True
