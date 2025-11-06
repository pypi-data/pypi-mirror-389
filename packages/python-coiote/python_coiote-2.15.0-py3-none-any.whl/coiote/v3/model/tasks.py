from dataclasses import dataclass, field
from enum import auto
from typing import Optional, List, Dict, Union

from coiote.utils import AutoNamedEnum


@dataclass
class ReadDefinition:
    key: str


@dataclass
class ReadOperation:
    read: ReadDefinition

    @staticmethod
    def create(key: str):
        return ReadOperation(ReadDefinition(key))


@dataclass
class WriteDefinition:
    key: str
    value: str


@dataclass
class WriteOperation:
    write: WriteDefinition

    @staticmethod
    def create(key: str, value: str):
        return WriteOperation(WriteDefinition(key, value))


@dataclass
class ExecuteArg:
    digit: int
    argument: Optional[str] = None


@dataclass
class ExecuteDefinition:
    key: str
    argumentList: List[ExecuteArg] = field(default_factory=list)


@dataclass
class ExecuteOperation:
    execute: ExecuteDefinition

    @staticmethod
    def create(key: str, argumentList: List[ExecuteArg]):
        return ExecuteOperation(ExecuteDefinition(key, argumentList))


DeviceOperation = Union[ReadOperation, WriteOperation, ExecuteOperation]


@dataclass
class ConfigurationTaskDefinition:
    name: str
    batchRequests: bool = True
    executeImmediately: bool = True
    operations: List[DeviceOperation] = field(default_factory=list)


class TransferMethod(AutoNamedEnum):
    Pull = auto()
    Push = auto()


class TransferProtocol(AutoNamedEnum):
    HTTP = auto()
    HTTPS = auto()
    COAP = auto()
    COAPS = auto()
    COAP_TCP = auto()
    COAP_TLS = auto()


class UpgradeStrategy(AutoNamedEnum):
    ObservationTrigger = auto()
    WithoutObservations = auto()
    ObservationBased = auto()
    SendBased = auto()


@dataclass
class TaskParameter:
    name: str
    value: str


@dataclass
class TaskConfig:
    taskName: str
    parameters: List[TaskParameter]
    properties: Dict[str, str]
    isActive: Optional[bool] = False


@dataclass
class Task:
    id: str
    config: TaskConfig
