from .base import BaseComponent

class KeyComponent(BaseComponent):
    ASSET = ["[obj_color]k[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            player.keys.append(self.properties['color'])
            room.objects.remove(self)
    def get_asset(self, tick):
        return self.ASSET

class LockComponent(BaseComponent):
    ASSET = ["[obj_color]X[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            color = self.properties.get('color', 0)
            if color in player.keys:
                target_id = self.properties.get('target_door_idx')
                # Use duck typing or import DoorComponent locally if needed
                room_doors = [obj for obj in room.objects if obj.type == 'door']
                if 0 <= target_id < len(room_doors):
                    if room_doors[target_id].state == 0:
                        room_doors[target_id].state = 1
                        player.keys.remove(color)
    def get_asset(self, tick):
        return self.ASSET
