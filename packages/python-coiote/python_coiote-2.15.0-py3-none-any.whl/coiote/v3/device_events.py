from dataclasses import asdict
from typing import List, Optional

from coiote.utils import ApiEndpoint, api_call, api_call_raw
from coiote.v3.model.device_events import EventHandler, EventHandlerConfiguration, EventHandlerFilter, EventHandlerUpdateData, HandlerTestResult, HandlerType, WebhookConnectionConfig, WebhookFormat, CustomAuth


class DeviceEvents(ApiEndpoint):
    def __init__(
            self, *args, **kwargs
    ):
        super().__init__(*args, **kwargs, api_url="deviceEvents/handler")

    @api_call(List[EventHandler])
    def get_handlers_in_domain(self, domain: str):
        return self.session.get(self.get_url(), params={"domain": domain})

    @api_call(EventHandler)
    def get_handler_by_id(self, id: str):
        if len(id) == 0:
            return None
        return self.session.get(self.get_url(f"/{id}"))

    @api_call_raw
    def delete_handler_by_id(self, id: str):
        return self.session.delete(self.get_url(f"/{id}"))

    @api_call(EventHandler)
    def update_handler(self, id: str, handler_type: HandlerType, update_data: EventHandlerUpdateData):
        if handler_type == HandlerType.Kafka:
            return self.session.put(self.get_url(f"/kafka/{id}"), json=asdict(update_data))
        else:
            return self.session.put(self.get_url(f"/webhook/{id}"), json=asdict(update_data))

    @api_call(HandlerTestResult)
    def test_handler(self, id: str):
        return self.session.post(self.get_url(f"/test/existing/{id}"))

    @api_call(HandlerTestResult)
    def test_handler(self, id: Optional[str] = None, handler_data: Optional[EventHandlerConfiguration] = None):
        if id is None and handler_data is None:
            raise ValueError(
                "To test a handler, you must provide either an ID for a handler that already exists, or entire configuration for a fresh one")
        if id is not None:
            return self.session.post(self.get_url(f"/test/existing/{id}"))
        elif handler_data is not None:
            return self.__test_new_handler(handler_data)

    def __test_new_handler(self, handler_data: EventHandlerConfiguration):
        domain = handler_data.domain
        if domain:
            domain_params = {"domain": domain}
        else:
            domain_params = {}
        if handler_data.type == HandlerType.Kafka:
            return self.session.post(self.get_url(f"/test/kafka"), json=asdict(handler_data), params=domain_params)
        else:
            return self.session.post(self.get_url(f"/test/webhook"), json=asdict(handler_data), params=domain_params)

    @api_call(str)
    def create_handler(self, create_data: EventHandlerConfiguration):
        domain = create_data.domain
        if domain:
            domain_params = {"domain": domain}
        else:
            domain_params = {}
        if create_data.type == HandlerType.Kafka:
            return self.session.post(self.get_url(f"/kafka"), json=asdict(create_data), params=domain_params)
        else:
            return self.session.post(self.get_url(f"/webhook"), json=asdict(create_data), params=domain_params)

    def create_influx_handler(self,
                              name: str,
                              host: str,
                              bucket_id: str,
                              token: str,
                              filter: EventHandlerFilter,
                              enabled: bool = True,
                              domain: Optional[str] = None,
                              description: Optional[str] = None):
        configuration = EventHandlerConfiguration(
            type=HandlerType.Webhook,
            name=name,
            enabled=enabled,
            filter=filter,
            domain=domain,
            description=description,
            connectionConfig=WebhookConnectionConfig(
                uri=f"https://{host}/api/v2/write?precision=ms&bucket={bucket_id}",
                auth=CustomAuth(value=f"Token {token}"),
                additionalHeaders={},
                format=WebhookFormat.InfluxDb
            )
        )
        return self.create_handler(configuration)
