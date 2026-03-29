from .base import BaseComponent

class TextComponent(BaseComponent):
    """
    Informational text displayed in the room.
    """
    def __init__(self, data):
        super().__init__(data)
        self.text = data.get('text', "")
        self.font = data.get('font', 0)

    def get_asset(self, tick):
        # Map C64-style color codes to human-readable names for ASCII fallback
        return [f"[white]{self.text}[/]"]
