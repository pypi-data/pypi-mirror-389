from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Union

from coiote.utils import AutoNamedEnum


class HandlerType(str, AutoNamedEnum):
    Kafka = "kafka"
    Webhook = "webhook"


class DeviceLifecycleEventType(str, AutoNamedEnum):
    Created = "deviceCreated"
    FirstRegistration = "deviceFirstRegistration"
    UpdatedViaWrite = "deviceUpdatedViaWrite"
    UpdatedViaFota = "deviceUpdatedViaFota"
    Deleted = "deviceDeleted"


@dataclass
class TelemetryEventHandlerFilter:
    lwm2mUrls: List[str]
    type: str = "telemetry"


@dataclass
class LifecycleEventHandlerFilter:
    eventTypes: List[DeviceLifecycleEventType]
    type: str = "lifecycle"


EventHandlerFilter = Union[TelemetryEventHandlerFilter,
                           LifecycleEventHandlerFilter]


@dataclass
class EventHandlerUpdateData:
    name: Optional[str] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None
    filter: Optional[EventHandlerFilter] = None
    connectionConfig: Optional[dict] = None


@dataclass
class BasicAuth:
    user: str
    password: str
    type: str = "basic"


@dataclass
class Token:
    token: str
    type: str = "token"


@dataclass
class CustomAuth:
    value: str
    type: str = "customAuth"


WebhookAuth = Union[BasicAuth, Token, CustomAuth]


class WebhookFormat(str, AutoNamedEnum):
    Generic = "generic"
    InfluxDb = "influxDb"


class WebhookMethod(str, AutoNamedEnum):
    Post = "post"
    Put = "put"
    Patch = "patch"


class ContentType(str, AutoNamedEnum):
    Text = "text"
    Json = "json"


@dataclass
class BodyTemplate:
    contentType: ContentType
    value: str


@dataclass
class WebhookConnectionConfig:
    uri: str
    auth: Optional[WebhookAuth] = None
    additionalHeaders: Dict[str, str] = field(default_factory=dict)
    bodyTemplate: Optional[BodyTemplate] = None
    format: Optional[WebhookFormat] = None
    method: Optional[WebhookMethod] = WebhookMethod.Post


@dataclass
class KafkaFromPropertiesConnectionConfig:
    topic: str
    headers: Dict[str, str] = field(default_factory=dict)
    bodyTemplate: Optional[BodyTemplate] = None
    type: str = field(default="domainProperty", init=False)


@dataclass
class CustomKafkaConnectionConfig:
    value: str
    topic: str
    headers: Dict[str, str] = field(default_factory=dict)
    bodyTemplate: Optional[BodyTemplate] = None
    type: str = field(default="custom", init=False)


KafkaConnectionConfig = Union[KafkaFromPropertiesConnectionConfig,
                              CustomKafkaConnectionConfig]


@dataclass
class EventHandlerConfiguration:
    type: HandlerType
    name: str
    enabled: bool
    filter: EventHandlerFilter
    connectionConfig: Union[WebhookConnectionConfig, KafkaConnectionConfig]
    domain: Optional[str] = None
    description: Optional[str] = None


@dataclass
class EventHandler(EventHandlerConfiguration):
    id: Optional[str] = None


@dataclass
class HandlerTestResult:
    successful: bool
    message: Optional[str] = None
