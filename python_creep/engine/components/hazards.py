from .base import BaseComponent

class ForcefieldComponent(BaseComponent):
    STATES = {
        0: ["[cyan]z[/]", " ", " ", " ", " ", " ", " ", " "],
        1: ["[cyan]z[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]"]
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1

    def filter_movement(self, engine, room, entity, dx, dy):
        if self.state == 1: # Active
            if abs(entity.y - self.y) < 24:
                # Entity is moving into or across the forcefield
                next_x = entity.x + dx
                if entity.x < self.x and next_x >= self.x - 4: return (self.x - 4) - entity.x, dy, True
                elif entity.x > self.x and next_x <= self.x + 4: return (self.x + 4) - entity.x, dy, True
        return dx, dy, False

class LightningMachineComponent(BaseComponent):
    ASSET = ["[cyan](O)[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)

    def on_collide(self, engine, room, entity):
        if engine.room_states[entity.room_id]['lightning'].get(self.system_id):
            if abs(entity.x - (self.x + 2)) < 12 and self.y <= entity.y <= self.y + 160:
                engine._reset_player(entity)

    def get_asset(self, tick):
        return self.ASSET

class RaygunComponent(BaseComponent):
    ASSET = ["[red]>====>[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.initial_y = self.y
        self.direction = 1

    def update(self, engine, room, tick):
        if self.timer > 0:
            self.timer -= 1
        if tick % 2 == 0:
            self.y += self.direction * 1
            if self.y >= self.initial_y + 32:
                self.direction = -1
            elif self.y <= self.initial_y:
                self.direction = 1

    def on_collide(self, engine, room, entity):
        if abs(entity.y - self.y) < 16 and self.timer == 0:
            self.timer = 100
            direction = 1 if entity.x > self.x else -1
            # Current way: engine.state.projectiles.append(...)
            # This logic might move to entities.py later.
            engine.state.projectiles.append({'x': self.x + (16*direction), 'y': self.y, 'vx': 3.0 * direction, 'room_id': entity.room_id})

    def get_asset(self, tick):
        return self.ASSET
