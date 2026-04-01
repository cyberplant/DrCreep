from tests.utils import assert_render_match

class TestRoom3:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 3, "tutorial_room_3a.png", tmp_path)

    def test_lightning_interaction(self, engine, renderer, tmp_path):
        """
        Scenario test:
        1. Start in Room 3 (lightning room) on the bottom walkway (y=192).
        2. Move into lightning beam (x=100) -> Player should die.
        3. Respawn, move to switch (x=72), turn off lightning.
        4. Move into lightning beam -> Player should survive.
        """
        player = engine.state.players[0]
        player.room_id = 3
        player.x = 20
        player.y = 192
        
        # Step 1: Walk into lightning machine at x=100
        for _ in range(120): # Enough steps to reach x=100
            engine.handle_input(0, {'right': True})
            engine._update()
            if player.room_id == 0:
                break
        
        assert player.room_id == 0, f"Player did not die at lightning! Room: {player.room_id}, x: {player.x}"
        
        # Step 2: Set back to room 3 at switch (x=72, y=192)
        player.room_id = 3
        player.x = 72
        player.y = 192
        
        # Toggle switch
        engine.handle_input(0, {'action': True})
        engine._update()
        
        # Verify lightning is off
        assert engine.room_states[3]['lightning'][0] == False
        
        # Step 3: Walk back into lightning at x=100
        for _ in range(50):
            engine.handle_input(0, {'right': True})
            engine._update()
            
        assert player.room_id == 3
        assert player.x > 100
        
        # Step 4: Render
        import pygame
        from PIL import Image
        state_dict = engine.get_state_dict()
        surface = renderer.render_state(state_dict)
        rendered_path = tmp_path / "lightning_off.png"
        pygame.image.save(surface, str(rendered_path))
        img = Image.open(rendered_path).convert("RGB")
        extrema = img.convert("L").getextrema()
        assert extrema[1] > 0, "Rendered lightning room is all black!"
