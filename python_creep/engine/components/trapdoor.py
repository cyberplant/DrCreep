from .base import BaseComponent

class TrapdoorComponent(BaseComponent):
    STATES = {
        0: ["[white]__________[/]"], # Closed
        1: ["[white]          [/]"]  # Open (Hole)
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1 if data.get('is_open') else 0

    def filter_movement(self, engine, room, entity, dx, dy):
        if self.state == 1:
            if abs(self.y - (entity.y - 32)) < 8 and self.x - 4 <= entity.x <= self.x + 12:
                return dx, dy, True
        return dx, dy, False

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[0])

class TrapdoorSwitchComponent(BaseComponent):
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_idx')
            if 0 <= target_id < len(room.objects):
                t_obj = room.objects[target_id]
                t_obj.state = 1 if t_obj.state == 0 else 0
    def get_asset(self, tick):
        return ["[cyan]o[/]"]
