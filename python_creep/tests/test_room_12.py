from tests.utils import assert_render_match

class TestRoom12:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 12, "tutorial_room_12.png", tmp_path)
