from tests.utils import assert_render_match

class TestRoom2:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 2, "tutorial_room_2.png", tmp_path)
