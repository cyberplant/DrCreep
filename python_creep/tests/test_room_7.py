from tests.utils import assert_render_match

class TestRoom7:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 7, "tutorial_room_7a.png", tmp_path)
