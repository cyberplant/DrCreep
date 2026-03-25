from .base import BaseComponent

class WalkwayComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)

class LadderComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)

class PoleComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.length = data.get('length', 0)
