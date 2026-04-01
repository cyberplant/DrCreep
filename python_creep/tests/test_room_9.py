from tests.utils import assert_render_match

class TestRoom9:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 9, "tutorial_room_9a.png", tmp_path)

    def test_trapdoor_blocking(self, engine):
        room = engine.state.rooms[9]
        trapdoor = next(o for o in room.objects if o.type == 'trapdoor')
        trapdoor.state = 1 # Open
        
        player = engine.state.players[0]
        player.room_id = 9
        # Walk over open trapdoor
        player.x, player.y = trapdoor.x + 4, trapdoor.y + 4
        
        proposal = {
            'x': player.x + 4, 'y': player.y, 'room_id': 9, 'move_mode': 'walkway',
            'commands': {'right': True}, 'has_support': True, 'keys': []
        }
        
        trapdoor.process_proposal(engine, room, player, proposal)
        
        # Support should be denied
        assert proposal['has_support'] == False
