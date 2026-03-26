from .parser import RoomData
from .components import create_component
from .components.player import Player

class RoomState:
    def __init__(self, room_data: RoomData):
        self.id = room_data.number
        self.color = room_data.color
        self.objects = [create_component(o) for o in room_data.objects]
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
