from tests.utils import assert_render_match

class TestRoom10:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 10, "tutorial_room_10a.png", tmp_path)
