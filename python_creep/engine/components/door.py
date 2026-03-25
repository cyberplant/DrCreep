from .base import BaseComponent

class DoorComponent(BaseComponent):
    """
    Standard Door component for transitions between rooms.
    Logic:
    - state 0: Closed
    - state 1: Opening (advances frame every 10 ticks)
    - state 2: Open (player can transition)
    """
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
        self.state = 0

    def update(self, engine, room, tick):
        """Handle automatic door animation sequence."""
        if 0 < self.state < 2:
            if tick % 10 == 0:
                self.state += 1

    def get_asset(self, tick):
        """Return the appropriate frame based on current door state."""
        if self.state == 0: return self.ASSET[0]
        if self.state == 2: return self.ASSET[-1]
        return self.ASSET[1]

class DoorbellComponent(BaseComponent):
    """Simple trigger to open a specific door in the room."""
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_door_idx')
            # Look for door objects in the room
            room_doors = [obj for obj in room.objects if obj.type == 'door']
            if 0 <= target_id < len(room_doors):
                # Trigger opening sequence
                if room_doors[target_id].state == 0:
                    room_doors[target_id].state = 1
    def get_asset(self, tick):
        return ["[white]●[/]"]
