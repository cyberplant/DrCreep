from .walkway import WalkwayComponent
from .ladder import LadderComponent, PoleComponent
from .door import DoorComponent, DoorbellComponent
from .trapdoor import TrapdoorComponent, TrapdoorSwitchComponent
from .conveyor import ConveyorComponent, ConveyorSwitchComponent
from .raygun import RaygunComponent, RaygunSwitchComponent
from .lightning import LightningMachineComponent, LightningSwitchComponent
from .forcefield import ForcefieldComponent, ForcefieldSwitchComponent
from .mummy import MummyReleaseComponent, MummyTombComponent
from .frankie import FrankieComponent
from .teleport import TeleportComponent, TeleportTargetComponent
from .items import KeyComponent, LockComponent
from .text import TextComponent
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
