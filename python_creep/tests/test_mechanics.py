import pytest
from engine.parser import CastleParser
from engine.state import GameState
from engine.game import GameEngine

@pytest.fixture
def engine():
    # Use ZTUTORIAL for testing
    return GameEngine("run/data/castles/ZTUTORIAL", debug_mode=True)

def test_door_linking(engine):
    room0 = engine.state.rooms[0]
    door0 = next(o for o in room0.objects if o.type == 'door')
    
    # Simulate player entering door 0 in room 0
    player = engine.state.players[0]
    player.x, player.y = door0.x + 5, door0.y + 32
    player.move_mode = 'walkway'
    
    proposal = {
        'x': player.x, 'y': player.y, 'room_id': 0, 'move_mode': 'walkway',
        'commands': {'up': True}, 'has_support': True, 'keys': []
    }
    
    door0.process_proposal(engine, room0, player, proposal)
    
    assert proposal['room_id'] == door0.properties['link_room']
    assert proposal['x'] == engine.state.rooms[proposal['room_id']].objects[0].x + 5

def test_ladder_transition(engine):
    room1 = engine.state.rooms[1]
    ladder = next(o for o in room1.objects if o.type == 'ladder')
    
    player = engine.state.players[0]
    player.room_id = 1
    # Stand at top of ladder
    player.x, player.y = ladder.x, ladder.y
    player.move_mode = 'walkway'
    
    # Intent to go DOWN
    proposal = {
        'x': player.x, 'y': player.y + 4, 'room_id': 1, 'move_mode': 'walkway',
        'commands': {'down': True}, 'has_support': True, 'keys': []
    }
    
    ladder.process_proposal(engine, room1, player, proposal)
    
    assert proposal['move_mode'] == 'ladder'
    assert proposal['x'] == ladder.x

def test_trapdoor_blocking(engine):
    room = engine.state.rooms[5]
    trapdoor = next(o for o in room.objects if o.type == 'trapdoor')
    trapdoor.state = 1 # Open
    
    player = engine.state.players[0]
    player.room_id = 5
    # Walk over open trapdoor
    player.x, player.y = trapdoor.x + 4, trapdoor.y + 4
    
    proposal = {
        'x': player.x + 4, 'y': player.y, 'room_id': 5, 'move_mode': 'walkway',
        'commands': {'right': True}, 'has_support': True, 'keys': []
    }
    
    trapdoor.process_proposal(engine, room, player, proposal)
    
    # Support should be denied
    assert proposal['has_support'] == False
