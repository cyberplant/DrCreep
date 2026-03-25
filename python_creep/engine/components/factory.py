from .environment import (
    DoorComponent, WalkwayComponent, LadderComponent, 
    PoleComponent, TrapdoorComponent, ConveyorComponent
)
from .interactive import (
    TeleportComponent, TeleportTargetComponent, 
    KeyComponent, LockComponent, TextComponent
)
from .hazards import (
    ForcefieldComponent, LightningMachineComponent, RaygunComponent
)
from .switches import (
    DoorbellComponent, LightningSwitchComponent, ForcefieldSwitchComponent,
    TrapdoorSwitchComponent, ConveyorSwitchComponent, RaygunSwitchComponent
)
from .entities import (
    MummyReleaseComponent, MummyTombComponent, FrankieComponent
)
from .base import BaseComponent

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
