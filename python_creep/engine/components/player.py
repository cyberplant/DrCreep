
class Player:
    """
    Player state container.
    Logic has been moved to GameEngine and Components (State Pipeline).
    """
    def __init__(self, id, start_x, start_y):
        self.id = id
        self.x = start_x
        self.y = start_y
        self.keys = []
        self.room_id = 0
        self.facing_left = False
        self.move_mode = 'walkway'
        self.is_moving = False
        self.is_acting = 0

    def apply_proposal(self, proposal):
        """Apply the final state resolved by the Engine pipeline."""
        self.x = proposal['x']
        self.y = proposal['y']
        self.room_id = proposal['room_id']
        self.move_mode = proposal['move_mode']
        self.keys = proposal['keys']
        self.is_moving = proposal['is_moving']
        self.is_acting = proposal['is_acting']
        self.facing_left = proposal['facing_left']

    def serialize(self):
        return {
            'id': self.id, 'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'keys': self.keys, 'is_moving': self.is_moving, 
            'is_acting': self.is_acting, 'facing_left': self.facing_left
        }
