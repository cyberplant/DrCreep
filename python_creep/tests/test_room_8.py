from tests.utils import assert_render_match

class TestRoom8:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 8, "tutorial_room_8.png", tmp_path)
