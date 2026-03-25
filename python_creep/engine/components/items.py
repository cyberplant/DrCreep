from .base import BaseComponent

class KeyComponent(BaseComponent):
    """
    Collectable key.
    - Interaction adds key color to player inventory and removes the component.
    """
    ASSET = ["[obj_color]k[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            player.keys.append(self.properties['color'])
            room.objects.remove(self)
    def get_asset(self, tick):
        return self.ASSET

class LockComponent(BaseComponent):
    """
    Key-operated lock for doors.
    - Consumes a matching key to trigger a door opening sequence.
    """
    ASSET = ["[obj_color]X[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            color = self.properties.get('color', 0)
            # Check if player has the matching key
            if color in player.keys:
                target_id = self.properties.get('target_door_idx')
                room_doors = [obj for obj in room.objects if obj.type == 'door']
                if 0 <= target_id < len(room_doors):
                    if room_doors[target_id].state == 0:
                        # Unlock door and consume key
                        room_doors[target_id].state = 1
                        player.keys.remove(color)
    def get_asset(self, tick):
        return self.ASSET
