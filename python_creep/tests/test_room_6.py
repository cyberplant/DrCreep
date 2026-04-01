from tests.utils import assert_render_match

class TestRoom6:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 6, "tutorial_room_6.png", tmp_path)
