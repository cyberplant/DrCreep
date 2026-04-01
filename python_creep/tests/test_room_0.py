from tests.utils import assert_render_match

class TestRoom0:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 0, "tutorial_room_0.png", tmp_path)

    def test_door_linking(self, engine):
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
        
        assert getattr(engine.state, 'transition', None) is not None
        assert engine.state.transition['to_room'] == door0.properties['link_room']

    def test_map_view_rendering(self, engine, renderer, tmp_path):
        """Scenario test: Trigger a transition to show the map, then render it."""
        player = engine.state.players[0]
        door = [o for o in engine.state.rooms[0].objects if o.type == 'door'][0]
        player.room_id = 0
        player.x = door.x + 5
        player.y = door.y + 32
        
        engine.handle_input(0, {'up': True})
        engine._update()
        # Call update once more so the transition logic runs and logs the debug
        engine._update()
        
        assert engine.state.transition is not None
        
        from tests.utils import verify_not_black
        state_dict = engine.get_state_dict()
        surface = renderer.render_state(state_dict)
        # Check that map is not black
        import pygame
        from PIL import Image
        rendered_path = tmp_path / "map_view.png"
        pygame.image.save(surface, str(rendered_path))
        img = Image.open(rendered_path).convert("RGB")
        verify_not_black(img, "Rendered map view")
