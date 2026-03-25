from .base import BaseComponent

class DoorComponent(BaseComponent):
    ASSET = [
               [ # Closed
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white]----------"
            ],
               [ # Partial 1
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][[yellow]________[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ],
               [ # Partial 2
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][[yellow]________[/]][/]",
                "[white][  [next_room_color]/░░░░░[/]][/]",
                "[white][ [next_room_color]/______[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ],
               [ # Open
                "[white]----------[/]",
                "[white][     [next_room_color]___[/]][/]",
                "[white][    [next_room_color]/░░░[/]][/]",
                "[white][   [next_room_color]/____[/]][/]",
                "[white][  [next_room_color]/░░░░░[/]][/]",
                "[white][ [next_room_color]/______[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ]
        ]

    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=closed, 1=opening, 2=open

    def update(self, engine, room, tick):
        if 0 < self.state < 2:
            if tick % 10 == 0:
                self.state += 1

    def get_asset(self, tick):
        if self.state == 0: return self.ASSET[0]
        if self.state == 2: return self.ASSET[-1]
        return self.ASSET[1]

class WalkwayComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)

class LadderComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)

class PoleComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)

class TrapdoorComponent(BaseComponent):
    STATES = {
        0: ["[white]__________[/]"], # Closed
        1: ["[white]          [/]"]  # Open (Hole)
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1 if data.get('is_open') else 0

    def filter_movement(self, engine, room, entity, dx, dy):
        # If open and player is on top, they should fall
        if self.state == 1:
            # We need to find the walkway this trapdoor is on
            # and check if player is within trapdoor bounds
            if abs(self.y - (entity.y - 32)) < 8 and self.x - 4 <= entity.x <= self.x + 12:
                return dx, dy, True # STOP/FALL signal? 
                # Actually original logic sets is_hole=True which blocks support
        return dx, dy, False

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[0])

class ConveyorComponent(BaseComponent):
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

    def filter_movement(self, engine, room, entity, dx, dy):
        if self.state != 1: # Moving left or right
            if abs(self.y - (entity.y - 32)) < 8 and self.x - 4 <= entity.x <= self.x + 36:
                push = -1.5 if self.state == 0 else 1.5
                return dx + push, dy, False
        return dx, dy, False

    def get_asset(self, tick):
        if self.state == 0: # LEFT
            frames = self.ASSETS["left"]
            return frames[(tick // 4) % len(frames)]
        elif self.state == 2: # RIGHT
            frames = self.ASSETS["right"]
            return frames[(tick // 4) % len(frames)]
        else:
            return self.ASSETS["off"]
