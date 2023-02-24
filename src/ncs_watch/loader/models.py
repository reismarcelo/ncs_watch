from typing import Dict
from enum import Enum
from ipaddress import IPv4Address
from pydantic import BaseModel, Extra


class DeviceTypeOptions(str, Enum):
    cisco_xr_telnet = 'cisco_xr_telnet'
    cisco_xr = 'cisco_xr'


class DeviceConfigModel(BaseModel, extra=Extra.forbid, use_enum_values=True):
    address: IPv4Address
    device_type: DeviceTypeOptions = DeviceTypeOptions.cisco_xr


class GlobalsConfigModel(BaseModel, extra=Extra.forbid):
    timeout_std: float = 30.0
    timeout_ext: float = 120.0


#
# Top-level ConfigModel
#

class ConfigModel(BaseModel, extra=Extra.forbid):
    globals: GlobalsConfigModel
    devices: Dict[str, DeviceConfigModel]
