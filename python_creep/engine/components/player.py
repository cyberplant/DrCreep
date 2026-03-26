
class Player:
    def __init__(self, id, start_x, start_y):
        self.id = id
        self.x = start_x
        self.y = start_y
        self.vx = 0
        self.vy = 0
        self.lives = 3
        self.keys = []
        self.anim_state = "idle"
        self.room_id = 0
        self.facing_left = False
        self.move_mode = 'walkway'
        self.last_transition_tick = 0
        self.is_teleporting = 0
        self.target_room_id = 0
        self.target_x = 0
        self.target_y = 0
        self.is_moving = False
        self.is_acting = 0
        self.death_timer = 0

    def update(self, engine, tick, commands):
        if self.death_timer > 0:
            self.death_timer -= 1
            if self.death_timer == 0:
                self.room_id = 0
                self.x, self.y = 20, 192
                self.move_mode = 'walkway'
                self.vx, self.vy = 0, 0
            return

        if self.is_teleporting > 0:
            self.is_teleporting -= 1
            if self.is_teleporting == 0:
                self.room_id, self.x, self.y = self.target_room_id, self.target_x, self.target_y
            return

        room = engine.state.rooms.get(self.room_id)
        if not room: return

        if self.is_acting > 0: self.is_acting -= 1
        
        # Intent based on input
        if commands.get('left'): self.vx = -2.0
        if commands.get('right'): self.vx = 2.0
        if commands.get('up'): self.vy = -2.0
        if commands.get('down'): self.vy = 2.0
        if commands.get('action'): self.is_acting = 10

        current_state = {
            'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'vx': self.vx, 'vy': self.vy, 'move_mode': self.move_mode,
            'is_dead': False,
            'keys': self.keys[:]
        }
        
        proposal = current_state.copy()
        proposal['x'] += self.vx
        proposal['y'] += self.vy
        proposal['commands'] = commands
        proposal['has_support'] = False # Default: falling

        # Pipeline: All objects (environment, entities, hazards) process the proposal
        for obj in room.objects:
            obj.process_proposal(engine, room, current_state, proposal)
        
        for m in engine.state.mummies:
            if hasattr(m, 'process_proposal'): m.process_proposal(engine, room, current_state, proposal)
        for f in engine.state.frankies:
            if hasattr(f, 'process_proposal'): f.process_proposal(engine, room, current_state, proposal)
        for proj in engine.state.projectiles:
            if hasattr(proj, 'process_proposal'): proj.process_proposal(engine, room, current_state, proposal)

        if proposal.get('is_dead'):
            self.death_timer = 30
            return

        # If no component gave support, entity falls (simplified gravity)
        if not proposal['has_support']:
            proposal['y'] += 4
            proposal['move_mode'] = 'walkway' # Force walkway mode when falling

        # Apply boundary limits (World)
        proposal['x'] = max(16, min(304, proposal['x']))
        proposal['y'] = max(0, min(200, proposal['y']))

        # 5. Apply approved proposal
        self.x, self.y = proposal['x'], proposal['y']
        self.room_id = proposal['room_id']
        self.move_mode = proposal['move_mode']
        self.keys = proposal['keys']
        self.is_moving = (abs(self.vx) > 0.1 or abs(self.vy) > 0.1)

        if abs(self.vx) > 0.1: self.facing_left = (self.vx < 0)

        # Friction
        self.vx *= 0.5
        self.vy *= 0.5

    def serialize(self):
        res = {
            'id': self.id, 'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'keys': self.keys, 'is_moving': self.is_moving, 
            'is_acting': self.is_acting, 'is_teleporting': self.is_teleporting, 
            'facing_left': self.facing_left
        }
        if self.death_timer > 0:
            res['is_dead'] = True
        return res
