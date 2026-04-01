from tests.utils import assert_render_match

class TestRoom4:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 4, "tutorial_room_4a.png", tmp_path)
