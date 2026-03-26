
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
        self.death_timer = 0 # Animation timer for disintegration

    def update(self, engine, tick, commands):
        # 0. Handle Death Animation
        if self.death_timer > 0:
            self.death_timer -= 1
            if self.death_timer == 0:
                # Respawn at room 0 (Tutorial start or similar)
                self.room_id = 0
                self.x, self.y = 20, 192
                self.move_mode = 'walkway'
                self.vx, self.vy = 0, 0
            return

        # Handle teleport delay
        if self.is_teleporting > 0:
            self.is_teleporting -= 1
            if self.is_teleporting == 0:
                self.room_id, self.x, self.y = self.target_room_id, self.target_x, self.target_y
            return

        room = engine.state.rooms.get(self.room_id)
        if not room: return

        if self.is_acting > 0: self.is_acting -= 1
        
        # 1. Create Initial Proposal based on input
        if commands.get('left'): self.vx = -2.0
        if commands.get('right'): self.vx = 2.0
        if commands.get('up'): self.vy = -2.0
        if commands.get('down'): self.vy = 2.0
        if commands.get('action'): self.is_acting = 10

        current_state = {
            'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'vx': self.vx, 'vy': self.vy, 'move_mode': self.move_mode,
            'is_dead': False
        }
        
        proposal = current_state.copy()
        proposal['x'] += self.vx
        proposal['y'] += self.vy
        proposal['commands'] = commands

        # 2. Pipeline: Let components AND dynamic entities process the proposal
        for obj in room.objects:
            obj.process_proposal(engine, room, current_state, proposal)
        
        # Also process against dynamic entities in the same room
        for m in engine.state.mummies:
            if hasattr(m, 'process_proposal'): m.process_proposal(engine, room, current_state, proposal)
        for f in engine.state.frankies:
            if hasattr(f, 'process_proposal'): f.process_proposal(engine, room, current_state, proposal)
        for p in engine.state.projectiles:
            if hasattr(p, 'process_proposal'): p.process_proposal(engine, room, current_state, proposal)

        # 3. Handle Death from pipeline
        if proposal.get('is_dead'):
            self.death_timer = 30 # Start disintegration
            return

        # 4. Resolve Final Movement and Support
        # Logic for walkway/ladder bounds remains but uses proposal results
        support = self._find_support(room, proposal['x'], proposal['y'], proposal['move_mode'])
        
        # Boundary and Mode Logic
        if support:
            if proposal['move_mode'] == 'walkway':
                proposal['y'] = support.y
                min_scr_x, max_scr_x = 16, 172
                proposal['x'] = max(max(min_scr_x, support.x), min(min(max_scr_x, support.x + (support.properties['length'] * 4)), proposal['x']))
                
                # Room transitions (Simplified: components can set target_room_id in proposal)
                if proposal.get('target_room_id') is not None:
                    self.room_id = proposal['target_room_id']
                    self.x, self.y = proposal['target_x'], proposal['target_y']
                    self.last_transition_tick = tick
                    return
            else:
                proposal['x'] = support.x
                # Boundary logic for ladder...
                # (Keeping it simple for now, can be fully componentized later)

        # 5. Apply approved proposal
        self.x, self.y = proposal['x'], proposal['y']
        self.room_id = proposal['room_id']
        self.move_mode = proposal['move_mode']
        self.is_moving = (abs(self.vx) > 0.1 or abs(self.vy) > 0.1)
        if abs(self.vx) > 0.1: self.facing_left = (self.vx < 0)

        # Friction
        self.vx *= 0.5
        self.vy *= 0.5

    def _find_support(self, room, x, y, move_mode):
        if move_mode == 'walkway':
            for obj in room.objects:
                if obj.type == 'walkway':
                    start_x, end_x = obj.x, obj.x + (obj.properties['length'] * 4)
                    if start_x <= x <= end_x and abs(y - obj.y) < 4:
                        return obj
        else:
            for obj in room.objects:
                if obj.type in ('ladder', 'pole'):
                    if abs(x - obj.x) < 4:
                        # Simple height check for ladder
                        return obj
        return None

    def serialize(self):
        res = {
            'id': self.id, 'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'keys': self.keys, 'is_moving': self.is_moving, 
            'is_acting': self.is_acting, 'is_teleporting': self.is_teleporting, 
            'facing_left': self.facing_left
        }
        if self.death_timer > 0:
            res['is_dead'] = True # For client animation
        return res
