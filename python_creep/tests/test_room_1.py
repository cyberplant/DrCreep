from tests.utils import assert_render_match

class TestRoom1:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 1, "tutorial_room_1a.png", tmp_path)

    def test_ladder_transition(self, engine):
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
