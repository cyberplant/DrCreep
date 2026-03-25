from .base import BaseComponent

class TextComponent(BaseComponent):
    def get_asset(self, tick):
        color_map = {0x1D: "white", 0x1E: "yellow", 0x1F: "cyan", 0x20: "green"}
        color = color_map.get(self.properties.get('color'), "white")
        return [f"[{color}]{self.properties.get('text', '')}[/]"]
