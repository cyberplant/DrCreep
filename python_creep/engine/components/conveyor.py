from .base import BaseComponent

class ConveyorComponent(BaseComponent):
    """
    Moving belt that pushes the player horizontally.
    - state 0: LEFT
    - state 1: OFF
    - state 2: RIGHT
    """
    ASSETS = {
        "left": [
            [r"[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[/]"],
            [r"[blue][gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~[blue][/]"],
            [r"[blue][gray]~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue][/]"],
        ],
        "right": [
            ["[blue]/  /  /  / [/]"],
            ["[blue] /  /  /  /[/]"],
            ["[blue]  /  /  /  [/]"],
        ],
        "off": [["[blue]~~~~~~~~~~~~[/]"]]
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = data.get('state', 1)

    def process_proposal(self, engine, room, player, proposal):
        """Applies horizontal push to entities standing on the belt."""
        if self.state != 1: # ON
            # Check if entity is on the belt
            if abs(self.y - (proposal['y'] - 32)) < 8 and self.x - 4 <= proposal['x'] <= self.x + 36:
                push = -1.5 if self.state == 0 else 1.5
                proposal['x'] += push

    def get_asset(self, tick):
        """Returns animated or static belt frame."""
        if self.state == 0: # LEFT
            frames = self.ASSETS["left"]
            return frames[(tick // 4) % len(frames)]
        elif self.state == 2: # RIGHT
            frames = self.ASSETS["right"]
            return frames[(tick // 4) % len(frames)]
        else:
            return self.ASSETS["off"]

class ConveyorSwitchComponent(BaseComponent):
    """Toggles conveyor state: Left -> Off -> Right -> Off."""
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_idx')
            if 0 <= target_id < len(room.objects):
                c_obj = room.objects[target_id]
                states = [0, 1, 2, 1]
                cur_idx = states.index(c_obj.state) if c_obj.state in states else 1
                # Cycle through states
                c_obj.state = states[(cur_idx + 1) % 4]
    def get_asset(self, tick):
        return ["[cyan]o[/]"]
