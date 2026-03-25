from .base import BaseComponent

class ForcefieldComponent(BaseComponent):
    """
    Impassable energy barrier.
    - Blocking behavior is handled in filter_movement.
    """
    STATES = {
        0: ["[cyan]z[/]", " ", " ", " ", " ", " ", " ", " "],
        1: ["[cyan]z[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]"]
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1

    def filter_movement(self, engine, room, entity, dx, dy):
        """Block entities if field is active (state 1)."""
        if self.state == 1: # Active
            if abs(entity.y - self.y) < 24:
                next_x = entity.x + dx
                # Simple X-axis blocking logic
                if entity.x < self.x and next_x >= self.x - 4: return (self.x - 4) - entity.x, dy, True
                elif entity.x > self.x and next_x <= self.x + 4: return (self.x + 4) - entity.x, dy, True
        return dx, dy, False

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[1])

class ForcefieldSwitchComponent(BaseComponent):
    """
    Temporary switch for forcefields.
    - Action button turns forcefields OFF.
    - Automatically turns back ON after a timer expires.
    """
    def update(self, engine, room, tick):
        """Countdown timer to re-activate fields."""
        if self.timer > 0:
            if tick % engine.ticks_per_second == 0:
                self.timer -= 1
                if self.timer == 0:
                    for obj in room.objects:
                        if obj.type == 'forcefield':
                            obj.state = 1

    def on_interact(self, engine, room, player, commands):
        """Disable forcefields in the room temporarily."""
        if commands.get('action'):
            self.timer = 8
            for fobj in room.objects:
                if fobj.type == 'forcefield':
                    fobj.state = 0
    def get_asset(self, tick):
        return ["[cyan]S[/]"]
