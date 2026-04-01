from tests.utils import assert_render_match

class TestRoom11:
    def test_render(self, engine, renderer, tmp_path):
        assert_render_match(engine, renderer, 11, "tutorial_room_11a.png", tmp_path)
