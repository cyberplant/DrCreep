from .base import BaseComponent

class ForcefieldComponent(BaseComponent):
    """
    Impassable energy barrier.
    """
    STATES = {
        0: ["[cyan]z[/]", " ", " ", " ", " ", " ", " ", " "],
        1: ["[cyan]z[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]"]
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1

    def process_proposal(self, engine, room, current_state, proposal):
        """Block entities if field is active."""
        if self.state == 1:
            if abs(proposal['y'] - self.y) < 24:
                # Check if moving through the field
                if current_state['x'] < self.x and proposal['x'] >= self.x - 4:
                    proposal['x'] = self.x - 4
                elif current_state['x'] > self.x and proposal['x'] <= self.x + 4:
                    proposal['x'] = self.x + 4

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[1])

class ForcefieldSwitchComponent(BaseComponent):
    """
    Temporary switch for forcefields.
    """
    def update(self, engine, room, tick):
        self.state = self.timer
        if self.timer > 0:
            if tick % engine.ticks_per_second == 0:
                self.timer -= 1
                if self.timer == 0:
                    for obj in room.objects:
                        if obj.type == 'forcefield':
                            obj.state = 1

    def process_proposal(self, engine, room, current_state, proposal):
        """Handle interaction via pipeline."""
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            if proposal.get('commands', {}).get('action'):
                self.timer = 8
                for fobj in room.objects:
                    if fobj.type == 'forcefield':
                        fobj.state = 0

    def get_asset(self, tick):
        if self.timer > 0:
            return [f"[cyan][ {self.timer} ][/]"]
        else:
            return ["[cyan][ * ][/]"]
