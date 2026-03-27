from .base import BaseComponent

class DoorComponent(BaseComponent):
    """Standard Door component for transitions between rooms."""
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
        if 0 < self.state < 2:
            if tick % 10 == 0:
                self.state += 1

    def process_proposal(self, engine, room, current_state, proposal):
        """Handle room transitions when walking into an open door."""
        if self.state == 2: # Fully open
            # Tighten X-bounds: player must be within 4 pixels of door center (x+10)
            if abs(proposal['x'] - (self.x + 10)) < 4 and abs(proposal['y'] - (self.y + 32)) < 16:
                if proposal.get('commands', {}).get('up'): # Intent to enter door
                    if self.properties.get('is_exit'):
                        engine.state.victory = True
                        return
                    
                    target_room_id = self.properties['link_room']
                    target_door_idx = self.properties['link_door']
                    target_room = engine.state.rooms.get(target_room_id)
                    
                    if target_room:
                        target_doors = [t for t in target_room.objects if t.type == 'door']
                        if 0 <= target_door_idx < len(target_doors):
                            tobj = target_doors[target_door_idx]
                            proposal['room_id'] = target_room_id
                            proposal['x'] = tobj.x + 10
                            proposal['y'] = tobj.y + 32
                            tobj.state = 2 # Ensure target door is also open

    def get_asset(self, tick):
        if self.state == 0: return self.ASSET[0]
        if self.state == 2: return self.ASSET[-1]
        return self.ASSET[1]

class DoorbellComponent(BaseComponent):
    """Simple trigger to open a specific door in the room."""
    def process_proposal(self, engine, room, current_state, proposal):
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            if proposal.get('commands', {}).get('action'):
                target_id = self.properties.get('target_door_idx')
                room_doors = [obj for obj in room.objects if obj.type == 'door']
                if 0 <= target_id < len(room_doors):
                    if room_doors[target_id].state == 0:
                        room_doors[target_id].state = 1
    def get_asset(self, tick):
        return ["[white]●[/]"]
