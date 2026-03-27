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
        # Detect horizontal movement intent
        has_horizontal_intent = abs(proposal['x'] - player.x) > 0.1
        # Detect vertical intent
        intent_up = proposal['commands'].get('up')
        intent_down = proposal['commands'].get('down')

        if abs(proposal['x'] - self.x) < 4:
            # Entry/Support Range: From top (self.y) to bottom (self.end_y)
            # Allow 'down' entry from the walkway surface (self.y)
            if self.y - 2 <= proposal['y'] <= self.end_y + 2:
                if proposal['move_mode'] == 'ladder':
                    # Only snap to X if no horizontal intent (allows walking off)
                    if not has_horizontal_intent:
                        proposal['x'] = self.x
                    proposal['has_support'] = True
                elif intent_up or intent_down:
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
        # Detect horizontal movement intent
        has_horizontal_intent = abs(proposal['x'] - player.x) > 0.1
        # Detect vertical intent
        intent_down = proposal['commands'].get('down')

        if abs(proposal['x'] - self.x) < 4:
            if self.y - 2 <= proposal['y'] <= self.end_y + 2:
                if proposal['move_mode'] == 'ladder':
                    # Only snap to X if no horizontal intent
                    if not has_horizontal_intent:
                        proposal['x'] = self.x
                    proposal['has_support'] = True
                    # Block UP movement on poles
                    if dy < -0.1: 
                        proposal['y'] = player.y
                elif intent_down:
                    # Switch to ladder mode only if moving DOWN
                    proposal['move_mode'] = 'ladder'
                    proposal['x'] = self.x
                    proposal['has_support'] = True
