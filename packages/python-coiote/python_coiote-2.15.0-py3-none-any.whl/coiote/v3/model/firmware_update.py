from dataclasses import dataclass, field
from datetime import datetime
from enum import auto
from typing import Optional, Dict, List, Union

from coiote.utils import AutoNamedEnum


class FirmwareUpdateKind(str, AutoNamedEnum):
    BasicFota = auto()
    MulticomponentFota = auto()
class FirmwareDeliveryMethod(str, AutoNamedEnum):
     Push = auto()
     Pull = auto()

@dataclass
class FirmwareTransferConfig:
    deliveryMethod: FirmwareDeliveryMethod
    protocol: Optional[str] = None
    uriFormat: Optional[str] = None

    @staticmethod
    def pull(protocol: str = "COAPS", uriFormat: str = "DNS"):
        return FirmwareTransferConfig(FirmwareDeliveryMethod.Pull, protocol, uriFormat)
    
    @staticmethod
    def push():
        return FirmwareTransferConfig(FirmwareDeliveryMethod.Push)


@dataclass
class BasicFirmwareUpdateExecutionConfig:
    resourceId: str
    transfer: FirmwareTransferConfig
    version: Optional[str] = None
    timeout: str = "10m"
    fotaTaskBlocking: bool = True
    kind: FirmwareUpdateKind = field(default=FirmwareUpdateKind.BasicFota, init=False)

@dataclass
class MulticomponentFirmwareUpdateExecutionConfig:
    pass

FirmwareUpdateExecutionConfig = Union[BasicFirmwareUpdateExecutionConfig, MulticomponentFirmwareUpdateExecutionConfig]

@dataclass
class FirmwareUpdateConfigCreateRequest:
    name: str
    execution: FirmwareUpdateExecutionConfig
    description: Optional[str] = None
    visibleInSubDomains: Optional[bool] = True

FirmwareConfigId = str

@dataclass
class FirmwareUpdateConfigCreated:
    id: FirmwareConfigId
    message: Optional[str] = None

@dataclass
class FirmwareUpdateConfig:
    id: FirmwareConfigId
    name: str
    domainId: str
    execution: FirmwareUpdateExecutionConfig
    description: Optional[str] = None
    visibleInSubDomains: Optional[bool] = True

@dataclass
class ScheduledBasicFirmwareInfo:
    id: str
    message: str