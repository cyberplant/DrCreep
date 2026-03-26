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
            # Check if entity is on the belt (using 8-unit thickness range)
            if self.y <= (proposal['y'] - 32) <= self.y + 8 and self.x - 4 <= proposal['x'] <= self.x + 36:
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
    def update(self, engine, room, tick):
        target_id = self.properties.get('target_idx')
        if 0 <= target_id < len(room.objects):
            self.state = room.objects[target_id].state

    def process_proposal(self, engine, room, current_state, proposal):
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            if proposal.get('commands', {}).get('action') and proposal.get('is_acting') == 10:
                target_id = self.properties.get('target_idx')
                if 0 <= target_id < len(room.objects):
                    c_obj = room.objects[target_id]
                    # Cycle: LEFT (0) -> OFF (1) -> RIGHT (2) -> OFF (1) -> ...
                    if c_obj.state == 0: c_obj.state = 1
                    elif c_obj.state == 1: c_obj.state = 2
                    elif c_obj.state == 2: c_obj.state = 1
