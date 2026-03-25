from .base import BaseComponent

class WalkwayComponent(BaseComponent):
    """
    Horizontal platform for players and entities.
    - length: Number of tiles the walkway covers (each tile is 4 pixels wide).
    """
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)

class LadderComponent(BaseComponent):
    """
    Vertical movement structure.
    - Allows players to climb up and down.
    """
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)

class PoleComponent(BaseComponent):
    """
    Vertical slide structure.
    - Allows players to slide DOWN only.
    """
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)
