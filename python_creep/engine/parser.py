import struct
import os

# Object IDs
E_OBJECT_DOOR = 0x0803
E_OBJECT_WALKWAY = 0x0806
E_OBJECT_SLIDING_POLE = 0x0809
E_OBJECT_LADDER = 0x080C
E_OBJECT_DOOR_BELL = 0x080F
E_OBJECT_LIGHTNING = 0x0812
E_OBJECT_FORCEFIELD = 0x0815
E_OBJECT_MUMMY = 0x0818
E_OBJECT_KEY = 0x081B
E_OBJECT_LOCK = 0x081E
E_OBJECT_RAY_GUN = 0x0824
E_OBJECT_TELEPORT = 0x0827
E_OBJECT_TRAP_DOOR = 0x082A
E_OBJECT_CONVEYOR = 0x082D
E_OBJECT_FRANKENSTEIN = 0x0830
E_OBJECT_TEXT = 0x0833
E_OBJECT_IMAGE = 0x0836

VALID_IDS = {
    E_OBJECT_DOOR, E_OBJECT_WALKWAY, E_OBJECT_SLIDING_POLE, E_OBJECT_LADDER,
    E_OBJECT_DOOR_BELL, E_OBJECT_LIGHTNING, E_OBJECT_FORCEFIELD, E_OBJECT_MUMMY,
    E_OBJECT_KEY, E_OBJECT_LOCK, E_OBJECT_RAY_GUN,
    E_OBJECT_TELEPORT, E_OBJECT_TRAP_DOOR, E_OBJECT_CONVEYOR, E_OBJECT_FRANKENSTEIN,
    E_OBJECT_TEXT, E_OBJECT_IMAGE, 0x160A, 0x2A6D, 0x0839, 0x0821
}

class RoomData:
    def __init__(self, number):
        self.number = number
        self.color = 0
        self.map_x = 0
        self.map_y = 0
        self.map_width = 0
        self.map_height = 0
        self.objects = []

class CastleParser:
    def __init__(self, filepath):
        self.name = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            self.data = f.read()
        self.rooms = []
        self._parse_header()

    def _read_word(self, offset):
        if offset + 2 > len(self.data): return None
        return struct.unpack("<H", self.data[offset:offset+2])[0]

    def _parse_header(self):
        offset = 0x102
        dir_entries = []
        while offset < len(self.data):
            marker = self.data[offset]
            if marker == 0xFF: break
            ptr = self._read_word(offset + 6)
            if ptr < 0x7800: break
            
            room = RoomData(len(self.rooms))
            room.color = self.data[offset]
            room.map_x = self.data[offset+1]
            room.map_y = self.data[offset+2]
            size_byte = self.data[offset+3]
            room.map_height = (size_byte & 7)
            room.map_width = (size_byte >> 3) & 7
            room.file_dir_ptr = ptr - 0x7800 + 2
            
            self.rooms.append(room)
            dir_entries.append(room.file_dir_ptr)
            offset += 8
        
        dir_entries.sort()
        for room in self.rooms:
            end_offset = len(self.data)
            for entry in dir_entries:
                if entry > room.file_dir_ptr:
                    end_offset = entry
                    break
            self._parse_room_objects(room, end_offset)

    def _parse_room_objects(self, room, end_offset):
        offset = room.file_dir_ptr
        lightning_sys_id = 0
        while offset < end_offset - 1:
            func = self._read_word(offset)
            if func not in VALID_IDS:
                offset += 1
                continue
            
            offset += 2
            if func == E_OBJECT_DOOR:
                count = self.data[offset]; offset += 1
                for _ in range(count):
                    x, y = self.data[offset], self.data[offset+1]
                    direction, link_room, link_door = self.data[offset+2], self.data[offset+3], self.data[offset+4]
                    is_exit = self.data[offset+7] != 0
                    room.objects.append({
                        'type': 'door', 'x': x, 'y': y, 
                        'direction': direction, 'link_room': link_room, 
                        'link_door': link_door, 'is_exit': is_exit
                    })
                    offset += 8
            elif func == E_OBJECT_DOOR_BELL:
                count = self.data[offset]; offset += 1
                for _ in range(count):
                    x, y, target_door_idx = self.data[offset], self.data[offset+1], self.data[offset+2]
                    room.objects.append({'type': 'doorbell', 'x': x, 'y': y, 'target_door_idx': target_door_idx})
                    offset += 3
            elif func in [E_OBJECT_WALKWAY, E_OBJECT_SLIDING_POLE, E_OBJECT_LADDER]:
                name = {E_OBJECT_WALKWAY: 'walkway', E_OBJECT_SLIDING_POLE: 'pole', E_OBJECT_LADDER: 'ladder'}[func]
                while self.data[offset] != 0:
                    if self._read_word(offset) in VALID_IDS: break
                    length, x, y = self.data[offset], self.data[offset+1], self.data[offset+2]
                    room.objects.append({'type': name, 'x': x, 'y': y, 'length': length})
                    offset += 3
                offset += 1
            elif func == E_OBJECT_LIGHTNING:
                # Group machines by the switch preceding them
                current_sys = 0
                while self.data[offset] != 0x20:
                    if self._read_word(offset) in VALID_IDS: break
                    mode, x, y = self.data[offset], self.data[offset+1], self.data[offset+2]
                    if mode & 0x80:
                        current_sys += 1
                        room.objects.append({'type': 'lightning_switch', 'x': x, 'y': y, 'system_id': current_sys})
                    else:
                        length = self.data[offset+3]
                        room.objects.append({'type': 'lightning_machine', 'x': x, 'y': y, 'length': length, 'system_id': current_sys})
                    offset += 8
                offset += 1
            elif func == E_OBJECT_TELEPORT:
                x, y, target = self.data[offset], self.data[offset+1], self.data[offset+2]
                color = (target + 2) % 16
                room.objects.append({'type': 'teleport', 'x': x, 'y': y, 'target': target, 'color': color})
                offset += 3
                while self.data[offset] != 0:
                    if self._read_word(offset) in VALID_IDS: break
                    tx, ty = self.data[offset], self.data[offset+1]
                    room.objects.append({'type': 'teleport_target', 'x': tx, 'y': ty, 'color': color})
                    offset += 2
                offset += 1
            elif func == E_OBJECT_KEY:
                while self.data[offset] != 0:
                    if self._read_word(offset) in VALID_IDS: break
                    color, x, y = self.data[offset], self.data[offset+2], self.data[offset+3]
                    room.objects.append({'type': 'key', 'x': x, 'y': y, 'color': color})
                    offset += 4
                offset += 1
            elif func == E_OBJECT_MUMMY:
                while self.data[offset] != 0:
                    if self._read_word(offset) in VALID_IDS: break
                    x, y = self.data[offset+1], self.data[offset+2]
                    room.objects.append({'type': 'mummy', 'x': x, 'y': y})
                    offset += 3
                offset += 1
            elif func == E_OBJECT_LOCK:
                while self.data[offset] != 0:
                    if self._read_word(offset) in VALID_IDS: break
                    x, y = self.data[offset], self.data[offset+1]
                    room.objects.append({'type': 'lock', 'x': x, 'y': y})
                    offset += 2
                offset += 1
            elif func in [E_OBJECT_TEXT, 0x2A6D, 0x0839]:
                while self.data[offset] != 0:
                    if self._read_word(offset) in VALID_IDS: break
                    x, y, col = self.data[offset], self.data[offset+1], self.data[offset+2]
                    offset += 4
                    text = ""
                    while True:
                        if offset >= len(self.data): break
                        c = self.data[offset]; text += chr(c & 0x7F); offset += 1
                        if c & 0x80: break
                    room.objects.append({'type': 'text', 'x': x, 'y': y, 'text': text, 'color': col})
                offset += 1
            elif func in [E_OBJECT_RAY_GUN, E_OBJECT_TRAP_DOOR, E_OBJECT_CONVEYOR, E_OBJECT_FRANKENSTEIN]:
                name = {E_OBJECT_RAY_GUN: 'raygun', E_OBJECT_TRAP_DOOR: 'trapdoor', E_OBJECT_CONVEYOR: 'conveyor', E_OBJECT_FRANKENSTEIN: 'frankie'}[func]
                while self.data[offset] != 0x80:
                    if self._read_word(offset) in VALID_IDS: break
                    room.objects.append({'type': name, 'x': self.data[offset+1], 'y': self.data[offset+2]})
                    offset += 7 if func in [E_OBJECT_RAY_GUN, E_OBJECT_FRANKENSTEIN] else 5
                offset += 1
