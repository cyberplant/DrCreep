from .base import BaseComponent

class ProjectileEntity:
    """
    Moving projectile (Ray Gun bolt).
    - Moves horizontally until it hits a player or screen boundary.
    - Resets player on contact.
    """
    def __init__(self, data):
        self.x = data['x']
        self.y = data['y']
        self.vx = data['vx']
        self.room_id = data['room_id']
        self.active = True

    def update(self, engine, tick):
        self.x += self.vx
        # Hit check
        for p in engine.state.players:
            if p.room_id == self.room_id and abs(p.x - self.x) < 12 and abs(p.y - self.y) < 12:
                engine._reset_player(p)
                self.active = False
                return
        # Boundary check
        if self.x < 0 or self.x > 320:
            self.active = False

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
        """Vertical patrol logic."""
        if self.timer > 0:
            self.timer -= 1
        if tick % 2 == 0:
            self.y += self.direction * 1
            if self.y >= self.initial_y + 32:
                self.direction = -1
            elif self.y <= self.initial_y:
                self.direction = 1

    def on_collide(self, engine, room, entity):
        """Automatic firing logic when entity is in line of sight."""
        if abs(entity.y - self.y) < 16 and self.timer == 0:
            self.timer = 100
            direction = 1 if entity.x > self.x else -1
            engine.state.projectiles.append(ProjectileEntity({
                'x': self.x + (16*direction), 
                'y': self.y, 
                'vx': 3.0 * direction, 
                'room_id': entity.room_id
            }))

    def get_asset(self, tick):
        return self.ASSET

class RaygunSwitchComponent(BaseComponent):
    """Manual controls for a Ray Gun (Vertical movement and fire)."""
    ASSET = [
            " [cyan]^[/] ",
            " [cyan]O[/] ",
            " [cyan]v[/] "
        ]
    def on_interact(self, engine, room, player, commands):
        """Handle directional and action inputs to control ray guns."""
        for rgun in room.objects:
            if rgun.type == 'raygun':
                if commands.get('up'): rgun.y -= 2; return
                if commands.get('down'): rgun.y += 2; return
                if commands.get('action'):
                    if rgun.timer == 0:
                        rgun.timer = 100
                        engine.state.projectiles.append(ProjectileEntity({
                            'x': rgun.x + 16, 
                            'y': rgun.y, 
                            'vx': 3.0, 
                            'room_id': player.room_id
                        }))
                    return
    def get_asset(self, tick):
        return self.ASSET
