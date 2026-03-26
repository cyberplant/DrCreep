from .base import BaseComponent

class ProjectileEntity:
    """
    Moving projectile (Ray Gun bolt).
    - Moves horizontally until it hits a player or screen boundary.
    - Resets player on contact via process_proposal.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.vx = data['vx']
        self.room_id = data['room_id']
        self.active = True
        self.type = 'projectile_entity'

    def update(self, engine, tick):
        self.x += self.vx
        if self.x < 0 or self.x > 320:
            self.active = False

    def process_proposal(self, engine, room, current_state, proposal):
        """Check for contact with player and kill if touching."""
        if proposal['room_id'] == self.room_id:
            if abs(proposal['x'] - self.x) < 12 and abs(proposal['y'] - self.y) < 12:
                proposal['is_dead'] = True
                self.active = False # Bolt disappears on hit

    def serialize(self):
        return {'x': self.x, 'y': self.y, 'room_id': self.room_id}

class RaygunComponent(BaseComponent):
    """
    Automatic or trigger-able Ray Gun.
    - Moves vertically on its track.
    - Spawns a projectile when player is in front (if automatic).
    """
    ASSET = ["[red]>====>[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.initial_y = self.y
        self.direction = 1

    def update(self, engine, room, tick):
        """Vertical tracking or patrol logic."""
        if self.timer > 0: self.timer -= 1

        target_p = next((p for p in engine.state.players if p.room_id == room.id), None)
        if target_p:
            # Track player Y
            if abs(target_p.y - 32 - self.y) > 4:
                if target_p.y - 32 > self.y: self.y += 1
                else: self.y -= 1
            # Auto-fire if aligned
            if abs(target_p.y - 32 - self.y) < 8 and self.timer == 0:
                self.timer = 100
                direction = 1 if target_p.x > self.x else -1
                engine.state.projectiles.append(ProjectileEntity({
                    'x': self.x + (16*direction), 
                    'y': self.y, 
                    'vx': 3.0 * direction, 
                    'room_id': room.id
                }))
        else:
            # Patrol if no player
            if tick % 2 == 0:
                self.y += self.direction * 1
                if self.y >= self.initial_y + 32: self.direction = -1
                elif self.y <= self.initial_y: self.direction = 1

    def process_proposal(self, engine, room, current_state, proposal):
        pass # Logic moved to update for tracking

    def get_asset(self, tick):
        return self.ASSET

class RaygunSwitchComponent(BaseComponent):
    """Manual controls for a Ray Gun (Vertical movement and fire)."""
    def process_proposal(self, engine, room, current_state, proposal):
        """Handle directional and action inputs to control ray guns via proposal pipeline."""
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        self.state = 0
        if dist_x < 16 and dist_y < 48:
            commands = proposal.get('commands', {})
            if commands.get('up'): self.state = 1
            elif commands.get('down'): self.state = 2
            elif commands.get('action'): self.state = 3

            for rgun in room.objects:
                if rgun.type == 'raygun':
                    if commands.get('up'): rgun.y -= 2
                    if commands.get('down'): rgun.y += 2
                    if commands.get('action'):
                        if rgun.timer == 0:
                            rgun.timer = 100
                            engine.state.projectiles.append(ProjectileEntity({
                                'x': rgun.x + 16, 
                                'y': rgun.y, 
                                'vx': 3.0, 
                                'room_id': proposal['room_id']
                            }))

