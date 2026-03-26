from .base import BaseComponent

class TextComponent(BaseComponent):
    """
    Informational text displayed in the room.
    - Colors are mapped from binary data to standard ASCII colors.
    """
    def get_asset(self, tick):
        # Map C64-style color codes to human-readable names
        color_map = {0x1D: "white", 0x1E: "yellow", 0x1F: "cyan", 0x20: "green"}
        color = color_map.get(self.properties.get('color'), "white")
        return [f"[{color}]{self.properties.get('text', '')}[/]"]
