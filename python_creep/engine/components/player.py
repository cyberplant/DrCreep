
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
        self.on_trapdoor_switch = False # state for switch toggle debouncing

    def update(self, engine, tick, commands):
        if self.is_teleporting > 0:
            self.is_teleporting -= 1
            if self.is_teleporting == 0:
                self.room_id, self.x, self.y = self.target_room_id, self.target_x, self.target_y
            return

        room = engine.state.rooms.get(self.room_id)
        if not room: return

        if self.is_acting > 0: self.is_acting -= 1
        
        # 1. Handle Input (Basic intent)
        if commands:
            if commands.get('left'): self.vx = -2.0
            if commands.get('right'): self.vx = 2.0
            if commands.get('up'): self.vy = -2.0
            if commands.get('down'): self.vy = 2.0
            if commands.get('action'):
                self.is_acting = 10
                # Interaction check
                for obj in room.objects:
                    dist_x, dist_y = abs(self.x - obj.x), abs((self.y - 16) - obj.y)
                    if dist_x < 16 and dist_y < 48:
                        obj.on_interact(engine, room, self, commands)
            
            # Special up/down handling for some objects (Teleport color, Raygun vertical)
            # We call on_interact even if NOT action for some components
            if commands.get('up') or commands.get('down'):
                 for obj in room.objects:
                    dist_x, dist_y = abs(self.x - obj.x), abs((self.y - 16) - obj.y)
                    if dist_x < 16 and dist_y < 48:
                        # Only some components care about up/down without action
                        from .teleport import TeleportComponent
                        from .raygun import RaygunSwitchComponent
                        if isinstance(obj, (TeleportComponent, RaygunSwitchComponent)):
                            obj.on_interact(engine, room, self, commands)

        # 2. Collision Triggers (Passive)
        for obj in room.objects:
            obj.on_collide(engine, room, self)

        # 3. Physics & Movement
        dx, dy = self.vx, self.vy
        
        # Let components filter movement (Conveyors, Forcefields)
        stop_by_component = False
        for obj in room.objects:
            dx, dy, stop = obj.filter_movement(engine, room, self, dx, dy)
            if stop: stop_by_component = True

        # Support Detection
        support = self._find_support(room)
        
        # Check for Trapdoor falling
        if self.move_mode == 'walkway' and support:
            for obj in room.objects:
                from .trapdoor import TrapdoorComponent
                if isinstance(obj, TrapdoorComponent) and obj.state == 1:
                    # If player is on a trapdoor that is open
                    if abs(obj.y - (support.y - 32)) < 8 and obj.x - 4 <= self.x <= obj.x + 12:
                        support = None # Fall!
                        break

        self.is_moving = (abs(dx) > 0.1 or abs(dy) > 0.1)
        if abs(dx) > 0.1:
            self.facing_left = (dx < 0)

        if support:
            if self.move_mode == 'walkway':
                self.y = support.y
                next_x = self.x + dx
                min_scr_x, max_scr_x = 16, 172
                # Boundary check based on walkway length
                self.x = max(max(min_scr_x, support.x), min(min(max_scr_x, support.x + (support.properties['length'] * 4)), next_x))
                
                # Check for room transitions (Doors)
                if self.vy < -0.1 and (tick - self.last_transition_tick) > 50:
                    self._check_door_transition(engine, room, tick)

                # Check for mode switch (Walkway -> Ladder)
                if abs(self.vy) > 0.1:
                    for obj in room.objects:
                        from .environment import LadderComponent, PoleComponent
                        if isinstance(obj, (LadderComponent, PoleComponent)) and abs(self.x - obj.x) < 4:
                            if self.vy > 0 and abs(self.y - (obj.y + obj.properties['length']*8)) < 4: continue
                            if isinstance(obj, PoleComponent) and self.vy < 0: continue
                            self.move_mode, self.x = 'ladder', obj.x
                            break
            else: # Ladder mode
                self.x = support.x
                next_vy = dy
                from .environment import PoleComponent
                if isinstance(support, PoleComponent) and next_vy < 0: next_vy = 0
                
                # Find boundaries of the ladder/pole
                max_w_y = support.y
                for w in room.objects:
                    from .environment import WalkwayComponent
                    if isinstance(w, WalkwayComponent) and w.x <= support.x <= w.x + w.properties.get('length', 0) * 4:
                        if w.y >= support.y and w.y > max_w_y: max_w_y = w.y
                end_y = max_w_y if max_w_y > support.y else support.y + (support.properties['length'] * 8)
                
                self.y = max(support.y, min(end_y, self.y + next_vy))
                
                # Check for mode switch (Ladder -> Walkway)
                if abs(self.vx) > 0.1:
                    for obj in room.objects:
                        from .environment import WalkwayComponent
                        if isinstance(obj, WalkwayComponent) and abs(self.y - obj.y) < 4:
                            self.move_mode, self.y = 'walkway', obj.y
                            break
        
        # Friction
        self.vx *= 0.5
        self.vy *= 0.5

    def _find_support(self, room):
        if self.move_mode == 'walkway':
            for obj in room.objects:
                from .environment import WalkwayComponent
                if isinstance(obj, WalkwayComponent):
                    start_x, end_x = obj.x, obj.x + (obj.properties['length'] * 4)
                    if start_x <= self.x <= end_x and abs(self.y - obj.y) < 4:
                        return obj
        else:
            for obj in room.objects:
                from .environment import LadderComponent, PoleComponent
                if isinstance(obj, (LadderComponent, PoleComponent)):
                    start_y = obj.y
                    # Find bottom of ladder (next walkway)
                    max_w_y = start_y
                    for w in room.objects:
                        from .environment import WalkwayComponent
                        if isinstance(w, WalkwayComponent) and w.x <= obj.x <= w.x + w.properties.get('length', 0) * 4:
                            if w.y >= start_y and w.y > max_w_y: max_w_y = w.y
                    end_y = max_w_y if max_w_y > start_y else start_y + (obj.properties['length'] * 8)
                    if start_y <= self.y <= end_y and abs(self.x - obj.x) < 4:
                        return obj
        return None

    def _check_door_transition(self, engine, room, tick):
        from .door import DoorComponent
        for obj in room.objects:
            if isinstance(obj, DoorComponent) and obj.state == 2:
                if abs(self.x - (obj.x + 10)) < 16 and abs(self.y - (obj.y + 32)) < 16:
                    if obj.properties.get('is_exit'):
                        engine.state.victory = True
                        return
                    target_room_id, target_door_idx = obj.properties['link_room'], obj.properties['link_door']
                    target_room = engine.state.rooms.get(target_room_id)
                    if target_room:
                        target_doors = [t for t in target_room.objects if isinstance(t, DoorComponent)]
                        if 0 <= target_door_idx < len(target_doors):
                            tobj = target_doors[target_door_idx]
                            self.room_id, self.x, self.y = target_room_id, tobj.x + 10, tobj.y + 32
                            tobj.state, self.last_transition_tick = 2, tick
                            return

    def serialize(self):
        return {
            'id': self.id, 'x': self.x, 'y': self.y, 'room_id': self.room_id, 
            'keys': self.keys, 'is_moving': self.is_moving, 
            'is_acting': self.is_acting, 'is_teleporting': self.is_teleporting, 
            'facing_left': self.facing_left
        }
