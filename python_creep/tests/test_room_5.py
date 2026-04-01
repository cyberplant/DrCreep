from tests.utils import assert_render_match

class TestRoom5:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 5, "tutorial_room_5a.png", tmp_path)
