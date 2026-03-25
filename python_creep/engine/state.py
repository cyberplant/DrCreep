from .parser import RoomData

class Player:
    def __init__(self, id, start_x, start_y):
        self.id = id
        self.x = start_x
        self.y = start_y
        self.vx = 0
        self.vy = 0
        self.lives = 3
        self.keys = [] # list of key colors
        self.anim_state = "idle"
        self.room_id = 0
        self.facing_left = False
        self.move_mode = 'walkway' # 'walkway' or 'ladder'
        self.last_transition_tick = 0
        self.is_teleporting = 0
        self.target_room_id = 0
        self.target_x = 0
        self.target_y = 0

class GameObject:
    def __init__(self, data):
        self.type = data['type']
        self.x = data['x']
        self.y = data['y']
        self.properties = data
        self.active = True
        self.state = 0 # generic state (e.g. door open/close)
        self.timer = 0
        self.max_timer = 0

class RoomState:
    def __init__(self, room_data: RoomData):
        self.id = room_data.number
        self.objects = [GameObject(o) for o in room_data.objects]
        self.map_x = room_data.map_x
        self.map_y = room_data.map_y

class GameState:
    def __init__(self, castle_parser):
        self.castle_name = castle_parser.name
        self.rooms = {r.number: RoomState(r) for r in castle_parser.rooms}
        self.players = []
        self.mummies = []
        self.frankies = []
        self.projectiles = []
        self.current_tick = 0
        self.victory = False
        
    def add_player(self, id, start_room_id, start_x, start_y):
        p = Player(id, start_x, start_y)
        p.room_id = start_room_id
        self.players.append(p)
        return p
