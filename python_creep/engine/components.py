
class BaseComponent:
    def __init__(self, data):
        self.type = data.get('type')
        self.x = data.get('x', 0)
        self.y = data.get('y', 0)
        self.state = 0
        self.timer = 0
        self.max_timer = 0
        self.active = True
        self.properties = data

    def update(self, engine, room, tick):
        pass

    def on_collide(self, engine, room, entity):
        pass
        
    def on_interact(self, engine, room, player, commands):
        pass

    def get_asset(self, tick):
        return None

    def serialize(self, tick=0):
        res = {
            'type': self.type,
            'x': self.x,
            'y': self.y,
            'state': self.state,
            'timer': self.timer,
            'max_timer': self.max_timer,
            'properties': self.properties,
            'asset_frame': self.get_asset(tick)
        }
        return res

class DoorComponent(BaseComponent):
    ASSET = [
               [ # Closed
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white]----------"
            ],
               [ # Partial 1
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][[yellow]________[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ],
               [ # Partial 2
                "[white]----------[/]",
                "[white][░░░░░░░░][/]",
                "[white][░░░░░░░░][/]",
                "[white][[yellow]________[/]][/]",
                "[white][  [next_room_color]/░░░░░[/]][/]",
                "[white][ [next_room_color]/______[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ],
               [ # Open
                "[white]----------[/]",
                "[white][     [next_room_color]___[/]][/]",
                "[white][    [next_room_color]/░░░[/]][/]",
                "[white][   [next_room_color]/____[/]][/]",
                "[white][  [next_room_color]/░░░░░[/]][/]",
                "[white][ [next_room_color]/______[/]][/]",
                "[white][[next_room_color]/░░░░░░░[/]][/]",
                "[white]----------"
            ]
        ]

    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=closed, 1=opening, 2=open

    def update(self, engine, room, tick):
        if 0 < self.state < 2:
            if tick % 10 == 0:
                self.state += 1

    def get_asset(self, tick):
        if self.state == 0: return self.ASSET[0]
        if self.state == 2: return self.ASSET[-1]
        # For state 1, we could animate more if we had more frames, 
        # but let's just pick one of the partials based on some timer or just stick to one.
        return self.ASSET[1]

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

class TrapdoorComponent(BaseComponent):
    STATES = {
        0: ["[white]__________[/]"], # Closed
        1: ["[white]          [/]"]  # Open (Hole)
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1 if data.get('is_open') else 0

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[0])

class ConveyorComponent(BaseComponent):
    ASSETS = {
        "left": [
            [r"[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[/]"],
            [r"[blue][gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~[blue][/]"],
            [r"[blue][gray]~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue]\[gray]~~[blue][/]"],
        ],
        "right": [
            ["[blue]/  /  /  / [/]"],
            ["[blue] /  /  /  /[/]"],
            ["[blue]  /  /  /  [/]"],
        ],
        "off": [["[blue]~~~~~~~~~~~~[/]"]]
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = data.get('state', 1)

    def get_asset(self, tick):
        if self.state == 0: # LEFT
            frames = self.ASSETS["left"]
            return frames[(tick // 4) % len(frames)]
        elif self.state == 2: # RIGHT
            frames = self.ASSETS["right"]
            return frames[(tick // 4) % len(frames)]
        else:
            return self.ASSETS["off"]

class RaygunComponent(BaseComponent):
    ASSET = ["[red]>====>[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.initial_y = self.y
        self.direction = 1

    def update(self, engine, room, tick):
        if self.timer > 0:
            self.timer -= 1
        if tick % 2 == 0:
            self.y += self.direction * 1
            if self.y >= self.initial_y + 32:
                self.direction = -1
            elif self.y <= self.initial_y:
                self.direction = 1

    def on_collide(self, engine, room, entity):
        if abs(entity.y - self.y) < 16 and self.timer == 0:
            self.timer = 100
            direction = 1 if entity.x > self.x else -1
            engine.state.projectiles.append({'x': self.x + (16*direction), 'y': self.y, 'vx': 3.0 * direction, 'room_id': entity.room_id})

    def get_asset(self, tick):
        return self.ASSET

class ForcefieldComponent(BaseComponent):
    STATES = {
        0: ["[cyan]z[/]", " ", " ", " ", " ", " ", " ", " "],
        1: ["[cyan]z[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]", "[cyan].[/]"]
    }
    def __init__(self, data):
        super().__init__(data)
        self.state = 1

    def get_asset(self, tick):
        return self.STATES.get(self.state, self.STATES[1])

class ForcefieldSwitchComponent(BaseComponent):
    ASSET = ["[cyan]S[/]"]
    def update(self, engine, room, tick):
        if self.timer > 0:
            if tick % engine.ticks_per_second == 0:
                self.timer -= 1
                if self.timer == 0:
                    for obj in room.objects:
                        if isinstance(obj, ForcefieldComponent):
                            obj.state = 1

    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            self.timer = 8
            for fobj in room.objects:
                if isinstance(fobj, ForcefieldComponent):
                    fobj.state = 0

    def get_asset(self, tick):
        return self.ASSET

class LightningMachineComponent(BaseComponent):
    ASSET = ["[cyan](O)[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)

    def on_collide(self, engine, room, entity):
        if engine.room_states[entity.room_id]['lightning'].get(self.system_id):
            if abs(entity.x - (self.x + 2)) < 12 and self.y <= entity.y <= self.y + 160:
                engine._reset_player(entity)

    def get_asset(self, tick):
        return self.ASSET

class LightningSwitchComponent(BaseComponent):
    ASSET = ["[cyan][[yellow]T[/]][/]"]
    def __init__(self, data):
        super().__init__(data)
        self.system_id = data.get('system_id', 0)
        self.targets = data.get('targets', [])

    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            if player.room_id == 4:
                self.timer = 8
                for fobj in room.objects:
                    if isinstance(fobj, ForcefieldComponent):
                        fobj.state = 0
            else:
                sid = self.system_id
                targets = self.targets
                rs = engine.room_states[player.room_id]['lightning']
                if sid not in rs: rs[sid] = True
                rs[sid] = not rs[sid]
                for tid in targets:
                    if tid != 0xFF: rs[tid] = rs[sid]

    def get_asset(self, tick):
        return self.ASSET

class MummyReleaseComponent(BaseComponent):
    ASSET = ["[white]M[/]"]
    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=sleeping, 1=released

    def on_collide(self, engine, room, entity):
        if self.state == 0:
            if abs(entity.x - self.x) < 16 and abs((entity.y - 16) - self.y) < 32:
                self.state = 1
                engine.state.mummies.append({'x': self.properties['tomb_x'] + 12, 'y': self.properties['tomb_y'] + 32, 'room_id': entity.room_id, 'is_moving': False})

    def get_asset(self, tick):
        return self.ASSET

class MummyTombComponent(BaseComponent):
    ASSET = [
        "[red]#####[/]",
        "[red]#####[/]",
        "[red]#####[/]"
    ]
    def get_asset(self, tick):
        return self.ASSET

class FrankieComponent(BaseComponent):
    def __init__(self, data):
        super().__init__(data)
        self.state = 0 # 0=sleeping, 1=released

    def on_collide(self, engine, room, entity):
        if self.state == 0:
            if abs(entity.y - (self.y + 32)) < 24:
                self.state = 1
                engine.state.frankies.append({'x': self.x + 12, 'y': self.y + 32, 'room_id': entity.room_id, 'vx': 0.5, 'is_moving': True})

class TeleportComponent(BaseComponent):
    TEMPLATE = [
        "[obj_color]======[/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]",
        "[obj_color][    ][/]"
    ]
    def __init__(self, data):
        super().__init__(data)
        self.state = data.get('target', 0) # Use target as state for color rotation

    def on_interact(self, engine, room, player, commands):
        target_colors = sorted(list(set(o.properties['color'] for o in room.objects if isinstance(o, TeleportTargetComponent))))
        if not target_colors: target_colors = [0]
        cur_idx = target_colors.index(self.state) if self.state in target_colors else 0
        if commands.get('up'):
            self.state = target_colors[(cur_idx - 1) % len(target_colors)]
            return
        if commands.get('down'):
            self.state = target_colors[(cur_idx + 1) % len(target_colors)]
            return
        
        if commands.get('action'):
            tc = self.state
            for rid, rstate in engine.state.rooms.items():
                for tobj in rstate.objects:
                    if isinstance(tobj, TeleportTargetComponent) and tobj.properties['color'] == tc:
                        player.is_teleporting = 20
                        player.target_room_id = rid
                        player.target_x, player.target_y = tobj.x, tobj.y + 32
                        return

    def get_asset(self, tick):
        # We need to inject the color into the template
        # The client normally does this via [obj_color] replacement.
        # Here we could pre-replace it if we knew the color name.
        # For now, let's keep the markup and let the client handle [obj_color].
        return self.TEMPLATE

class TeleportTargetComponent(BaseComponent):
    ASSET = ["[obj_color]●[/]"]
    def get_asset(self, tick):
        return self.ASSET

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
                room_doors = [obj for obj in room.objects if isinstance(obj, DoorComponent)]
                if 0 <= target_id < len(room_doors):
                    if room_doors[target_id].state == 0:
                        room_doors[target_id].state = 1
                        player.keys.remove(color)
    def get_asset(self, tick):
        return self.ASSET

class TextComponent(BaseComponent):
    def get_asset(self, tick):
        color_map = {0x1D: "white", 0x1E: "yellow", 0x1F: "cyan", 0x20: "green"}
        color = color_map.get(self.properties.get('color'), "white")
        return [f"[{color}]{self.properties.get('text', '')}[/]"]

class TrapdoorSwitchComponent(BaseComponent):
    ASSET = ["[cyan]o[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_idx')
            if 0 <= target_id < len(room.objects):
                t_obj = room.objects[target_id]
                t_obj.state = 1 if t_obj.state == 0 else 0
    def get_asset(self, tick):
        return self.ASSET

class ConveyorSwitchComponent(BaseComponent):
    ASSET = ["[cyan]o[/]"] # Using same as trapdoor switch for now
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_idx')
            if 0 <= target_id < len(room.objects):
                c_obj = room.objects[target_id]
                states = [0, 1, 2, 1]
                cur_idx = states.index(c_obj.state) if c_obj.state in states else 1
                c_obj.state = states[(cur_idx + 1) % 4]
    def get_asset(self, tick):
        return self.ASSET

class RaygunSwitchComponent(BaseComponent):
    ASSET = [
            " [cyan]^[/] ",
            " [cyan]O[/] ",
            " [cyan]v[/] "
        ]
    def on_interact(self, engine, room, player, commands):
        for rgun in room.objects:
            if isinstance(rgun, RaygunComponent):
                if commands.get('up'): rgun.y -= 2; return
                if commands.get('down'): rgun.y += 2; return
                if commands.get('action'):
                    if rgun.timer == 0:
                        rgun.timer = 100
                        engine.state.projectiles.append({'x': rgun.x + 16, 'y': rgun.y, 'vx': 3.0, 'room_id': player.room_id})
                    return
    def get_asset(self, tick):
        return self.ASSET

class DoorbellComponent(BaseComponent):
    ASSET = ["[white]●[/]"]
    def on_interact(self, engine, room, player, commands):
        if commands.get('action'):
            target_id = self.properties.get('target_door_idx')
            room_doors = [obj for obj in room.objects if isinstance(obj, DoorComponent)]
            if 0 <= target_id < len(room_doors):
                if room_doors[target_id].state == 0:
                    room_doors[target_id].state = 1
    def get_asset(self, tick):
        return self.ASSET

COMPONENT_MAP = {
    'door': DoorComponent,
    'walkway': WalkwayComponent,
    'ladder': LadderComponent,
    'pole': PoleComponent,
    'trapdoor': TrapdoorComponent,
    'conveyor': ConveyorComponent,
    'raygun': RaygunComponent,
    'forcefield': ForcefieldComponent,
    'forcefield_switch': ForcefieldSwitchComponent,
    'lightning_machine': LightningMachineComponent,
    'lightning_switch': LightningSwitchComponent,
    'mummy_release': MummyReleaseComponent,
    'mummy_tomb': MummyTombComponent,
    'frankie': FrankieComponent,
    'teleport': TeleportComponent,
    'teleport_target': TeleportTargetComponent,
    'key': KeyComponent,
    'lock': LockComponent,
    'text': TextComponent,
    'trapdoor_switch': TrapdoorSwitchComponent,
    'conveyor_switch': ConveyorSwitchComponent,
    'raygun_switch': RaygunSwitchComponent,
    'doorbell': DoorbellComponent,
}

def create_component(data):
    ctype = data.get('type')
    cls = COMPONENT_MAP.get(ctype, BaseComponent)
    return cls(data)
