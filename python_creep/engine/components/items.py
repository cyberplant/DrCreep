from .base import BaseComponent

class KeyComponent(BaseComponent):
    """Collectable key."""
    ASSET = ["[obj_color]k[/]"]
    def process_proposal(self, engine, room, current_state, proposal):
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            if proposal.get('commands', {}).get('action'):
                proposal['keys'] = proposal.get('keys', []) + [self.properties['color']]
                room.objects.remove(self)
    def get_asset(self, tick):
        return self.ASSET

class LockComponent(BaseComponent):
    """Key-operated lock for doors."""
    ASSET = ["[obj_color]X[/]"]
    def process_proposal(self, engine, room, current_state, proposal):
        dist_x, dist_y = abs(proposal['x'] - self.x), abs((proposal['y'] - 16) - self.y)
        if dist_x < 16 and dist_y < 48:
            if proposal.get('commands', {}).get('action'):
                color = self.properties.get('color', 0)
                if color in proposal.get('keys', []):
                    target_id = self.properties.get('target_door_idx')
                    room_doors = [obj for obj in room.objects if obj.type == 'door']
                    if 0 <= target_id < len(room_doors):
                        if room_doors[target_id].state == 0:
                            # Unlock door and consume key in proposal
                            room_doors[target_id].state = 1
                            proposal['keys'].remove(color)

        return self.ASSET
