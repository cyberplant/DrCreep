from .base import BaseComponent

class MummyEntity:
    """
    Mummy AI Entity.
    Logic:
    - Moves slower than the player (every 3 ticks).
    - Tracks player X position.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.room_id = data['room_id']
        self.is_moving = False
        self.facing_left = data.get('facing_left', False)
        self.move_mode = 'walkway'
        self.is_acting = 0
        self.type = 'mummy_entity'

    def update(self, engine, tick):
        """AI intent logic: returns commands every 3 ticks."""
        target_p = next((p for p in engine.state.players if p.room_id == self.room_id), None)
        cmds = {}
        
        if target_p and tick % 3 == 0:
            dx = target_p.x - self.x
            # Track player X
            if dx > 4: cmds['right'] = True
            elif dx < -4: cmds['left'] = True
        
        return cmds

    def process_proposal(self, engine, room, entity, proposal):
        """Kill player on contact via the pipeline."""
        if proposal['room_id'] == self.room_id:
            if abs(proposal['x'] - self.x) < 12 and abs(proposal['y'] - self.y) < 12:
                proposal['is_dead'] = True

    def serialize(self):
        """Standard serialization for entity broadcast."""
        return {
            'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'is_moving': self.is_moving, 'facing_left': self.facing_left,
            'is_acting': self.is_acting
        }

class MummyReleaseComponent(BaseComponent):
    """Component that spawns a Mummy when an entity walks nearby."""
    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=sleeping, 1=released

    def process_proposal(self, engine, room, entity, proposal):
        """Detect entity proximity and trigger spawn."""
        if self.state == 0:
            # Trigger if an entity is close to the release trigger
            if abs(proposal['x'] - self.x) < 16 and abs(proposal['y'] - 32 - self.y) < 32:
                self.state = 1
                engine.state.mummies.append(MummyEntity({
                    'x': self.properties['tomb_x'] + 12, 
                    'y': self.properties['tomb_y'] + 24, 
                    'room_id': proposal['room_id']
                }))

    def get_asset(self, tick):
        # M for Mummy release trigger
        return ["[white]M[/]"]

class MummyTombComponent(BaseComponent):
    """Visual placeholder for a mummy's tomb."""
    def process_proposal(self, engine, room, entity, proposal):
        pass

    def get_asset(self, tick):
        return ["[red]#####[/]", "[red]#####[/]", "[red]#####[/]", "[red]#####[/]", "[red]#####[/]", "[red]#####[/]"]
